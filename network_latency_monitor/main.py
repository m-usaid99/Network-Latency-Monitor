# main.py

import asyncio
import sys
import logging
import os
from rich.console import Console
from rich.console import Group
from rich.columns import Columns
from rich.prompt import Prompt
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from datetime import datetime
import pandas as pd
import ipaddress
from network_latency_monitor.cli import parse_arguments
from network_latency_monitor.config import load_config
from network_latency_monitor.logger import setup_logging
from network_latency_monitor.ping_manager import run_ping
from network_latency_monitor.plot_generator import (
    extract_ping_times,
    aggregate_ping_times,
    generate_plots,
    process_ping_file,
    display_summary,
)
from network_latency_monitor.utils import clear_data
from typing import Dict, Optional
import asciichartpy
from collections import deque

# Initialize Rich Console
console = Console()

# TODO:
#       - create documentation
#       - turn it into publishable package
#       - try to fix flicker
#       - make config file work properly
#       - graceful error handling


def ask_confirmation(message: str, auto_confirm: bool) -> bool:
    """
    Prompts the user for a yes/no confirmation unless auto_confirm is True.
    """
    if auto_confirm:
        return True

    response = Prompt.ask(f"{message}", choices=["y", "n"], default="n")
    return response.lower() in ["y", "yes"]


def merge_args_into_config(args, config):
    """
    Merges command-line arguments into the configuration dictionary,
    giving precedence to CLI arguments over config file settings.
    """
    # Map CLI argument names to config keys
    arg_to_config_map = {
        "duration": "duration",
        "ping_interval": "ping_interval",
        "latency_threshold": "latency_threshold",
        "no_aggregation": "no_aggregation",
        "no_segmentation": "no_segmentation",
        # Add more mappings if needed
    }

    for arg_name, config_key in arg_to_config_map.items():
        arg_value = getattr(args, arg_name, None)
        if arg_value is not None:
            config[config_key] = arg_value

    # Handle positional arguments like ip_addresses
    if args.ip_addresses:
        config["ip_addresses"] = args.ip_addresses

    return config


def validate_config(config):
    """
    Validates configuration values.
    """
    # Validate duration
    if not isinstance(config.get("duration"), int) or config["duration"] <= 0:
        console.print("[bold red]Invalid duration in configuration.[/bold red]")
        sys.exit(1)

    # Validate ping_interval
    if not isinstance(config.get("ping_interval"), int) or config["ping_interval"] <= 0:
        console.print("[bold red]Invalid ping_interval in configuration.[/bold red]")
        sys.exit(1)

    # Validate latency_threshold
    if (
        not isinstance(config.get("latency_threshold"), float)
        or config["latency_threshold"] <= 0
    ):
        console.print(
            "[bold red]Invalid latency_threshold in configuration.[/bold red]"
        )
        sys.exit(1)

    # Add more validations as needed


def handle_clear_operations(config):
    """
    Handles data clearing operations based on command-line arguments.
    """
    folders_to_clear = []
    confirmation_message = ""

    # Assuming you have flags in config for clear operations
    if config.get("clear"):
        folders_to_clear = [
            config.get("results_folder", "results"),
            config.get("log_folder", "logs"),
        ]
        confirmation_message = (
            "Are you sure you want to clear ALL data (results, logs)?"
        )
    else:
        if config.get("clear_results"):
            folders_to_clear.append(config.get("results_folder", "results"))
        if config.get("clear_logs"):
            folders_to_clear.append(config.get("log_folder", "logs"))
        confirmation_message = "Are you sure you want to clear the selected data?"

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


def process_file_mode(config):
    """
    Processes the ping result file if file mode is enabled.
    """
    file_path = config.get("file")
    if file_path:
        console.print(
            f"[bold green]Processing ping result file:[/bold green] {file_path}"
        )
        logging.info(f"Processing ping result file: {file_path}")
        process_ping_file(
            file_path=file_path,
            config=config,
            no_aggregation=config.get("no_aggregation", False),
            duration=config.get("duration", 10800),
            latency_threshold=config.get("latency_threshold", 200.0),
        )
        console.print("[bold green]Processing of ping file completed.[/bold green]")
        logging.info("Processing of ping file completed.")
        sys.exit(0)  # Exit after processing file


