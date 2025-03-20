#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser

def read_db_config(config_path: str):
    """
    Reads the database configuration from an INI file.

    Args:
        config_path (str): Path to the configuration file (e.g., 'db_config.ini').

    Returns:
        dict: A dictionary with host, port, db, user, password.
    """
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')

    db_conf = {
        "host": config["database"]["host"],
        "port": int(config["database"]["port"]),
        "db": config["database"]["db"],
        "user": config["database"]["user"],
        "password": config["database"]["password"],
    }
    return db_conf
