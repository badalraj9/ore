from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import settings
from datetime import datetime

engine = create_engine(settings.DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    authors = Column(String) # JSON string or comma-separated
    abstract = Column(Text)
    doi = Column(String, unique=True, index=True)
    source = Column(String) # arxiv, semantic_scholar
    url = Column(String)
    published_date = Column(DateTime)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    filepath_raw = Column(String)
    filepath_processed = Column(String)

    # Relationships
    chunks = relationship("Chunk", back_populates="paper")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    section = Column(String) # e.g., "introduction", "results"
    text = Column(Text)
    token_count = Column(Integer)
    embedding_id = Column(String, nullable=True) # For Phase 5

    paper = relationship("Paper", back_populates="chunks")

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    canonical_name = Column(String, unique=True, index=True)
    aliases = Column(Text) # JSON list of strings: ["CNN", "ConvNet"]
    category = Column(String) # e.g., "Method", "Metric", "Task"

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
