"""Database configuration and session helpers for the SEMS backend."""

import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, declarative_base, sessionmaker


# Load .env from the project root, independent of the command used to start Uvicorn.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def required_setting(name: str) -> str:
    """Return one required database setting without printing any credentials."""

    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing {name} in .env. Add it before starting the backend.")
    return value


# URL.create safely handles special characters in a password without placing it
# in source code or logs. The actual value exists only in the local .env file.
database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=required_setting("DB_USER"),
    password=required_setting("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "SEMS_db"),
)

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide one database session per API request and close it afterwards."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
