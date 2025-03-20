#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from openai_sql import generate_statements_from_question, execute_multiple_queries
from db_runner import run_sql_from_config
from result_summarizer import summarize_sql_result

def main():
    """
    Main entry point: prompt user for a question, generate SQL, execute it, and print results.
    """
    user_question = input("Please enter your question: ").strip()
    config_path = "db_config.ini"  # Adjust path if needed

    # Call OpenAI to generate SQL
    sqls = generate_statements_from_question(user_question, config_path)
    all_results = execute_multiple_queries(sqls, config_path)

    # Print out each query and its result
    for idx, item in enumerate(all_results, start=1):
        print(f"\n--- Query #{idx} ---")
        print("SQL:\n", item["query"])
        print("Result:\n", item["result"])

    # 3. Summarize in a human-readable way
    summary = summarize_sql_result(user_question, sqls, all_results)
    print("\nSummary:\n", summary)

if __name__ == "__main__":
    main()
