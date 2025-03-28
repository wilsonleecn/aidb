import os
import json
import yaml
import re
import sys

def get_domain_name_aliases(domain_name: str) -> list:
    """
    Reads 'resource_alias.yml' from the current working directory (os.getcwd()),
    finds any entry where resource_type == 'domain' and name == domain_name.
    Returns all aliases (list of strings) for that domain, or an empty list if none found.
    """
    # Build a path to 'resource_alias.yml' in the current working directory
    yaml_file = os.path.join(os.getcwd(), "resource_alias.yml")
    if not os.path.isfile(yaml_file):
        print(f"[WARNING] {yaml_file} not found in current working directory.")
        return []
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # Expected YAML format, e.g.:
    # resourcealias:
    #   - resource_type: "domain"
    #     name: "dev1"
    #     alias:
    #       - "DE"
    #       - "Dev QA Europe"
    resource_list = data.get("resourcealias", [])
    if not isinstance(resource_list, list):
        return []
    aliases = []
    for item in resource_list:
        if item.get("resource_type") == "domain" and item.get("name") == domain_name:
            alias_list = item.get("alias", [])
            aliases.extend(alias_list)
    return aliases

def escape_sql(value):
    """Escape single quotes and other special characters for SQL."""
    return value.replace("'", "''") if value else value

def is_ip_address(hostname):
    """Check if a string is a valid IP address."""
    return re.match(r'^\d+\.\d+\.\d+\.\d+$', hostname) is not None

def parse_server_hosts(file_path):
    server_hosts = {}
    parent_groups = {}  # Maps child groups to their parent group
    children_groups = {}  # Maps parent groups to their child groups
    current_group = None
    current_parent = None

    # First pass: collect all groups and their relationships
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Check for group headers
            if re.match(r'^\[.*\]$', line):
                group_name = line.strip('[]')
                
                # Check if this is a parent group definition
                if ':children' in group_name:
                    parent_name = group_name.replace(':children', '')
                    current_parent = parent_name
                    current_group = None
                    if current_parent not in children_groups:
                        children_groups[current_parent] = []
                    if current_parent not in server_hosts:
                        server_hosts[current_parent] = []
                else:
                    current_group = group_name
                    current_parent = None
                    if current_group not in server_hosts:
                        server_hosts[current_group] = []
            
            # If we're in a parent group definition, record child groups
            elif current_parent and line:
                child_group = line.strip()
                children_groups[current_parent].append(child_group)
                parent_groups[child_group] = current_parent
            
            # Process host entries
            elif current_group:
                parts = line.split()
                hostname = parts[0]
                ip_address = hostname if is_ip_address(hostname) else ''
                variables = ' '.join(parts[1:]) if len(parts) > 1 else ''
                
                host_entry = {
                    "hostname": escape_sql(hostname),
                    "ip_address": escape_sql(ip_address),
                    "vars": escape_sql(variables)
                }
                server_hosts[current_group].append(host_entry)

    # Second pass: propagate hosts from child groups to parent groups
    for parent, children in children_groups.items():
        all_hosts = []
        # Collect hosts from all child groups
        for child in children:
            if child in server_hosts:
                all_hosts.extend(server_hosts[child])
        
        # Add collected hosts to parent group
        if parent not in server_hosts:
            server_hosts[parent] = []
        server_hosts[parent].extend(all_hosts)

        # Remove duplicates while preserving order
        seen_hosts = set()
        unique_hosts = []
        for host in server_hosts[parent]:
            host_key = (host['hostname'], host['ip_address'], host['vars'])
            if host_key not in seen_hosts:
                seen_hosts.add(host_key)
                unique_hosts.append(host)
        server_hosts[parent] = unique_hosts

    return server_hosts, parent_groups

def parse_service_info(file_path):
    services = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            service_name = parts[0]
            service_type = parts[1]
            docker = parts[2].lower() == 'true'
            service_package = parts[3]
            config_files = parts[4]
            deploy_dir = parts[5]
            status_port = parts[6]
            management_endpoint = parts[7]
            services[service_name] = {
                "type": escape_sql(service_type),
                "docker": docker,
                "package": escape_sql(service_package),
                "config": escape_sql(config_files),
                "deploy_dir": escape_sql(deploy_dir),
                "status_port": escape_sql(status_port),
                "management_endpoint": escape_sql(management_endpoint)
            }
    return services

def parse_server_mapping(file_path):
    server_groups = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            server_group = parts[0]
            server_host_group = parts[1]
            services = parts[2:]
            if server_group not in server_groups:
                server_groups[server_group] = []
            server_groups[server_group].append({
                "server_host_group": escape_sql(server_host_group),
                "services": [escape_sql(service) for service in services]
            })
    return server_groups

