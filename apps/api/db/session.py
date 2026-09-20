"""SQLAlchemy engine + session from DATABASE_URL (Supabase Postgres or local).

Use the direct connection (port 5432) for FastAPI. Falls back to the local
docker-compose Postgres when DATABASE_URL is unset.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://atlas:atlas@localhost:5432/atlas",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def get_db():
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
