
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.config import Config
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



class DBSession:
    _instance = None
    config = Config().config
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBSession, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Read from config file
        
        db_url = self.config['database']['url']
        self.DATABASE_URL = os.getenv("DATABASE_URL", db_url)

        # Choose connect_args based on DB type
        connect_args = {}
        if self.DATABASE_URL and self.DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        self.engine = create_engine(
            self.DATABASE_URL,
            connect_args=connect_args
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self._initialized = True
