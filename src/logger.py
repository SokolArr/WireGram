import logging, sys
from settings import settings

class MainLogger:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.DEBUG_MODE else logging.INFO) 
    formatter = logging.Formatter('[%(asctime)s]-[%(name)s]-%(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    file_handler = logging.FileHandler('./logs/main.log')
    file_handler.setFormatter(formatter)

    #console_handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    #handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    
logger = MainLogger.logger