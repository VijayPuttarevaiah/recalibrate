
import os
import configparser


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

    
        # Read from config file
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
        self.config = config