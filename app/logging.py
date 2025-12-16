"""Dependencies for logging."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO", log_dir: str = "logs", app_name: str = "app") -> None:
    """Initialize logging."""
    logger.remove()

    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | \
                <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
    )

    logger.add(
        log_path / f"{app_name}.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | " "{level: <8} | " "{name}:{function}:{line} | " "{message} | " "{extra}"
        ),
        level=log_level,
        enqueue=True,
    )

    logger.add(
        log_path / f"{app_name}.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format=("{time:YYYY-MM-DD HH:mm:ss.SSS} | " "{level: <8} | " "{name}:{function}:{line} | " "{message}"),
        level=log_level,
        enqueue=True,
    )

    logger.info(f"Logging initialized. Logs directory: {log_path.absolute()}")
