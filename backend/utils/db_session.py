import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.config import Config
from .logging_config import LogManager

logger = LogManager.get_logger()

# Singleton class to manage the SQLAlchemy database engine and session factory
class DBSession:
    _instance = None
    config = Config().config
    def __new__(cls):
        # Create a new instance only if one doesn't already exist
        if cls._instance is None:
            cls._instance = super(DBSession, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Prevent re-initialization of the singleton instance
        if self._initialized:
            return

        # Retrieve the database URL from configuration or environment variable
        db_url = self.config['database']['url']
        self.DATABASE_URL = os.getenv("DATABASE_URL", db_url)
        logger.debug(f"Connecting to database at: {self.DATABASE_URL.split('@')[-1] if '@' in self.DATABASE_URL else self.DATABASE_URL}")

        # Configure connection arguments specific to the database type
        # For SQLite, we must disable thread checking to allow multiple requests to use the same connection
        connect_args = {}
        if self.DATABASE_URL and self.DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        # Initialize the SQLAlchemy engine
        self.engine = create_engine(
            self.DATABASE_URL,
            connect_args=connect_args,
            pool_pre_ping=True
        )
        # Create a session factory for generating new database sessions
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self._initialized = True

# Dependency to get a local database session
def get_db():
    logger.debug("Creating new DB session")
    db = DBSession().SessionLocal()
    try:
        yield db
    finally:
        logger.debug("Closing DB session")
        db.close()
