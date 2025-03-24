#!/usr/bin/env python3
#docker build . -t ai:latest
#docker run -v /home/work/operationtool/resource_searcher/openai_request.py:/tmp/openai_request.py -v /home/work/operationtool/resource_searcher/db:/tmp/db --rm -ti ai:latest bash
#python db_runner.py "SELECT * FROM Domain LIMIT 5;" "db_config.ini"

import os
import re
from openai import OpenAI
from prompt_helper import get_metadata, build_domain_alias_prompt
from db_runner import run_sql_from_config
from config_reader import Config

# Initialize the OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)


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

SYSTEM_PROMPT_BASE = """
You are an AI assistant that generates SQL queries based on the following schema and helper info.
Use only the information in the schema to answer questions.
Provide only the SQL query (or queries) that fulfill the user's request.
Do not provide explanations—only the SQL.
"""

def generate_statements_from_question(user_question: str, config_path: str) -> list:
    """
    1) Calls get_metadata to fetch domain/server group/service names from DB.
    2) Calls build_domain_alias_prompt to fetch domain alias to generate prompt from DB.
    2) Builds a system prompt that includes both the DB schema and the actual metadata.
    3) Calls OpenAI to generate SQL from the user question.

    Args:
        user_question (str): Natural language question from the user.
        config_path (str): Path to the DB config file for fetching metadata (e.g., 'db_config.ini').

    Returns:
        str: The SQL query (as a string).
    """
    # Get actual domain/servergroup/service names from the DB:
    domain_alias_prompt = build_domain_alias_prompt(config_path)
    helper_info = get_metadata(config_path)
    # Combine the schema and the dynamic helper info in the system prompt
    system_prompt = SYSTEM_PROMPT_BASE + "\n\n" + DB_SCHEMA_PROMPT + "\n\n" + helper_info + "\n\n" + domain_alias_prompt

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

def parse_multiple_queries(sql_answer: str) -> list:
    """
    Splits an OpenAI-generated SQL response into separate statements.
    We assume statements are separated by a semicolon or a blank line.
    
    Returns a list of SQL statements (strings).
    """
    # 1) Split on semicolons. This is simplistic—works for basic SQL.
    # 2) Trim whitespace. 
    statements = []
    for part in sql_answer.split(";"):
        stmt = part.strip()
        # If it still contains newlines, we can remove them or keep them, doesn't matter for simple queries
        # but let's keep them just in case.
        if stmt:
            statements.append(stmt)
    return statements

def execute_multiple_queries(sqls: str, config_path: str) -> list:
    """
    Parses the SQL answer into individual statements,
    executes each, and collects results.
    
    Returns a list of dictionaries, each containing the query and the result.
    """
    statements = parse_multiple_queries(sqls)
    results_list = []
    
    #Print the generated SQL
    print("\nGenerated SQL Query:\n")
    for stmt in statements:
        print(stmt)

    #Execute statements and collect the results
    for stmt in statements:
        # run_sql_from_config returns a list of dicts
        query_result = run_sql_from_config(stmt, config_path)
        results_list.append({"query": stmt, "result": query_result})
    
    return results_list