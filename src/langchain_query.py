from langchain_openai import OpenAI
from langchain_community.utilities import SQLDatabase
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain.prompts.prompt import PromptTemplate
import os
from config_reader import Config

def setup_database_chain():
    """Setup database connection and LangChain"""
    # Initialize OpenAI LLM
    llm = OpenAI(
        temperature=0,
        api_key=Config.OPENAI_API_KEY
    )
    
    # Connect to database
    db = SQLDatabase.from_uri(Config.get_db_url())
    
    # Custom prompt template with all required variables
    custom_prompt = """Given a question, first create a syntactically correct SQL query to answer the question.
    Then look at the query results and answer the question in natural language.

    Only use the following table information to answer the question:
    {table_info}

    Top {top_k} most relevant tables:

    Question: {input}"""

    PROMPT = PromptTemplate(
        input_variables=["input", "table_info", "top_k"],
        template=custom_prompt
    )

    # Create database chain
    db_chain = create_sql_query_chain(
        llm=llm,
        db=db,
        prompt=PROMPT
    )
    
    return db_chain

def query_database(question: str) -> str:
    """Process natural language query and return answer"""
    try:
        # Get database chain
        db_chain = setup_database_chain()
        
        # Execute query
        result = db_chain.invoke({"question": question})
        
        return result
    except Exception as e:
        return f"Error occurred during query: {str(e)}"

if __name__ == "__main__":
    # Test example
    question = "How many domains are in the database?"
    answer = query_database(question)
    print(f"Question: {question}")
    print(f"Answer: {answer}") 