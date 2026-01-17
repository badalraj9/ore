import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "ORE - Open Research Engine"
    API_V1_STR: str = "/api/v1"

    # Storage - Robust Path Resolution
    # Base dir is the repo root (parent of ore-backend)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    RAW_DIR: str = os.path.join(DATA_DIR, "raw")
    PROCESSED_DIR: str = os.path.join(DATA_DIR, "processed")

    # Use absolute path for SQLite to avoid CWD issues
    DB_URL: str = f"sqlite:///{os.path.join(DATA_DIR, 'ore.db')}"

    # NLP
    SPACY_MODEL: str = "en_core_web_sm"

    class Config:
        case_sensitive = True

settings = Settings()

# Ensure directories exist
os.makedirs(settings.RAW_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
