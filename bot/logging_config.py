"""
Centralized logging configuration.

All API requests, responses, and errors are logged to a rotating log file
(trading_bot.log) as well as to the console (console shows INFO+ only,
the file captures DEBUG+ for full request/response detail).
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")


def setup_logger(name: str = "trading_bot") -> logging.Logger:
    """Create (or return existing) configured logger.

    - File handler: DEBUG level, rotates at 5MB, keeps 3 backups.
    - Console handler: INFO level, concise format.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if setup_logger() is called more than once
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
