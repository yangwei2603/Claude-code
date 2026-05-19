from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "requirement_pool.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表"""
    from app.models import Requirement, RequirementReview, StatusLog, ReviewSession
    Base.metadata.create_all(bind=engine)