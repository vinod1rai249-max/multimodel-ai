import sys
from loguru import logger

def setup_logger(log_level="INFO"):
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
    )
    logger.add(
        "app.log",
        rotation="10 MB",
        retention="1 week",
        level="DEBUG",
    )
    return logger

app_logger = setup_logger()
