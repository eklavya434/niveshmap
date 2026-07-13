import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Fetch database configurations with fallback to SQLite for testing/reproducibility
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

if DB_HOST and DB_NAME and DB_USER:
    # PostgreSQL connection string
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    # Fallback to local SQLite file for testing and demo execution
    os.makedirs("data", exist_ok=True)
    DATABASE_URL = "sqlite:///data/ncr_real_estate.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_session():
    """Context manager or dependency for retrieving database sessions."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
