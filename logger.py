# logger.py

import logging
import os
from datetime import datetime


def setup_logging(log_folder: str) -> None:
    """
    Sets up logging configuration to log messages only to a file.

    :param log_folder: Directory where log files will be stored.
    """
    os.makedirs(log_folder, exist_ok=True)
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_folder, f"wifi_ping_monitor_{current_date}.log")

    # Create a custom logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set the desired logging level

    # Create handlers
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)  # Set the desired logging level for the file

    # Create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)

    # Optionally, remove other handlers if they exist to prevent duplicate logs
    if logger.hasHandlers():
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                logger.removeHandler(handler)

    logger.info(f"Logging initialized. Logs are being written to: {log_file}")

