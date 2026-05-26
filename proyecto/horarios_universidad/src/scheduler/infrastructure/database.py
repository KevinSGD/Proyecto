# src/scheduler/infrastructure/database.py
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from .models import Base

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")


def build_database_url() -> str:
    host = (os.getenv("DB_HOST") or "").strip()
    sslmode = (os.getenv("DB_SSLMODE") or "require").strip()

    # Allow DB_HOST to carry a full connection URL.
    if "://" in host:
        if sslmode and "sslmode=" not in host:
            sep = "&" if "?" in host else "?"
            return f"{host}{sep}sslmode={sslmode}"
        return host

    port = (os.getenv("DB_PORT") or "5432").strip()
    name = (os.getenv("DB_NAME") or "").strip()
    user = (os.getenv("DB_USER") or "").strip()
    password = os.getenv("DB_PASSWORD") or ""

    if not all([host, name, user, password]):
        return None  # Return None instead of raising

    safe_user = quote_plus(user)
    safe_password = quote_plus(password)
    return f"postgresql+psycopg2://{safe_user}:{safe_password}@{host}:{port}/{name}?sslmode={sslmode}"


DATABASE_URL = os.getenv("DATABASE_URL") or build_database_url()

# Create engine only if DATABASE_URL is available
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        poolclass=NullPool,  # Disable connection pooling
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None


def get_db() -> Session:
    """Dependency to get database session"""
    if not SessionLocal:
        raise RuntimeError("Database not configured. Check your .env file.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    if not engine:
        print("Warning: Database not configured. Skipping table creation.")
        return
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not initialize database tables: {e}")


