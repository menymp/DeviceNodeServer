import logging
import sys

def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Create and configure a logger.

    Args:
        name (str): Name of the logger (usually __name__).
        level (int): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:  # Prevent duplicate handlers if called multiple times
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
