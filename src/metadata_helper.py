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
