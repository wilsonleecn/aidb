#!/usr/bin/env python3
#docker build . -t ai:latest
#docker run -v /home/work/operationtool/resource_searcher/openai_request.py:/tmp/openai_request.py -v /home/work/operationtool/resource_searcher/db:/tmp/db --rm -ti ai:latest bash
#python db_runner.py "SELECT * FROM Domain LIMIT 5;" "db_config.ini"

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def main():
    # Make sure you set your OpenAI API key in an environment variable or directly here:
    # openai.api_key = "YOUR_OPENAI_API_KEY"

    # The database schema you want the AI to know:
    db_schema = """
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

    # Prompt the user for the question
    user_question = input("Please enter your question: ").strip()

    # Construct the messages for ChatGPT
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant that generates SQL queries based on the following schema. "
                "Use only the information in the schema to answer questions. "
                "Provide the most direct SQL query or queries that fulfill the request. "
                "Do not provide additional commentary—only the SQL."
                "\n\n"
                + db_schema
            ),
        },
        {
            "role": "user",
            "content": user_question
        }
    ]

    # Make the request to OpenAI
    response = client.chat.completions.create(model="gpt-4o",
    messages=messages,
    temperature=0.2,
    max_tokens=300)

    # Extract and print the assistant's answer (SQL statement)
    sql_answer = response.choices[0].message.content
    print("\nGenerated SQL Query:\n")
    print(sql_answer)


if __name__ == "__main__":
    main()

