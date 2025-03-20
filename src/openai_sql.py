#!/usr/bin/env python3
#docker build . -t ai:latest
#docker run -v /home/work/operationtool/resource_searcher/openai_request.py:/tmp/openai_request.py -v /home/work/operationtool/resource_searcher/db:/tmp/db --rm -ti ai:latest bash
#python db_runner.py "SELECT * FROM Domain LIMIT 5;" "db_config.ini"

import os
import re
from metadata_helper import get_metadata
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def generate_sql_from_question(user_question: str, config_path: str) -> str:
    """
    1) Calls get_metadata to fetch domain/server group/service names from DB.
    2) Builds a system prompt that includes both the DB schema and the actual metadata.
    3) Calls OpenAI to generate SQL from the user question.

    Args:
        user_question (str): Natural language question from the user.
        config_path (str): Path to the DB config file for fetching metadata (e.g., 'db_config.ini').

    Returns:
        str: The SQL query (as a string).
    """
    # Get actual domain/servergroup/service names from the DB:
    helper_info = get_metadata(config_path)
    # Combine the schema and the dynamic helper info in the system prompt
    system_prompt = SYSTEM_PROMPT_BASE + "\n\n" + DB_SCHEMA_PROMPT + "\n\n" + helper_info

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]

    # Make the request to OpenAI
    response = client.chat.completions.create(model="gpt-4o",
    messages=messages,
    temperature=0.2,
    max_tokens=300)

    # Extract and print the assistant's answer (SQL statement)
    sql_answer = response.choices[0].message.content
    sql_answer = parse_sql_code_block(sql_answer)
    return sql_answer

def parse_sql_code_block(text: str) -> str:
    """
    Parses out the first ```sql ... ``` code block from the text and returns the SQL code without the backticks.
    If no code block is found, returns the original text stripped.
    """
    # Regex to capture text within ```sql ... ```
    pattern = r"```sql\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        # Return only the code inside the code fence
        return match.group(1).strip()
    else:
        # If no match, just return the text stripped
        return text.strip()