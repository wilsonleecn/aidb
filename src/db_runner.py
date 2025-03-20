#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
from config_reader import read_db_config

def run_sql_from_config(sql_str: str, config_path: str):
    """
    Reads the configuration file, connects to the MariaDB database, executes the SQL statement, and returns the result.
    
    Args:
        sql_str (str): The SQL statement to be executed.
        config_path (str): The path to the configuration file (e.g., 'db_config.ini').

    Returns:
        list: The query result, where each row is a dictionary.
    """
    # Read config using the config_reader module
    db_conf = read_db_config(config_path)

    # Establish the database connection
    connection = pymysql.connect(
        host=db_conf["host"],
        port=db_conf["port"],
        user=db_conf["user"],
        password=db_conf["password"],
        database=db_conf["db"],
        cursorclass=pymysql.cursors.DictCursor  # Return results as dict
    )

    result = []
    try:
        with connection.cursor() as cursor:
            # Execute the SQL statement
            cursor.execute(sql_str)
            # Fetch the result (assuming a SELECT query here)
            result = cursor.fetchall()
        # Commit if it's an update/insert/delete operation
        connection.commit()
    except Exception as e:
        print("An exception occurred while executing SQL:", e)
    finally:
        # Close the connection
        connection.close()

    return result
