#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from openai_sql import generate_statements_from_question, execute_multiple_queries
from result_summarizer import summarize_sql_result
from datetime import datetime

def process_question(user_question, language: str = "en"):
    """
    Process a question and return the summary and metadata
    """
    # 记录中间过程的元数据
    metadata = {
        "start_time": datetime.now().isoformat(),
        "language": language
    }
    
    try:
        # 生成 SQL
        sqls = generate_statements_from_question(user_question)
        metadata["generated_sql"] = sqls
        
        # 执行查询
        all_results = execute_multiple_queries(sqls)
        metadata["query_results"] = all_results
        
        # 生成摘要
        summary = summarize_sql_result(user_question, sqls, all_results, language)
        
        metadata["end_time"] = datetime.now().isoformat()
        metadata["status"] = "success"
        
        # 创建一个带有额外属性的 Response 对象
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
