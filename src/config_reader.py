from pathlib import Path
from dotenv import load_dotenv
import os

# Get the src directory path
SRC_DIR = Path(__file__).resolve().parent
ENV_PATH = SRC_DIR / '.env'

# Load environment variables from .env file
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'serverconf')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    @classmethod
    def get_db_url(cls):
        return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"