# logger.py

"""
Logging Configuration

Sets up logging for the Network Latency Monitor (NLM) tool. This module initializes
the logging system, ensuring that logs are properly formatted and stored in designated
log files with appropriate log levels.

Functions:
    - setup_logging: Configures logging settings.
"""

import logging
import os
import sys
from datetime import datetime


def setup_logging(log_folder: str) -> None:
    """
    Configures the logging settings for the NLM tool.

    This function sets up the logging system by creating a log directory if it doesn't exist,
    initializing a log file with a timestamped name, and configuring the logging level and format.
    It ensures that all logs are written to both the log file and the console for real-time monitoring.

    Args:
        log_folder (str): The directory where log files will be stored.

    Raises:
        OSError: If the log directory cannot be created due to permission issues or other OS-related errors.
    """
    try:
        # Create the log directory if it doesn't exist
        os.makedirs(log_folder, exist_ok=True)
        logging.debug(f"Log directory ensured at: {log_folder}")

        # Generate a timestamped log file name
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(log_folder, f"nlm_{current_date}.log")

        # Create a custom logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # Set the root logger level to DEBUG

        # Prevent adding multiple handlers if the logger already has them
        if not logger.handlers:
            # Create handlers
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)  # Set file handler to INFO level

            console_handler = logging.StreamHandler()
            console_handler.setLevel(
                logging.WARNING
            )  # Set console handler to WARNING level

            # Create formatter and add it to the handlers
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add the handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

            logging.info(f"Logging initialized. Logs are being written to: {log_file}")
            logging.debug("File and console handlers added to the logger.")
    except OSError as e:
        print(f"Failed to create log directory '{log_folder}': {e}", file=sys.stderr)
        raise

