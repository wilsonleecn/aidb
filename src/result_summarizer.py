#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import openai

# Set your OpenAI API key:
openai.api_key = os.getenv("OPENAI_API_KEY")  # or hardcode, but not recommended

def summarize_sql_result(user_question: str, sql_query: str, query_result) -> str:
    """
    Calls OpenAI to create a human-readable summary of the query result.

    Args:
        user_question (str): The original user question (natural language).
        sql_query (str): The SQL query that was used to get the result.
        query_result (list): The result fetched from the database (list of dicts, typically).

    Returns:
        str: A user-friendly description or summary of the query result.
    """
    # Convert query_result (a list of dicts) to a more readable string
    # You can adjust how much detail you include:
    result_str = f"SQL Query: {sql_query}\n\nQuery Result:\n{repr(query_result)}"

    # We'll feed the above to the model in the user message
    # So the system prompt sets the role, the user prompt includes the question, the query, the results
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant that produces a concise, human-readable summary. "
                "The user asked a question, we have a SQL query and the raw query result. "
                "Please summarize the result clearly in plain language. "
                "Feel free to include minimal details like row counts or key fields, but make it understandable."
            )
        },
        {
            "role": "user",
            "content": (
                f"User question: {user_question}\n\n"
                f"{result_str}\n\n"
                "Now please summarize these results in a simple, direct way."
            )
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or gpt-4, depending on availability
        messages=messages,
        temperature=0.7,
        max_tokens=400
    )

    summary_text = response["choices"][0]["message"]["content"].strip()
    return summary_text

def main():
    """
    A small demo showing how to use the summarize_sql_result function.
    """
    # Example data
    user_question = "Which domains are available in the system?"
    sql_query = "SELECT name FROM Domain;"
    # Suppose our DB returned two rows:
    query_result = [{"name": "dev1"}, {"name": "prod1"}]

    # Generate the summary
    summary = summarize_sql_result(user_question, sql_query, query_result)
    print("=== Human-readable Summary ===")
    print(summary)

if __name__ == "__main__":
    main()
