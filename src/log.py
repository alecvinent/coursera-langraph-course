import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <cyan>{name}</cyan> | <level>{level:<8}</level> | {message}",
    level="INFO",
)
