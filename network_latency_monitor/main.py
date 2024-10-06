# main.py

"""
Network Latency Monitor (NLM) Main Module

This module serves as the entry point for the NLM tool. It orchestrates the execution flow,
including argument parsing, configuration loading and validation, logging setup, data clearing,
IP address validation, ping monitoring initiation, result processing, and output display.

Functions:
    - main: Asynchronous main function that runs the NLM tool.
    - cli: Synchronous entry point for the console script.
"""

import asyncio
import logging
import os
import sys
from collections import deque

from rich.console import Console

from network_latency_monitor import (
    create_results_directory,
    display_plots_and_summary,
    handle_clear_operations,
    load_config,
    merge_args_into_config,
    parse_arguments,
    process_file_mode,
    process_ping_results,
    regenerate_default_config,
    run_ping_monitoring,
    setup_logging,
    validate_and_get_ips,
    validate_config,
)

# Initialize Rich Console
console = Console()

# TODO:
#       - make main.py modular
#       - figure out filepath where shit is saved
#       - create documentation
#       - turn it into publishable package
#       - try to fix flicker
#       - add interactivity thru keyboard controls


async def main():
    """
    Asynchronous main function that runs the Network Latency Monitor (NLM) tool.

    This function orchestrates the entire execution flow of the NLM tool, including:
        - Parsing command-line arguments.
        - Handling configuration regeneration.
        - Loading and validating configurations.
        - Setting up logging.
        - Handling data clearing operations.
        - Processing existing ping result files if provided.
        - Validating IP addresses.
        - Creating results directory.
        - Initializing latency data storage.
        - Starting ping monitoring.
        - Processing ping results.
        - Generating plots and displaying summary statistics.

    Raises:
        SystemExit: If critical errors occur or after certain operations like config regeneration.

    Example:
        >>> asyncio.run(main())
        # Starts the NLM tool.
    """

    # Parse command-line arguments
    args = parse_arguments()

    # Handle configuration regeneration
    if args.regen_config:
        regenerate_default_config()
        sys.exit(0)

    # Load configuration
    config = load_config()

    if not os.path.exists("config.yaml") or os.path.getsize("config.yaml") == 0:
        console.print(
            "[bold yellow]A default 'config.yaml' has been created. Please review and modify it as needed before running the tool again.[/bold yellow]"
        )
        sys.exit(0)

    config = merge_args_into_config(args, config)
    validate_config(config)
    # Setup logging (logs are written to files only)
    setup_logging(config.get("log_folder", "logs"))

    logging.info("Configuration and arguments loaded.")
    logging.info(f"Configuration: {config}")
    logging.info(f"Arguments: {args}")

    # Handle clear operations if any
    handle_clear_operations(config)

    # If file mode is enabled, process the file directly
    process_file_mode(config)

    # Validate IP addresses
    config["ip_addresses"] = validate_and_get_ips(config)

    # Create results subdirectory with timestamp
    results_subfolder = create_results_directory(config)

    # Initialize in-memory latency data storage
    latency_window = 30  # Number of data points in the sliding window
    latency_data = {
        ip: deque([0] * latency_window, maxlen=latency_window)
        for ip in config["ip_addresses"]
    }

    # Start ping monitoring with enhanced progress bars and real-time charts
    console.print("[bold blue]Starting ping monitoring...[/bold blue]")
    await run_ping_monitoring(config, results_subfolder, latency_data)
    console.print("[bold green]Ping monitoring completed.[/bold green]")
    logging.info("All ping tasks completed.")

    # Process ping results
    data_dict = process_ping_results(results_subfolder, config)

    # Generate plots and display summary statistics
    display_plots_and_summary(data_dict, config)


def cli():
    """
    Synchronous entry point for the console script.

    This function serves as the main entry point when the NLM tool is invoked from the command line.
    It handles the asynchronous execution of the main function and manages keyboard interrupts gracefully.

    Example:
        >>> cli()
        # Runs the NLM tool from the command line.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Ping monitoring interrupted by user.[/bold red]")
        logging.warning("Ping monitoring interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    cli()
