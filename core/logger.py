import sys
import os
from loguru import logger

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

def setup_logger(log_level="INFO"):
    logger.remove()
    
    # Console sink
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
    )
    
    # Main app log
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="1 week",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message} | {extra}",
    )
    
    # Specific error log
    logger.add(
        "logs/errors.log",
        rotation="10 MB",
        retention="1 month",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message} | {extra}",
    )
    
    return logger

app_logger = setup_logger()
