import os
import configparser

# Singleton class to manage and provide application configuration from a file
class Config:
    _instance = None

    def __new__(cls):
        # Create a new instance only if one doesn't already exist
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Prevent re-initialization of the singleton instance
        if self._initialized:
            return

        # Initialize the configparser and read settings from the local config.ini file
        config = configparser.ConfigParser()
        # Resolve the absolute path to the config.ini file located in the same directory
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        config.read(config_path)
        self.config = config
        
        # Mark the instance as initialized
        self._initialized = True