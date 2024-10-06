# utils.py

import os
import shutil
import logging


def clear_data(folders_to_clear: list) -> None:
    """
    Clears specified data directories.

    :param folders_to_clear: List of folder paths to clear.
    """
    for folder in folders_to_clear:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            logging.info(f"Cleared folder: {folder}")
        else:
            logging.warning(f"Folder not found: {folder}")
