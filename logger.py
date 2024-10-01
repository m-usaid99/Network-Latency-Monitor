# logger.py

import logging
import os
from datetime import datetime


def setup_logging(log_folder="logs"):
    os.makedirs(log_folder, exist_ok=True)
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_folder, f"wifi_ping_monitor_{current_date}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    logging.info("Logging initialized.")

    return log_file
