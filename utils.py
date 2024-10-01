# utils.py

import os
import shutil
import logging
import argparse


def clear_data(args: argparse.Namespace, config: dict) -> None:
    """
    Clears specified data directories based on user arguments.

    :param args: Parsed command-line arguments.
    :param config: Configuration dictionary.
    """
    if args.clear:
        # Clear results, plots, and logs
        folders_to_clear = [
            config.get("results_folder", "results"),
            config.get("plots_folder", "plots"),
            config.get("log_folder", "logs"),
        ]
        for folder in folders_to_clear:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                logging.info(f"Cleared folder: {folder}")
            else:
                logging.warning(f"Folder not found: {folder}")

    else:
        if args.clear_results:
            folder = config.get("results_folder", "results")
            if os.path.exists(folder):
                shutil.rmtree(folder)
                logging.info(f"Cleared results folder: {folder}")
            else:
                logging.warning(f"Results folder not found: {folder}")

        if args.clear_plots:
            folder = config.get("plots_folder", "plots")
            if os.path.exists(folder):
                shutil.rmtree(folder)
                logging.info(f"Cleared plots folder: {folder}")
            else:
                logging.warning(f"Plots folder not found: {folder}")

        if args.clear_logs:
            folder = config.get("log_folder", "logs")
            if os.path.exists(folder):
                shutil.rmtree(folder)
                logging.info(f"Cleared logs folder: {folder}")
            else:
                logging.warning(f"Logs folder not found: {folder}")

