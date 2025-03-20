#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import pymysql
import configparser

def run_sql_from_config(sql_str: str, config_path: str):
    """
    Read the configuration file, connect to the MariaDB database, execute the given SQL statement, and return the result.
    
    Args:
        sql_str (str): The SQL statement to be executed.
        config_path (str): The path to the configuration file.
    
    Returns:
        list: The query result, where each row is represented as a dictionary.
    """
    # 1. Parse the configuration file
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')

    # Retrieve database connection information from the configuration file
    host = config['database']['host']
    port = int(config['database']['port'])
    db_name = config['database']['db']
    user = config['database']['user']
    password = config['database']['password']

    # 2. Establish the database connection
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor  # Return results as dictionaries
    )

    try:
        with connection.cursor() as cursor:
            # 3. Execute the SQL statement
            cursor.execute(sql_str)
            # 4. Fetch the result (assuming a SELECT query here; other queries can also be executed)
            result = cursor.fetchall()
        # Commit if it's an update/insert/delete operation
        connection.commit()
    except Exception as e:
        print("An exception occurred while executing SQL:", e)
        result = []
    finally:
        # 5. Close the connection
        connection.close()

    # 6. Return the query result
    return result


def main():
    """
    Program entry point: demonstrates calling run_sql_from_config and printing the result to the console.
    """
    # Example: read the first command line argument as the SQL statement and the second as the config path
    # If command line arguments are missing, a default SQL statement is used.
    if len(sys.argv) > 2:
        sql_str = sys.argv[1]
        config_path = sys.argv[2]
    else:
        # Provide a default SQL statement for demonstration if no arguments are passed
        sql_str = "SELECT 'Hello, world!' AS greeting;"
        config_path = "db_config.ini"

    # Call the method above to execute the SQL
    results = run_sql_from_config(sql_str, config_path)

    # Print the result to the console
    print("SQL statement:", sql_str)
    print("Query result:", results)


if __name__ == "__main__":
    main()
