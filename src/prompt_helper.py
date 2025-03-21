#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from db_runner import run_sql_from_config

def get_metadata(config_path: str) -> str:
    """
    Retrieves domain names, server group names, and service names from the database,
    and returns them as a helper info string.

    Args:
        config_path (str): Path to the DB config file (e.g., 'db_config.ini').

    Returns:
        str: A text listing available domains, server groups, and services.
    """
    # Fetch domain names
    domain_rows = run_sql_from_config("SELECT name FROM Domain;", config_path)
    domain_names = [row["name"] for row in domain_rows]

    # Fetch server group names
    sg_rows = run_sql_from_config("SELECT name FROM ServerGroup;", config_path)
    server_group_names = [row["name"] for row in sg_rows]

    # Fetch service names
    service_rows = run_sql_from_config("SELECT name FROM Service;", config_path)
    service_names = [row["name"] for row in service_rows]

    # Build the helper info string
    helper_info = (
        "Available domain names: " + ", ".join(domain_names) + "\n"
        "Available server group names: " + ", ".join(server_group_names) + "\n"
        "Available service names: " + ", ".join(service_names)
    )

    return helper_info

def build_domain_alias_prompt(config_path: str) -> str:
    """
    Queries ResourceAlias for resource_type='domain', joins Domain to get domain names,
    and constructs a text block listing all domains and their aliases in a human-readable format.

    Example output:
      "The following domains and their aliases exist:
       - Domain 'dev1' can also be called: DE, Dev QA Europe
       - Domain 'prod1' can also be called: production, PRD1"

    Args:
        config_path (str): Path to your DB config file for run_sql_from_config.

    Returns:
        str: A multi-line string that enumerates each domain's aliases.
    """
    # 1) Query ResourceAlias + Domain
    sql = """
    SELECT d.name AS domain_name,
           ra.alias AS alias_name
      FROM ResourceAlias ra
      JOIN Domain d ON ra.resource_id = d.id
     WHERE ra.resource_type = 'domain';
    """
    rows = run_sql_from_config(sql, config_path)
    # rows is typically a list of dicts, e.g.:
    # [ {"domain_name": "dev1", "alias_name": "DE"},
    #   {"domain_name": "dev1", "alias_name": "Dev QA Europe"},
    #   {"domain_name": "prod1", "alias_name": "production"} ]

    # 2) Group aliases by domain_name
    domain_alias_map = {}
    for row in rows:
        domain = row["domain_name"]
        alias = row["alias_name"]
        if domain not in domain_alias_map:
            domain_alias_map[domain] = []
        domain_alias_map[domain].append(alias)

    # 3) Build a prompt string enumerating them
    if not domain_alias_map:
        return "No domain aliases found in the database."

    lines = ["Additionally, here are known domain aliases:","The following domains and their aliases exist:"]
    for domain_name, aliases in domain_alias_map.items():
        alias_str = ", ".join(aliases)
        lines.append(f"- Domain '{domain_name}' can also be called: {alias_str}")

    return "\n".join(lines)