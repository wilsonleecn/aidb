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
    print("Debug: Starting parse_server_hosts")
    server_hosts = {}
    current_group = None
    parent_group = None
    is_children_section = False

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('['):
                group_name = line[1:-1]  # Remove brackets
                print(f"Debug: Found group: {group_name}")
                if ':children' in group_name:
                    parent_group = group_name.replace(':children', '')
                    is_children_section = True
                    print(f"Debug: Set parent_group to: {parent_group}")
                else:
                    current_group = group_name
                    if not is_children_section:
                        parent_group = None
                    print(f"Debug: Set current_group to: {current_group}")
                continue

            group = parent_group if parent_group else current_group
            if group and line:
                server_info = line.split()
                hostname = server_info[0]
                ip = server_info[1] if len(server_info) > 1 else hostname
                server_hosts[hostname] = {
                    'group': group,
                    'ip': ip
                }
                print(f"Debug: Added host {hostname} with group {group} and ip {ip}")

    print("Debug: Final server_hosts structure:")
    for host, info in server_hosts.items():
        print(f"  {host}: {info}")
    return server_hosts

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

def generate_sql(domain_name, domain_name_alias_list, server_hosts, service_info, server_mapping):
    print("Debug: Starting generate_sql")
    print("Debug: server_hosts content:")
    for host, info in server_hosts.items():
        print(f"  {host}: {info}")
    
    sql_commands = []
    sql_commands.append(f"INSERT INTO Domain (id, name) VALUES (NULL, '{escape_sql(domain_name)}');")
    sql_commands.append(f"SET @domain_id = LAST_INSERT_ID();")
    sql_commands.append(f"SET @id_prefix = @domain_id * 1000;")
    
    # Insert aliases for this domain into ResourceAlias
    #    resource_type = 'domain', resource_id = @domain_id, alias = each item in domain_name_alias_list
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
    
    for idx, (group, hosts) in enumerate(server_hosts.items(), start=1):
        host_group_ids[group] = f"(@id_prefix + {idx})"
        sql_commands.append(f"INSERT INTO ServerHostGroup (id, domain_id, name) VALUES ({host_group_ids[group]}, @domain_id, '{group}');")
        for hostname, host_info in hosts.items():
            print(f"Debug: Processing host {hostname}, info: {host_info}, type: {type(host_info)}")
            
            if not isinstance(host_info, dict):
                print(f"Warning: host_info is not a dictionary for {hostname}")
                continue
            
            try:
                group = host_info['group']
                ip = host_info['ip']
            except (KeyError, TypeError) as e:
                print(f"Error processing host {hostname}: {e}")
                print(f"host_info content: {host_info}")
                continue

            vars_json = '{}'
            
            sql_commands.append(f"INSERT INTO ServerHost (id, domain_id, hostname, ip_address, server_host_group_id, vars) "
                              f"VALUES (@id_prefix + {server_host_id_counter}, @domain_id, '{hostname}', '{ip}', "
                              f"{host_group_ids[group]}, '{vars_json}');")
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
    server_hosts = parse_server_hosts(os.path.join(folder_path, 'serverHosts'))
    service_info = parse_service_info(os.path.join(folder_path, 'serviceInfo.conf'))
    server_mapping = parse_server_mapping(os.path.join(folder_path, 'serverMapping.conf'))
    sql_statements = generate_sql(domain_name, domain_name_alias_list, server_hosts, service_info, server_mapping)
    
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
