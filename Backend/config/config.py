from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(str(BASE_DIR / ".env"))


class Settings:

    APP_NAME = os.getenv("APP_NAME", "Wind Data Insight Pro")

    ENVIRONMENT = os.getenv("ENVIRONMENT")

    DEBUG = (os.getenv("DEBUG","False").lower()== "true")

    API_V1_PREFIX = os.getenv("API_V1_PREFIX","/api/v1")

    FRONTEND_URL = os.getenv("FRONTEND_URL")

    DATABASE_URL = os.getenv("DATABASE_URL")

    UPLOAD_DIRECTORY = os.getenv("UPLOAD_DIRECTORY")

    OLLAMA_URL = os.getenv("OLLAMA_URL",)

    PORT = int(os.getenv("PORT"))


settings = Settings()