def generate_sql(domain_name, domain_name_alias_list, server_hosts_data, service_info, server_mapping):
    server_hosts, parent_groups = server_hosts_data  # Unpack the tuple
    sql_commands = []
    sql_commands.append(f"INSERT INTO Domain (id, name) VALUES (NULL, '{escape_sql(domain_name)}');")
    sql_commands.append(f"SET @domain_id = LAST_INSERT_ID();")
    sql_commands.append(f"SET @id_prefix = @domain_id * 1000;")
    
    # Insert aliases for this domain into ResourceAlias
    for alias in domain_name_alias_list:
        sql_commands.append(
            f"INSERT INTO ResourceAlias (resource_type, resource_id, alias) "
            f"VALUES ('domain', @domain_id, '{escape_sql(alias)}');"
        )

    host_group_ids = {}
    service_ids = {}
    server_group_ids = {}
    server_host_id_counter = 1
    server_group_mapping_id_counter = 1
    
    # Filter out child groups before generating SQL
    parent_groups_set = set(parent_groups.values())
    filtered_server_hosts = {
        group: hosts for group, hosts in server_hosts.items()
        if group not in parent_groups or group in parent_groups_set
    }
    
    for idx, (group, hosts) in enumerate(filtered_server_hosts.items(), start=1):
        host_group_ids[group] = f"(@id_prefix + {idx})"
        sql_commands.append(f"INSERT INTO ServerHostGroup (id, domain_id, name) VALUES ({host_group_ids[group]}, @domain_id, '{group}');")
        for host in hosts:
            sql_commands.append(f"INSERT INTO ServerHost (id, domain_id, hostname, ip_address, server_host_group_id, vars) VALUES (@id_prefix + {server_host_id_counter}, @domain_id, '{host['hostname']}', '{host['ip_address']}', {host_group_ids[group]}, '{host['vars']}');")
            server_host_id_counter += 1
    
    for idx, (service, info) in enumerate(service_info.items(), start=1):
        service_ids[service] = f"(@id_prefix + {idx})"
        sql_commands.append(f"INSERT INTO Service (id, domain_id, name, service_type, docker, service_package_name, service_config_file, service_deploy_dir, status_port, management_endpoint) VALUES ({service_ids[service]}, @domain_id, '{service}', '{info['type']}', {int(info['docker'])}, '{info['package']}', '{info['config']}', '{info['deploy_dir']}', {info['status_port'] if info['status_port'].isdigit() else 'NULL'}, '{info['management_endpoint']}');")
    
    for idx, (server_group, mappings) in enumerate(server_mapping.items(), start=1):
        server_group_ids[server_group] = f"(@id_prefix + {idx})"
        sql_commands.append(f"INSERT INTO ServerGroup (id, domain_id, name) VALUES ({server_group_ids[server_group]}, @domain_id, '{server_group}');")
        for mapping in mappings:
            host_group_id = host_group_ids.get(mapping['server_host_group'], 'NULL')
            if server_group_ids[server_group] == 'NULL' or host_group_id == 'NULL':
                continue
            for service in mapping['services']:
                service_id = service_ids.get(service, 'NULL')
                sql_commands.append(f"INSERT INTO ServerGroupMapping (id, domain_id, server_group_id, server_host_group_id, service_id) VALUES (@id_prefix + {server_group_mapping_id_counter}, @domain_id, {server_group_ids[server_group]}, {host_group_id}, {service_id});")
                server_group_mapping_id_counter += 1
    
    return sql_commands

def main(folder_path):
    domain_name = os.path.basename(folder_path)
    domain_name_alias_list = get_domain_name_aliases(domain_name)
    server_hosts_data = parse_server_hosts(os.path.join(folder_path, 'serverHosts'))
    service_info = parse_service_info(os.path.join(folder_path, 'serviceInfo.conf'))
    server_mapping = parse_server_mapping(os.path.join(folder_path, 'serverMapping.conf'))
    sql_statements = generate_sql(domain_name, domain_name_alias_list, server_hosts_data, service_info, server_mapping)
    
    crrentPath = os.getcwd()
    fileName =  domain_name+'_aid.sql'
    with open(os.path.join(crrentPath, fileName), 'w') as f:
        f.write('\n'.join(sql_statements))
    print(f"SQL script saved to {crrentPath}/{fileName}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)
    folder_path = sys.argv[1]
    main(folder_path)
