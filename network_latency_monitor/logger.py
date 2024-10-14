# logger.py

"""
Logging Configuration

Sets up logging for the Network Latency Monitor (NLM) tool using Loguru. This module initializes
the logging system, ensuring that logs are properly formatted and stored in designated
log files with appropriate log levels. It implements log rotation to manage log file sizes
and prevents duplicate log entries by configuring the logger as a singleton.

Functions:
    - setup_logging: Configures logging settings with log rotation and appropriate sinks.
"""

from datetime import datetime
from pathlib import Path
import sys
from loguru import logger

# Define a module-level flag to implement the Singleton pattern
_logger_initialized = False


def setup_logging(
    log_folder: str,
    log_level_file: str = "INFO",
    log_level_console: str = "WARNING",
    rotation: str = "5 MB",
    retention: int = 5,  # Number of backup log files to keep
) -> None:
    """
    Configures the logging settings for the NLM tool with log rotation and appropriate sinks.

    Args:
        log_folder (str): The directory where log files will be stored.
        log_level_file (str, optional): Logging level for the file sink. Defaults to "INFO".
        log_level_console (str, optional): Logging level for the console sink. Defaults to "WARNING".
        rotation (str, optional): Log rotation criteria. Defaults to "5 MB".
        retention (int, optional): Number of backup log files to keep. Defaults to 5.

    Raises:
        OSError: If the log directory cannot be created due to permission issues or other OS-related errors.
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

        # Remove any default Loguru sinks to prevent duplicate logs
        logger.remove()

        # Add File Sink with log rotation and retention
        logger.add(
            log_file,
            level=log_level_file,
            rotation=rotation,
            retention=retention,  # Pass retention as an integer
            encoding="utf-8",
            enqueue=True,  # Ensures thread-safe logging
            serialize=False,  # Set to True if you prefer JSON logs
        )

        # Add Console Sink with specified log level
        logger.add(
            sys.stdout,
            level=log_level_console,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "{message}",
            colorize=True,
            enqueue=True,
        )

        # Suppress logs from specific libraries if necessary
        # Example: Suppressing matplotlib logs
        logger.configure(extra={"matplotlib": {"level": "ERROR"}})

        # Log the initialization
        logger.debug("Logging has been configured successfully.")

        _logger_initialized = True  # Mark logger as initialized

    except OSError as e:
        print(f"Failed to create log directory '{log_folder}': {e}", file=sys.stderr)
        raise
