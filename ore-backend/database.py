from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import settings
from datetime import datetime
import enum

engine = create_engine(settings.DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskStatusEnum(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    authors = Column(String)
    abstract = Column(Text)
    doi = Column(String, unique=True, index=True)
    source = Column(String)
    url = Column(String)
    published_date = Column(DateTime)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    filepath_raw = Column(String)
    filepath_processed = Column(String)

    chunks = relationship("Chunk", back_populates="paper")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    section = Column(String)
    text = Column(Text)
    token_count = Column(Integer)
    embedding_id = Column(String, nullable=True)

    paper = relationship("Paper", back_populates="chunks")

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    canonical_name = Column(String, unique=True, index=True)
    aliases = Column(Text)
    category = Column(String)

class IngestionTask(Base):
    __tablename__ = "ingestion_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    source = Column(String)
    query = Column(String, nullable=True)
    url = Column(String, nullable=True)
    status = Column(SQLEnum(TaskStatusEnum), default=TaskStatusEnum.PENDING)
    progress = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    webhook_url = Column(String, nullable=True)
    task_metadata = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