def validate_and_get_ips(config) -> list:
    """
    Validates the list of IP addresses and returns the validated list.
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


async def run_ping_monitoring(config, results_subfolder, latency_data):
    """
    Initiates ping monitoring with progress bars and real-time graphs.
    """
    duration = config.get("duration", 10800)
    ping_interval = config.get("ping_interval", 1)
    ips = config["ip_addresses"]
    tasks = []

    # Initialize Rich Progress
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )

    # Create tasks for each IP
    task_id_map = {}
    for ip in ips:
        results_file = os.path.join(results_subfolder, f"ping_results_{ip}.txt")
        task_id = progress.add_task(f"Pinging [cyan]{ip}[/cyan]", total=duration)
        task_id_map[ip] = task_id
        task = asyncio.create_task(
            run_ping(
                ip_address=ip,
                duration=duration,
                interval=ping_interval,
                results_file=results_file,
                progress=progress,
                task_id=task_id,
                latency_data=latency_data,
            )
        )
        tasks.append(task)

    # Calculate dynamic graph dimensions
    terminal_width = console.size.width
    terminal_height = console.size.height
    reserved_height = 10  # Reserve some lines for margins and other info
    progress_bar_height = len(ips) * 3  # Approximate progress bar height
    available_height = terminal_height - reserved_height - progress_bar_height
    graph_height = (
        max(5, available_height // len(ips)) if len(ips) > 0 else 5
    )  # Ensure a minimum height

    # Define a sliding window size
    window_size = 50  # Number of recent data points to display

    # Start the Live context
    with Live(console=console, refresh_per_second=4) as live:
        while not all(task.done() for task in tasks):
            # Generate ASCII charts
            charts = []
            for ip in ips:
                data = list(latency_data[ip])[
                    -window_size:
                ]  # Get the most recent data points
                current_max = max(data) if data else 100
                plot_max = max(current_max, 100)  # Ensure plot max is at least 100ms

                # Determine graph width based on number of columns
                if len(ips) == 1:
                    graph_width = (
                        terminal_width - 10
                    )  # Use most of the terminal width for a single IP
                elif len(ips) <= 2:
                    graph_width = (
                        terminal_width // 2
                    ) - 10  # Split the terminal width between two IPs
                else:
                    graph_width = (
                        terminal_width // 3
                    ) - 10  # Adjust as needed for more IPs

                chart = asciichartpy.plot(
                    data,
                    {
                        "height": graph_height,
                        "min": 0,
                        "max": plot_max,
                        "format": "{:>6.1f}",
                        "padding": 1,
                        "width": graph_width,
                    },
                )

                # Determine color based on current max latency
                if current_max < 75:
                    color = "green"
                elif current_max < 100:
                    color = "yellow"
                else:
                    color = "red"

                colored_chart = f"[{color}]{chart}[/{color}]"
                charts.append(
                    Panel(colored_chart, title=f"IP: {ip}", border_style=color)
                )

            # Organize charts into columns
            if len(charts) > 1:
                charts_renderable = Columns(charts, equal=True)
            else:
                charts_renderable = (
                    charts[0]
                    if charts
                    else Panel(
                        "No Data", title="Real-time Latency Graphs", border_style="grey"
                    )
                )

            # Create the legend panel with markup enabled
            legend_text = Text.from_markup(
                "Legend: [green]Green[/green] < 75ms | [yellow]Yellow[/yellow] 75ms-125ms | [red]Red[/red] > 125ms",
                style="bold",
            )
            legend_panel = Panel(legend_text, border_style="none", expand=False)

            # Combine charts and legend
            charts_renderable = Group(charts_renderable, legend_panel)

            # Render the progress bars
            progress_renderable = Panel(
                progress, title="Ping Progress", border_style="blue", expand=False
            )

            # Combine progress and charts into a single renderable
            combined = Group(progress_renderable, charts_renderable)

            # Update the Live display
            live.update(combined)

            await asyncio.sleep(0.5)  # Adjust the sleep time as needed

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)


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

    # Load configuration
    config = load_config()

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
        for ip in args.ip_addresses
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
    asyncio.run(main())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Ping monitoring interrupted by user.[/bold red]")
        logging.warning("Ping monitoring interrupted by user.")
        sys.exit(0)
