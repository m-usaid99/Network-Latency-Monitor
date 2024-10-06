# main.py

import asyncio
import sys
import logging
import os
from rich.console import Console
import pandas as pd
from network_latency_monitor.cli import parse_arguments
from network_latency_monitor.config import (
    load_config,
    regenerate_default_config,
    merge_args_into_config,
    validate_config,
)
from network_latency_monitor.logger import setup_logging
from network_latency_monitor.ping_manager import run_ping_monitoring
from network_latency_monitor.plot_generator import (
    generate_plots,
    display_summary,
)
from network_latency_monitor.utils import handle_clear_operations
from typing import Dict, Optional
from collections import deque

# Initialize Rich Console
console = Console()

# TODO:
#       - make main.py modular
#       - create documentation
#       - turn it into publishable package
#       - try to fix flicker
#       - add interactivity thru keyboard controls


def process_ping_results(
    results_subfolder, config
) -> Dict[str, Dict[str, pd.DataFrame]]:
    data_dict = {}
    ip_files = [
        f
        for f in os.listdir(results_subfolder)
        if f.startswith("ping_results_") and f.endswith(".txt")
    ]

    for file_name in ip_files:
        file_path = os.path.join(results_subfolder, file_name)
        # Extract IP address from filename
        ip_address = file_name[len("ping_results_") : -len(".txt")]
        ping_times = extract_ping_times(file_path)
        if not ping_times:
            console.print(
                f"[bold red]No ping times extracted from {file_path}. Skipping.[/bold red]"
            )
            logging.warning(f"No ping times extracted from {file_path}. Skipping.")
            continue

        # Determine if aggregation should be enforced based on duration
        duration = config.get("duration", 10800)
        if duration < 60:
            console.print(
                f"[bold yellow]Duration ({duration}s) is less than 60 seconds. Aggregation disabled for {ip_address}.[/bold yellow]"
            )
            logging.info(
                f"Duration ({duration}s) is less than 60 seconds. Aggregation disabled for {ip_address}."
            )
            aggregate = False
        else:
            aggregate = not config.get("no_aggregation", False)

        if aggregate:
            aggregated_data = aggregate_ping_times(ping_times, interval=60)
            agg_df: Optional[pd.DataFrame] = pd.DataFrame(
                aggregated_data,
                columns=["Time (s)", "Mean Latency (ms)", "Packet Loss (%)"],
            )
            # Ensure no NaN values in agg_df
            agg_df["Mean Latency (ms)"] = agg_df["Mean Latency (ms)"].fillna(0.0)
            agg_df["Packet Loss (%)"] = agg_df["Packet Loss (%)"].fillna(
                100.0
            )  # If packet loss is NaN, assume 100%
            logging.debug(f"Aggregated data for {ip_address}:\n{agg_df}")
            logging.info(
                f"Aggregated {len(aggregated_data)} intervals for {ip_address}."
            )
        else:
            agg_df = None

        # Convert raw ping times to DataFrame
        raw_df = pd.DataFrame(
            {"Time (s)": range(1, len(ping_times) + 1), "Ping (ms)": ping_times}
        )

        # Store data
        data_dict[ip_address] = {"raw": raw_df, "aggregated": agg_df}

    return data_dict


def display_plots_and_summary(data_dict, config):
    """
    Generates plots and displays summary statistics if data is available.

    :param data_dict: Dictionary containing ping data for each IP.
    :param config: Configuration dictionary.
    """
    latency_threshold = config.get("latency_threshold", 200.0)
    no_segmentation = config.get("no_segmentation", False)

    # Generate plots if data is available
    if data_dict:
        console.print("[bold blue]Generating plots...[/bold blue]")
        generate_plots(
            config=config,
            data_dict=data_dict,
            latency_threshold=latency_threshold,
            no_segmentation=no_segmentation,
        )
        console.print("[bold green]Plot generation completed.[/bold green]")
        logging.info("Plot generation completed.")
    else:
        console.print("[bold red]No data available for plotting.[/bold red]")
        logging.warning("No data available for plotting.")

    # Display summary statistics
    if data_dict:
        console.print("[bold blue]Displaying Summary Statistics...[/bold blue]")
        display_summary(data_dict)
        logging.info("Summary statistics displayed.")
    else:
        console.print("[bold red]No data available for summary statistics.[/bold red]")
        logging.warning("No data available for summary statistics.")


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
