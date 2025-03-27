#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from openai_sql import generate_statements_from_question, execute_multiple_queries
from result_summarizer import summarize_sql_result
from datetime import datetime

def process_question(user_question, language: str = "en"):
    """
    Process a question and return the summary and metadata
    """
    # metadata in process
    metadata = {
        "start_time": datetime.now().isoformat(),
        "language": language
    }
    
    try:
        # generate SQL
        sqls = generate_statements_from_question(user_question)
        metadata["generated_sql"] = sqls
        
        # execute sql
        all_results = execute_multiple_queries(sqls)
        metadata["query_results"] = all_results
        
        # generate summary
        summary = summarize_sql_result(user_question, sqls, all_results, language)
        
        # append query results to summary
        show_raw_results = False
        result_limit = 10  # Configure the threshold here
        
        raw_results_section = "\n\n----Raw Results----"
        for i, result in enumerate(all_results):
            raw_results_section += f"\n[Query {i+1}]:\n"
            if isinstance(result, list):
                if len(result) > result_limit:
                    show_raw_results = True
                for row in result:
                    raw_results_section += f"{row}\n"
            else:
                if isinstance(result['result'], list):
                    if len(result['result']) > result_limit:
                        show_raw_results = True
                    for item in result['result']:
                        raw_results_section += f"{item}\n"
                else:
                    raw_results_section += f"{result['result']}\n"
        
        # Only append raw results if there are more items than the limit in any result
        if show_raw_results:
            summary = summary + raw_results_section
        
        # update metadata 
        metadata.update({
            "end_time": datetime.now().isoformat(),
            "status": "success"
        })
        metadata["summary_process"] = getattr(summary, 'metadata', {})
        
        # add more object into response which will be returned
        class Response(str):
            pass
            
        response = Response(summary)
        response.metadata = metadata
        response.generated_sql = sqls
        response.query_results = all_results
        
        return response
        
    except Exception as e:
        metadata["end_time"] = datetime.now().isoformat()
        metadata["status"] = "error"
        metadata["error"] = {
            "type": type(e).__name__,
            "message": str(e)
        }
        raise

def main():
    """
    Main entry point: prompt user for a question, generate SQL, execute it, and print results.
    """
    user_question = input("Please enter your question: ").strip()
    summary = process_question(user_question)
    print("\nSummary:\n", summary)

if __name__ == "__main__":
    main()
