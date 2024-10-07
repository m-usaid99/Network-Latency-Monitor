# data_processing.py

"""
Data Processing

Handles the processing of existing ping result files for the Network Latency Monitor (NLM) tool.
This module provides functions to extract ping times from files, aggregate the data, generate
visual plots, and process the results based on user configurations.

Functions:
    - process_file_mode: Processes the ping result file if file mode is enabled.
    - extract_ping_times: Extracts ping times from a given file.
    - aggregate_ping_times: Aggregates ping times over specified intervals.
    - process_ping_results: Processes all ping result files in a subdirectory.
    - process_ping_file: Processes a single ping result file and generates the corresponding plot.
"""

import sys
import matplotlib.pyplot as plt
import pandas as pd
import logging
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from rich.console import Console
from .plot_generator import generate_plots

console = Console()


def process_file_mode(config: Dict):
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
    file_path = config.get("file")
    if file_path:
        file_path_obj = Path(file_path)  # Convert to Path object for path operations
        console.print(
            f"[bold green]Processing ping result file:[/bold green] {file_path_obj}"
        )
        process_ping_file(
            file_path=str(
                file_path_obj
            ),  # Pass as string to maintain original function signature
            config=config,
            no_aggregation=config.get("no_aggregation", False),
            duration=config.get("duration", 10800),
            latency_threshold=config.get("latency_threshold", 200.0),
        )
        console.print("[bold green]Processing of ping file completed.[/bold green]")
        sys.exit(0)  # Exit after processing file


def extract_ping_times(file_path: str) -> List[Optional[float]]:
    """
    Extracts ping times from a given ping result file.

    This function reads a ping result file line by line, parsing each line to extract
    the latency in milliseconds. If a ping attempt resulted in a loss or an error,
    the function records it as `None`. The function also logs any unexpected line formats.

    Args:
        file_path (str): Path to the ping result file.

    Returns:
        List[Optional[float]]: A list of ping times in milliseconds. `None` represents
        lost pings or errors.

    Example:
        >>> ping_times = extract_ping_times("results/ping_results_8.8.8.8.txt")
        >>> print(ping_times)
        [23.5, 24.1, None, 25.0, ...]
    """
    ping_times: List[Optional[float]] = []
    file_path_obj = Path(file_path)

    try:
        with file_path_obj.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line.lower() == "lost":
                    ping_times.append(None)
                else:
                    try:
                        ping_time = float(line)
                        ping_times.append(ping_time)
                    except ValueError:
                        # Handle unexpected line format
                        ping_times.append(None)
                        logging.warning(
                            f"Unexpected line format in {file_path_obj}: {line}"
                        )
    except FileNotFoundError:
        logging.error(f"Ping result file {file_path_obj} not found.")
    except Exception as e:
        logging.error(f"Error extracting ping times from {file_path_obj}: {e}")

    return ping_times


def aggregate_ping_times(
    ping_times: List[Optional[float]], interval: int
) -> List[Tuple[float, float, float]]:
    """
    Aggregates ping times over specified intervals.

    This function groups ping times into intervals and calculates the mean latency
    and packet loss percentage for each interval. If all pings in an interval are lost,
    it logs a warning and sets the mean latency to 0.0 ms.

    Args:
        ping_times (List[Optional[float]]): A list of ping times in milliseconds. `None` represents
            lost pings or errors.
        interval (int): The number of ping attempts to aggregate into a single interval.

    Returns:
        List[Tuple[float, float, float]]: A list of tuples containing:
            - Midpoint time of the interval in seconds.
            - Mean latency in milliseconds.
            - Packet loss percentage.

    Example:
        >>> ping_times = [23.5, 24.1, None, 25.0, 26.2, None]
        >>> aggregated = aggregate_ping_times(ping_times, 3)
        >>> print(aggregated)
        [(1.5, 24.2, 33.33333333333333), (4.5, 25.6, 33.33333333333333)]
    """

    aggregated_data = []
    total_intervals = len(ping_times) // interval

    for i in range(total_intervals):
        start = i * interval
        end = start + interval
        interval_pings = ping_times[start:end]
        successful_pings = [pt for pt in interval_pings if pt is not None]
        lost_pings = len(interval_pings) - len(successful_pings)
        packet_loss = (lost_pings / interval) * 100 if interval > 0 else 0

        if successful_pings:
            mean_latency = sum(successful_pings) / len(successful_pings)
        else:
            mean_latency = 0.0  # Indicate all pings lost

        midpoint_time = start + (interval / 2)
        aggregated_data.append((midpoint_time, mean_latency, packet_loss))

    # Handle remaining pings
    remaining_pings = ping_times[total_intervals * interval :]
    if remaining_pings:
        successful_pings = [pt for pt in remaining_pings if pt is not None]
        lost_pings = len(remaining_pings) - len(successful_pings)
        packet_loss = (
            (lost_pings / len(remaining_pings)) * 100 if len(remaining_pings) > 0 else 0
        )

        if successful_pings:
            mean_latency = sum(successful_pings) / len(successful_pings)
        else:
            mean_latency = 0.0

        midpoint_time = total_intervals * interval + (len(remaining_pings) / 2)
        aggregated_data.append((midpoint_time, mean_latency, packet_loss))

        if lost_pings == len(remaining_pings):
            logging.warning(
                f"All pings lost in remaining interval {total_intervals * interval}-{total_intervals * interval + len(remaining_pings)} seconds. Mean Latency set to 0.0 ms at {midpoint_time}s."
            )

    return aggregated_data


