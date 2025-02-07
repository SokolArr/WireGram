import logging
import sys
import os
from settings import settings

DEBUG_MODE = settings.DEBUG_MODE

LOG_FORMATTER = logging.Formatter(
    "[%(asctime)s]-[%(name)s]-%(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class MainLogger:
    def __init__(self, logger_name: str = "main", log_path: str = "./logs"):
        os.makedirs(log_path, exist_ok=True)
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(
            logging.DEBUG if settings.DEBUG_MODE else logging.INFO
        )

        log_file_path = os.path.join(log_path, "main.log")
        self._add_handlers(self.logger, log_file_path)

        self.config_sqlalchemy(log_file_path)

    @staticmethod
    def _add_handlers(logger: logging.Logger, log_file_path: str):
        if not logger.handlers:
            # file
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setFormatter(LOG_FORMATTER)

            # console
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(LOG_FORMATTER)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

    @staticmethod
    def config_sqlalchemy(log_file_path: str):
        logger = logging.getLogger("sqlalchemy.engine")
        logger.setLevel(logging.DEBUG if settings.DEBUG_MODE else logging.INFO)
        MainLogger._add_handlers(logger, log_file_path)

    def get(self):
        return self.logger


logger = MainLogger().get()
