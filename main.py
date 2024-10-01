# main.py
import asyncio
import sys
import logging
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from datetime import datetime
import pandas as pd
import ipaddress

from cli import parse_arguments
from config import load_config
from logger import setup_logging
from ping_manager import run_ping
from plot_generator import (
    extract_ping_times,
    aggregate_ping_times,
    generate_plots,
    process_ping_file,
    display_summary,
)
from utils import clear_data
from typing import Dict


# TODO: - examine packet loss data and see how to incorporate it better
#       - Turn it into a python package to make it pip installable
#       - add cross platform compatibility
#       - Look up how to incorporate real-time graph.
#       - add more config options
#       - update documentation to reflect changes

# Initialize Rich Console
console = Console()


def ask_confirmation(message: str, auto_confirm: bool) -> bool:
    """
    Prompts the user for a yes/no confirmation unless auto_confirm is True.
    """
    if auto_confirm:
        return True

    response = Prompt.ask(f"{message}", choices=["y", "n"], default="n")
    return response.lower() in ["y", "yes"]


def handle_clear_operations(args, config):
    """
    Handles data clearing operations based on command-line arguments.
    """
    folders_to_clear = []
    confirmation_message = ""

    if args.clear:
        folders_to_clear = [
            config.get("results_folder", "results"),
            config.get("plots_folder", "plots"),
            config.get("log_folder", "logs"),
        ]
        confirmation_message = (
            "Are you sure you want to clear ALL data (results, plots, logs)?"
        )
    else:
        if args.clear_results:
            folders_to_clear.append(config.get("results_folder", "results"))
        if args.clear_plots:
            folders_to_clear.append(config.get("plots_folder", "plots"))
        if args.clear_logs:
            folders_to_clear.append(config.get("log_folder", "logs"))
        confirmation_message = "Are you sure you want to clear the selected data?"

    if folders_to_clear:
        if ask_confirmation(confirmation_message, args.yes):
            clear_data(args, config)
            console.print(
                "[bold green]Selected data has been cleared successfully.[/bold green]"
            )
            logging.info("Clear operation completed.")
        else:
            console.print("[bold yellow]Clear operation canceled.[/bold yellow]")
            logging.info("Clear operation canceled by user.")
        sys.exit(0)  # Exit after clearing


def process_file_mode(args, config):
    """
    Processes the ping result file if file mode is enabled.
    """
    if args.file:
        console.print(
            f"[bold green]Processing ping result file:[/bold green] {args.file}"
        )
        logging.info(f"Processing ping result file: {args.file}")
        process_ping_file(
            file_path=args.file,
            config=config,
            no_aggregation=args.no_aggregation,
            duration=args.duration,
        )
        console.print("[bold green]Processing of ping file completed.[/bold green]")
        logging.info("Processing of ping file completed.")
        sys.exit(0)  # Exit after processing file


def validate_and_get_ips(args, config) -> list:
    """
    Validates the list of IP addresses and returns the validated list.
    """
    ips = args.ip_addresses or [config.get("ip_address", "8.8.8.8")]

    if not args.ip_addresses:
        default_ip = config.get("ip_address", "8.8.8.8")
        console.print(
            f"[bold yellow]No IP addresses provided. Using default IP:[/bold yellow] {default_ip}"
        )
        logging.info(f"No IP addresses provided. Using default IP: {default_ip}")

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
    Creates a results subdirectory with a timestamp and returns its path.
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


async def run_ping_monitoring(args, config, results_subfolder):
    """
    Initiates ping monitoring with progress bars.
    """
    duration = args.duration
    ping_interval = args.ping_interval
    ips = args.ip_addresses
    tasks = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Pinging {task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        for ip in ips:
            results_file = os.path.join(results_subfolder, f"ping_results_{ip}.txt")
            # Initialize each progress bar with a unique task
            task_id = progress.add_task(f"[cyan]{ip}", total=duration)
            task = asyncio.create_task(
                run_ping(
                    ip_address=ip,
                    duration=duration,
                    interval=ping_interval,
                    results_file=results_file,
                    progress=progress,
                    task_id=task_id,
                )
            )
            tasks.append(task)

        await asyncio.gather(*tasks)


def process_ping_results(results_subfolder, args) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Processes ping results and returns a data dictionary.
    """
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
        if args.duration < 60:
            console.print(
                f"[bold yellow]Duration ({args.duration}s) is less than 60 seconds. Aggregation disabled for {ip_address}.[/bold yellow]"
            )
            logging.info(
                f"Duration ({args.duration}s) is less than 60 seconds. Aggregation disabled for {ip_address}."
            )
            aggregate = False
        else:
            aggregate = not args.no_aggregation

        if aggregate:
            aggregated_data = aggregate_ping_times(ping_times, interval=60)
            agg_df = pd.DataFrame(
                aggregated_data, columns=["Time (s)", "Mean Latency (ms)"]
            )
            # Ensure no NaN values in agg_df
            agg_df["Mean Latency (ms)"] = agg_df["Mean Latency (ms)"].fillna(0.0)
            logging.debug(f"Aggregated data for {ip_address}: {aggregated_data}")
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
    """
    # Generate plots if data is available
    if data_dict:
        console.print("[bold blue]Generating plots...[/bold blue]")
        generate_plots(config=config, data_dict=data_dict)
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
    # Load configuration
    config = load_config()
    # Setup logging (logs are written to files only)
    setup_logging(config.get("log_folder", "logs"))

    logging.info("Configuration and arguments loaded.")
    logging.info(f"Configuration: {config}")
    logging.info(f"Arguments: {args}")

    # Handle clear operations if any
    handle_clear_operations(args, config)

    # If file mode is enabled, process the file directly
    process_file_mode(args, config)

    # Validate IP addresses
    args.ip_addresses = validate_and_get_ips(args, config)

    # Create results subdirectory with timestamp
    results_subfolder = create_results_directory(config)

    # Start ping monitoring with enhanced progress bars
    console.print("[bold blue]Starting ping monitoring...[/bold blue]")
    await run_ping_monitoring(args, config, results_subfolder)
    console.print("[bold green]Ping monitoring completed.[/bold green]")
    logging.info("All ping tasks completed.")

    # Process ping results
    data_dict = process_ping_results(results_subfolder, args)

    # Generate plots and display summary statistics
    display_plots_and_summary(data_dict, config)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Ping monitoring interrupted by user.[/bold red]")
        logging.warning("Ping monitoring interrupted by user.")
        sys.exit(0)
