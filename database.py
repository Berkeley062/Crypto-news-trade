"""Database setup and utilities."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from config import config
from models import Base
from utils.logging import get_logger

logger = get_logger(__name__)

# Database engine
engine = create_engine(
    config.database_url,
    poolclass=StaticPool if "sqlite" in config.database_url else None,
    connect_args={"check_same_thread": False} if "sqlite" in config.database_url else {},
    echo=config.debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_db() -> Generator[Session, None, None]:
    """Get database session (for dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session (for context manager usage)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_database():
    """Initialize the database with required tables and default data."""
    logger.info("Initializing database...")
    
    # Create tables
    create_tables()
    
    # Add default configuration if needed
    with get_db_session() as db:
        from models import ConfigItem
        
        # Check if we have any config items
        existing_config = db.query(ConfigItem).first()
        if not existing_config:
            logger.info("Adding default configuration items...")
            
            default_configs = [
                ConfigItem(
                    key="system_initialized",
                    value="true",
                    description="Flag indicating system has been initialized",
                    data_type="bool"
                ),
                ConfigItem(
                    key="last_startup",
                    value=str(datetime.utcnow().isoformat()),
                    description="Last system startup time",
                    data_type="string"
                )
            ]
            
            for config_item in default_configs:
                db.add(config_item)
            
            db.commit()
            logger.info("Default configuration added")
    
    logger.info("Database initialization completed")


if __name__ == "__main__":
    from datetime import datetime
    init_database()