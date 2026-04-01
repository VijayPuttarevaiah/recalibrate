import sys
import os
from loguru import logger
from config.config import Config

class LogManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._configure_logger()
        return cls._instance

    def _configure_logger(self):
        config_manager = Config()
        log_cfg = config_manager.get_logging_config()

        # Resolve the absolute path to the logs directory relative to the backend root
        # instead of relying on CWD
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file_path = os.path.abspath(os.path.join(base_dir, log_cfg["file_path"]))
        log_dir = os.path.dirname(log_file_path)

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Remove default logger
        logger.remove()

        # Add console logger
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            level=log_cfg["level"],
            format=console_format,
        )

        # Add file logger
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        )
        logger.add(
            log_file_path,
            level=log_cfg["level"],
            rotation=log_cfg["rotation"],
            retention=log_cfg["retention"],
            format=file_format,
            compression="zip",
        )
        self.logger = logger

    @staticmethod
    def get_logger():
        return LogManager().logger
