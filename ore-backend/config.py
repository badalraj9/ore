import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "ORE - Open Research Engine"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.1.0"

    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    API_KEY: str = ""
    SECRET_KEY: str = "ore-secret-change-in-production"

    # Storage - Robust Path Resolution
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    RAW_DIR: str = os.path.join(DATA_DIR, "raw")
    PROCESSED_DIR: str = os.path.join(DATA_DIR, "processed")
    DB_URL: str = f"sqlite:///{os.path.join(DATA_DIR, 'ore.db')}"

    # NLP
    SPACY_MODEL: str = "en_core_web_sm"

    # Retrieval Constants
    DEFAULT_TOP_K: int = 10
    RRF_K: int = 60
    SPARSE_WEIGHT: float = 0.5
    DENSE_WEIGHT: float = 0.5

    # Chunking Constants
    CHUNK_SIZES: dict = {
        "abstract": 400,
        "introduction": 350,
        "methods": 400,
        "results": 500,
        "discussion": 400,
        "conclusion": 350,
        "default": 300
    }
    CHUNK_OVERLAPS: dict = {
        "abstract": 0,
        "introduction": 40,
        "methods": 40,
        "results": 50,
        "discussion": 40,
        "conclusion": 40,
        "default": 30
    }

    # Clustering
    DEFAULT_CLUSTERS: int = 5
    MAX_CLUSTER_KEYWORDS: int = 5

    # Ingestion
    MAX_INGEST_RETRIES: int = 3
    INGEST_BACKOFF_BASE: float = 0.5
    MAX_CONCURRENT_DOWNLOADS: int = 5

    # Gap Analysis
    MAX_GAPS_RETURNED: int = 20

    # Webhook
    WEBHOOK_TIMEOUT: int = 30

    class Config:
        case_sensitive = True

settings = Settings()

os.makedirs(settings.RAW_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
