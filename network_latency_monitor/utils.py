# utils.py

"""
Utility Functions

Provides a collection of utility functions used across the Network Latency Monitor (NLM) tool.
These functions handle tasks such as data directory management, user confirmations, IP address
validation, and result directory creation.

Functions:
    - clear_data: Clears specified data directories.
    - ask_confirmation: Prompts the user for a yes/no confirmation unless auto_confirm is True.
    - handle_clear_operations: Handles data clearing operations based on configuration flags.
    - validate_and_get_ips: Validates the list of IP addresses and returns the validated list.
    - create_results_directory: Creates a results subdirectory with a timestamp and returns its path.
"""

from datetime import datetime
import ipaddress
import logging
import os
import shutil
import sys

from rich.console import Console
from rich.prompt import Prompt

console = Console()


def clear_data(folders_to_clear: list) -> None:
    """
    Removes specified directories and their contents.

    This function iterates through a list of folder paths and deletes each one using
    `shutil.rmtree`. It logs the outcome of each deletion attempt, noting whether
    the folder was successfully cleared or if it was not found.

    Args:
        folders_to_clear (List[str]): A list of directory paths to be removed.

    Raises:
        OSError: If a folder cannot be removed due to permission issues or other OS-related errors.
    """
    for folder in folders_to_clear:
        try:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                logging.info(f"Cleared folder: {folder}")
            else:
                logging.warning(f"Folder not found: {folder}")
        except OSError as e:
            logging.error(f"Failed to clear folder '{folder}': {e}")
            raise


def ask_confirmation(message: str, auto_confirm: bool) -> bool:
    """
    Prompts the user for a yes/no confirmation unless auto_confirm is True.

    This function displays a confirmation message to the user, asking for a 'y' or 'n' response.
    If `auto_confirm` is set to True, the function automatically returns True without prompting.

    Args:
        message (str): The confirmation message to display to the user.
        auto_confirm (bool): If True, automatically confirm without prompting.

    Returns:
        bool: True if the user confirms, False otherwise.
    """
    if auto_confirm:
        return True

    response = Prompt.ask(f"{message}", choices=["y", "n"], default="n")
    return response.lower() in ["y", "yes"]


def handle_clear_operations(config):
    """
    Manages data clearing operations based on configuration flags.

    Depending on the configuration settings, this function determines which data directories
    (results, plots, logs) need to be cleared. It then prompts the user for confirmation
    (unless auto-confirmed) and proceeds to clear the specified directories.

    Args:
        config (Dict): Configuration dictionary containing flags and directory paths.

    Raises:
        SystemExit: Exits the program after clearing operations are handled.
    """
    folders_to_clear = []
    confirmation_message = ""

    # Check if any clear operation is requested
    if config.get("clear", False):
        folders_to_clear = [
            config.get("results_folder", "results"),
            config.get("plots_folder", "plots"),  # Include plots_folder
            config.get("log_folder", "logs"),
        ]
        confirmation_message = (
            "Are you sure you want to clear ALL data (results, plots, logs)?"
        )
    else:
        if config.get("clear_results", False):
            folders_to_clear.append(config.get("results_folder", "results"))
        if config.get("clear_plots", False):  # Handle clear_plots
            folders_to_clear.append(config.get("plots_folder", "plots"))
        if config.get("clear_logs", False):
            folders_to_clear.append(config.get("log_folder", "logs"))
        if folders_to_clear:
            confirmation_message = "[bold yellow]Are you sure you want to clear the selected data?[/bold yellow]"

    if folders_to_clear:
        if ask_confirmation(confirmation_message, config.get("yes", False)):
            clear_data(folders_to_clear)
            console.print(
                "[bold green]Selected data has been cleared successfully.[/bold green]"
            )
            logging.info("Clear operation completed.")
        else:
            console.print("[bold yellow]Clear operation canceled.[/bold yellow]")
            logging.info("Clear operation canceled by user.")
        sys.exit(0)  # Exit after clearing


def validate_and_get_ips(config) -> list:
    """
    Validates the list of IP addresses and returns the validated list.

    This function checks each IP address provided in the configuration for validity.
    Invalid IP addresses are reported, and if none are valid, the program exits.

    Args:
        config (Dict): Configuration dictionary containing the list of IP addresses.

    Returns:
        List[str]: A list of validated IP addresses.

    Raises:
        SystemExit: If no valid IP addresses are provided.
    """
    ips = config.get("ip_addresses", ["8.8.8.8"])

    if not ips:
        default_ip = ["8.8.8.8"]
        console.print(
            f"[bold yellow]No IP addresses provided. Using default IP:[/bold yellow] {default_ip[0]}"
        )
        logging.info(f"No IP addresses provided. Using default IP: {default_ip[0]}")
        ips = default_ip

    validated_ips = []
    for ip in ips:
        try:
            ipaddress.ip_address(ip)
            validated_ips.append(ip)
        except ValueError:
            console.print(f"[bold red]Invalid IP address:[/bold red] {ip}")
            logging.error(f"Invalid IP address provided: {ip}")

    if not validated_ips:
        console.print("[bold red]No valid IP addresses provided. Exiting.[/bold red]")
        logging.error("No valid IP addresses provided. Exiting.")
        sys.exit(1)

    return validated_ips


def create_results_directory(config) -> str:
    """
    Processes the ping result file if file mode is enabled.

    If a file path is provided in the configuration, this function processes the ping results
    contained within that file. It leverages the `process_ping_file` function to handle the
    processing based on the current configuration settings, such as aggregation and latency thresholds.

    Args:
        config (Dict): Configuration dictionary containing settings and file path.

    Raises:
        SystemExit: Exits the program after processing the file.
    """
    results_folder = config.get("results_folder", "results")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_subfolder = os.path.join(results_folder, f"results_{timestamp}")
    os.makedirs(results_subfolder, exist_ok=True)
    console.print(
        f"[bold green]Created results subdirectory:[/bold green] {results_subfolder}"
    )
    logging.info(f"Created results subdirectory: {results_subfolder}")
    return results_subfolder