def process_ping_results(
    results_subfolder, config
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Processes all ping result files in a specified subdirectory.

    This function iterates through all ping result files within the provided subdirectory,
    extracts and aggregates ping times, and organizes the data into pandas DataFrames
    for further analysis or plotting.

    Args:
        results_subfolder (str): Path to the directory containing ping result files.
        config (Dict): Configuration dictionary containing settings like duration and aggregation flags.

    Returns:
        Dict[str, Dict[str, pd.DataFrame]]: A nested dictionary where each key is an IP address,
        and its value is another dictionary with 'raw' and 'aggregated' DataFrames.

    Example:
        >>> data = process_ping_results("results/results_2023-10-05_12-00-00", config)
        >>> print(data.keys())
        dict_keys(['8.8.8.8', '1.1.1.1'])
    """
    data_dict = {}
    results_subfolder_path = Path(results_subfolder)

    ip_files = [
        f
        for f in results_subfolder_path.iterdir()
        if f.is_file() and f.name.startswith("ping_results_") and f.suffix == ".txt"
    ]

    for file_path_obj in ip_files:
        file_path = str(
            file_path_obj
        )  # Convert Path object back to string for compatibility
        # Extract IP address from filename
        ip_address = file_path_obj.stem[len("ping_results_") :]
        ping_times = extract_ping_times(file_path)
        if not ping_times:
            console.print(
                f"[bold red]No ping times extracted from {file_path_obj}. Skipping.[/bold red]"
            )
            logging.warning(f"No ping times extracted from {file_path_obj}. Skipping.")
            continue

        # Determine if aggregation should be enforced based on duration
        duration = config.get("duration", 10800)
        if duration < 60:
            console.print(
                f"[bold yellow]Duration ({duration}s) is less than 60 seconds. Aggregation disabled for {ip_address}.[/bold yellow]"
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
        else:
            agg_df = None

        # Convert raw ping times to DataFrame
        raw_df = pd.DataFrame(
            {"Time (s)": range(1, len(ping_times) + 1), "Ping (ms)": ping_times}
        )

        # Store data
        data_dict[ip_address] = {"raw": raw_df, "aggregated": agg_df}

    return data_dict


def process_ping_file(
    file_path: str,
    config: dict,
    no_aggregation: bool,
    duration: int,
    latency_threshold: float,
) -> None:
    """
    Processes a single ping result file and generates the corresponding plot.

    This function reads ping results from a specified file, extracts and aggregates the
    data based on configuration settings, and generates visual plots using matplotlib.
    It also creates a timestamped subdirectory to store the generated plots.

    Args:
        file_path (str): Path to the ping result file.
        config (Dict): Configuration dictionary containing settings like aggregation flags and folders.
        no_aggregation (bool): Flag to disable data aggregation.
        duration (int): Total duration of the ping monitoring in seconds.
        latency_threshold (float): Latency threshold in milliseconds for highlighting high latency regions.

    Raises:
        FileNotFoundError: If the specified ping result file does not exist.
        Exception: For any other errors that occur during processing.
    """
    ip_address = Path(file_path).stem.split("_")[2]  # Extract IP from filename
    ping_times = extract_ping_times(file_path)

    if not ping_times:
        logging.warning(f"No ping times extracted from {file_path}. Skipping plot.")
        return

    # Determine if aggregation should be enforced based on duration
    if duration < 60:
        aggregate = False
    else:
        aggregate = not no_aggregation

    if aggregate:
        aggregated_data = aggregate_ping_times(ping_times, interval=60)
        agg_df = pd.DataFrame(
            aggregated_data,
            columns=["Time (s)", "Mean Latency (ms)", "Packet Loss (%)"],
        )
    else:
        agg_df = None

    # Convert raw ping times to DataFrame
    raw_df = pd.DataFrame(
        {"Time (s)": range(1, len(ping_times) + 1), "Ping (ms)": ping_times}
    )

    # Determine dynamic y-axis limit
    if agg_df is not None and not agg_df.empty:
        overall_max_ping = max(
            raw_df["Ping (ms)"].max(), agg_df["Mean Latency (ms)"].max()
        )
    else:
        overall_max_ping = raw_df["Ping (ms)"].max()

    # Calculate y_max
    if overall_max_ping > 800:
        y_max = 800
    else:
        y_max = overall_max_ping * 1.05  # Add 5% padding

    plt.ylim(0, y_max)

    # Prepare data dictionary
    data_dict = {ip_address: {"raw": raw_df, "aggregated": agg_df}}

    # Create plot subdirectory using pathlib.Path
    plots_folder = Path(config.get("plots_folder", "plots"))
    current_date = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
    plot_subfolder = plots_folder / f"plots_{current_date}"
    try:
        plot_subfolder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create plot subdirectory {plot_subfolder}: {e}")
        console.print(
            f"[bold red]Failed to create plot subdirectory {plot_subfolder}: {e}[/bold red]"
        )
        sys.exit(1)

    # Generate and save the plot
    generate_plots(config, data_dict, latency_threshold)
