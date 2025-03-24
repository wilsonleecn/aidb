from langchain_openai import OpenAI
from langchain_community.utilities import SQLDatabase
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain.prompts.prompt import PromptTemplate
import os
from config_reader import Config

def setup_database_chain():
    """设置数据库链接和 LangChain"""
    # 初始化 OpenAI LLM
    llm = OpenAI(
        temperature=0,
        api_key=Config.OPENAI_API_KEY
    )
    
    # 连接数据库
    db = SQLDatabase.from_uri(Config.get_db_url())
    
    # 自定义提示模板，包含所有必需的变量
    custom_prompt = """给定一个问题，首先创建一个符合语法的 SQL 查询来回答该问题。
    然后查看查询结果，并用自然语言回答问题。

    仅使用以下表信息来回答问题：
    {table_info}

    Top {top_k} 最相关的表：

    问题: {input}"""

    PROMPT = PromptTemplate(
        input_variables=["input", "table_info", "top_k"],
        template=custom_prompt
    )

    # 创建数据库链
    db_chain = create_sql_query_chain(
        llm=llm,
        db=db,
        prompt=PROMPT
    )
    
    return db_chain

def query_database(question: str) -> str:
    """处理自然语言查询并返回答案"""
    try:
        # 获取数据库链
        db_chain = setup_database_chain()
        
        # 执行查询
        result = db_chain.invoke({"question": question})
        
        return result
    except Exception as e:
        return f"查询过程中发生错误: {str(e)}"

if __name__ == "__main__":
    # 测试示例
    question = "数据库中有多少个domain？"
    answer = query_database(question)
    print(f"问题: {question}")
    print(f"回答: {answer}") 