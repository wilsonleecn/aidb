#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from openai_sql import generate_statements_from_question, execute_multiple_queries
from result_summarizer import summarize_sql_result

def process_question(user_question, language: str = "en"):
    """
    Process a question and return the summary
    """

    # Call OpenAI to generate SQL
    sqls = generate_statements_from_question(user_question)
    all_results = execute_multiple_queries(sqls)

    # Generate summary
    summary = summarize_sql_result(user_question, sqls, all_results, language)
    return summary

def main():
    """
    Main entry point: prompt user for a question, generate SQL, execute it, and print results.
    """
    user_question = input("Please enter your question: ").strip()
    summary = process_question(user_question)
    print("\nSummary:\n", summary)

if __name__ == "__main__":
    main()
