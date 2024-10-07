# logger.py

"""
Logging Configuration

Sets up logging for the Network Latency Monitor (NLM) tool. This module initializes
the logging system, ensuring that logs are properly formatted and stored in designated
log files with appropriate log levels. It implements log rotation to manage log file sizes
and prevents duplicate log entries by configuring the logger as a singleton.

Functions:
    - setup_logging: Configures logging settings with log rotation and appropriate handlers.
"""

from datetime import datetime
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import sys

# Define a module-level logger to implement the Singleton pattern
_logger_initialized = False


def setup_logging(
    log_folder: str,
    log_level_file: int = logging.INFO,
    log_level_console: int = logging.WARNING,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 5,
) -> None:
    """
    Configures the logging settings for the NLM tool with log rotation and appropriate handlers.

    This function sets up the logging system by creating a log directory if it doesn't exist,
    initializing a log file with a timestamped name, and configuring both file and console
    handlers with specified logging levels. It also implements log rotation to prevent log
    files from growing indefinitely and ensures that logging is configured only once to
    avoid duplicate log entries.

    Args:
        log_folder (str): The directory where log files will be stored.
        log_level_file (int, optional): Logging level for the file handler. Defaults to logging.INFO.
        log_level_console (int, optional): Logging level for the console handler. Defaults to logging.WARNING.
        max_bytes (int, optional): Maximum size in bytes for a single log file before rotation. Defaults to 5 MB.
        backup_count (int, optional): Number of backup log files to keep. Defaults to 5.

    Raises:
        OSError: If the log directory cannot be created due to permission issues or other OS-related errors.

    Example:
        >>> setup_logging(log_folder="logs")
    """
    global _logger_initialized

    if _logger_initialized:
        # Prevent re-initializing the logger
        return

    try:
        # Create the log directory using pathlib.Path
        log_dir = Path(log_folder)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Generate a safe timestamp for the log file name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = log_dir / f"nlm_{timestamp}.log"

        # Create a custom logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # Set the root logger level to DEBUG

        # File Handler with log rotation
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",  # Specify encoding for consistency
        )
        file_handler.setLevel(log_level_file)  # Set file handler level

        # Console Handler for critical issues
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level_console)  # Set console handler level

        # Create formatter and add it to the handlers
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Log the initialization
        logging.getLogger("matplotlib").setLevel(logging.ERROR)
        _logger_initialized = True  # Mark logger as initialized

    except OSError as e:
        print(f"Failed to create log directory '{log_folder}': {e}", file=sys.stderr)
        raise
