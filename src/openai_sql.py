#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import openai

# Ensure your OPENAI_API_KEY is set in the environment or replace with direct string:
openai.api_key = os.getenv("OPENAI_API_KEY")

# Prepare the database schema prompt you want the AI to know:
DB_SCHEMA_PROMPT = """
Here is the database schema we have:

CREATE TABLE Domain (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE ServerHostGroup (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE
);

CREATE TABLE ServerHost (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    server_host_group_id BIGINT UNSIGNED NOT NULL,
    ip_address VARCHAR(255),
    os VARCHAR(255),
    location VARCHAR(255),
    vars TEXT,
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE,
    FOREIGN KEY (server_host_group_id) REFERENCES ServerHostGroup(id) ON DELETE CASCADE
);

CREATE TABLE Service (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    service_type VARCHAR(255),
    docker BOOLEAN,
    service_package_name VARCHAR(255),
    service_config_file TEXT,
    service_deploy_dir VARCHAR(255),
    status_port INT,
    management_endpoint VARCHAR(255),
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE
);

CREATE TABLE ServerGroup (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE
);

CREATE TABLE ServerGroupMapping (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    server_group_id BIGINT UNSIGNED NOT NULL,
    server_host_group_id BIGINT UNSIGNED NOT NULL,
    service_id BIGINT UNSIGNED NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE,
    FOREIGN KEY (server_group_id) REFERENCES ServerGroup(id) ON DELETE CASCADE,
    FOREIGN KEY (server_host_group_id) REFERENCES ServerHostGroup(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES Service(id) ON DELETE CASCADE
);
"""

SYSTEM_PROMPT = """
You are an AI assistant that generates SQL queries based on the following schema.
Use only the information in the schema to answer questions.
Provide only the SQL query (or queries) that fulfill the user's request.
Do not provide explanations—only the SQL.
"""

def generate_sql_from_question(user_question: str) -> str:
    """
    Calls OpenAI to generate SQL from a user question using the schema in DB_SCHEMA_PROMPT.

    Args:
        user_question (str): Natural language question from the user.

    Returns:
        str: The SQL query (as a string).
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n" + DB_SCHEMA_PROMPT},
        {"role": "user", "content": user_question}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.2,
        max_tokens=300
    )

    # We assume the entire assistant message is the SQL
    sql_answer = response.choices[0].message.content.strip()
    return sql_answer
