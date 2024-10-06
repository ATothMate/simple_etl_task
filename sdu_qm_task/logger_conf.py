#!/usr/bin/env python3

import logging


def get_logger(name: str=__file__, level: int=logging.INFO) -> logging.Logger:
    """Creates and configure a logger.

    Args:
        name (str, optional): name of the logger. Defaults to 'current file name'.
        level (int, optional): logging level. Defaults to logging.INFO (20).

    Returns:
        logging.Logger: configured logger instance.
    """
    # Create logger with given name and logging level
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Check if handlers already exist (to prevent adding duplicate handlers)
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Create formatter and attach it to the handler
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)

        # Add configured handler to logger
        logger.addHandler(console_handler)

    return logger
