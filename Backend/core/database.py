from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.config import settings

# Create database directory if using SQLite
database_url = settings.DATABASE_URL
if database_url and database_url.startswith("sqlite:///"):
    # Extract the file path from sqlite:///path/to/db.db
    db_path = database_url.replace("sqlite:///", "")
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(database_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    
    finally:
        db.close()