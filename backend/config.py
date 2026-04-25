import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Config:
    SECRET_KEY = os.getenv("JWT_SECRET", "change-this-to-a-random-secret-key")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "nepal_law_ai")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'vector_db')
