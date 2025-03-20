#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from openai_sql import generate_sql_from_question
from db_runner import run_sql_from_config
from result_summarizer import summarize_sql_result

def main():
    """
    Main entry point: prompt user for a question, generate SQL, execute it, and print results.
    """
    user_question = input("Please enter your question: ").strip()
    config_path = "db_config.ini"  # Adjust path if needed

    # 1. Call OpenAI to generate SQL
    sql_query = generate_sql_from_question(user_question, config_path)

    # 2. Print the generated SQL
    print("\nGenerated SQL Query:\n")
    print(sql_query)

    # 3. Execute the SQL using our db_runner function
    results = run_sql_from_config(sql_query, config_path)

    # 4. Print the query results
    print("\nQuery Results:\n", results)
    
    # 3. Summarize in a human-readable way
    summary = summarize_sql_result(user_question, sql_query, results)
    print("\nSummary:\n", summary)

if __name__ == "__main__":
    main()
