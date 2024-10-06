# main.py

import asyncio
import logging
import os
import sys
from collections import deque

from rich.console import Console

from network_latency_monitor.cli import parse_arguments
from network_latency_monitor.config import (
    load_config,
    merge_args_into_config,
    regenerate_default_config,
    validate_config,
)
from network_latency_monitor.data_processing import (
    process_file_mode,
    process_ping_results,
)
from network_latency_monitor.logger import setup_logging
from network_latency_monitor.ping_manager import run_ping_monitoring
from network_latency_monitor.plot_generator import display_plots_and_summary
from network_latency_monitor.utils import (
    handle_clear_operations,
    create_results_directory,
    validate_and_get_ips,
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
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Ping monitoring interrupted by user.[/bold red]")
        logging.warning("Ping monitoring interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    cli()
