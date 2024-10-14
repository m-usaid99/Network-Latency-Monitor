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
import sys
from collections import deque
from rich.console import Console
from loguru import logger  # Import Loguru's logger

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
from network_latency_monitor.ping_manager import run_ping_monitoring_quiet
from network_latency_monitor.console_manager import NullConsole, console_proxy

# TODO: - implement multiple verbosity levels
#       - fix config file console prints
#       - incorporate use of --yes flag
#       - try implementing quiet mode


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

    # Merge CLI arguments into config
    config = merge_args_into_config(args, config)

    # Validate configuration
    validate_config(config)

    # Determine verbosity level and map to log levels
    verbosity = config.get("verbosity", 0)

    if verbosity == -1:
        # Quiet Mode
        log_level_file = "ERROR"
        log_level_console = "ERROR"  # Not used since console is suppressed
        active_console = NullConsole()
    elif verbosity == 0:
        # Normal Mode
        log_level_file = "INFO"
        log_level_console = "WARNING"
        active_console = Console()  # Reuse the real Console
    elif verbosity == 1:
        # Verbose Mode
        log_level_file = "INFO"
        log_level_console = "INFO"
        active_console = Console()
    elif verbosity >= 2:
        # Debug Mode
        log_level_file = "DEBUG"
        log_level_console = "DEBUG"
        active_console = Console()
    else:
        # Fallback to Normal Mode
        log_level_file = "INFO"
        log_level_console = "WARNING"
        active_console = Console()

    # Setup logging with determined log levels
    setup_logging(
        log_folder=config.get("log_dir"),
        log_level_file=log_level_file,
        log_level_console=log_level_console,
    )

    # Assign the active console based on verbosity
    console_proxy.set_console(active_console)

    # Log that logging has been set up
    logger.info("Logging has been configured successfully.")

    # Handle clear operations if any
    handle_clear_operations(config)

    # If file mode is enabled, process the file directly
    if config.get("file"):
        logger.info("Processing file mode.")
        process_file_mode(config)
        logger.info("File processing completed.")
        sys.exit(0)  # Exit after processing the file

    # Validate IP addresses
    config["ip_addresses"] = validate_and_get_ips(config)
    logger.debug(f"Validated IP addresses: {config['ip_addresses']}")

    # Create results subdirectory with timestamp
    results_subfolder = create_results_directory(config)
    logger.info(f"Results will be stored in: {results_subfolder}")

    # Initialize in-memory latency data storage
    latency_window = 30  # Number of data points in the sliding window
    latency_data = {
        ip: deque([0] * latency_window, maxlen=latency_window)
        for ip in config["ip_addresses"]
    }
    logger.debug(f"Initialized latency data storage: {latency_data}")

    # Start ping monitoring with enhanced progress bars and real-time charts
    if verbosity != -1:
        console_proxy.console.print(
            "[bold blue]Starting ping monitoring...[/bold blue]"
        )
    logger.info("Ping monitoring initiated.")
    # Start ping monitoring with or without console output based on verbosity
    if verbosity == -1:
        await run_ping_monitoring_quiet(config, results_subfolder)
    else:
        await run_ping_monitoring(config, results_subfolder, latency_data)
    logger.info("Ping monitoring completed.")
    if verbosity != -1:
        console_proxy.console.print(
            "[bold green]Ping monitoring completed.[/bold green]"
        )

    # Process ping results
    data_dict = process_ping_results(results_subfolder, config)
    logger.debug(f"Processed ping results: {data_dict}")

    # Generate plots and display summary statistics
    display_plots_and_summary(data_dict, config)
    logger.info("Plots generated and summary statistics displayed.")


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
        logger.warning("Ping monitoring interrupted by user.")
        verbosity = 0
        try:
            config = load_config()
            verbosity = config.get("verbosity", 0)
        except:  # noqa: E722
            logger.info("will replace with real logic later.")

        if verbosity != -1:
            console_proxy.console.print(
                "\n[bold red]Ping monitoring interrupted by user.[/bold red]"
            )
        sys.exit(0)


if __name__ == "__main__":
    cli()
