"""
SQLAlchemy engine, session factory.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATA_DIR

# Ensure database directory exists
os.makedirs(DATA_DIR, exist_ok=True)

db_path = os.path.join(DATA_DIR, "dpos.db")
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def init_db():
    """Create all database tables if they do not exist."""
    # Import models here to register them with Base.metadata before creating tables
    import core.models
    Base.metadata.create_all(bind=engine)
