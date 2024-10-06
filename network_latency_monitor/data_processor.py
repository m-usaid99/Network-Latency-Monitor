import sys
import matplotlib.pyplot as plt
import pandas as pd
import os
import logging
from typing import List, Tuple, Optional
from rich.console import Console
from .plot_generator import generate_plots

console = Console()


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


def extract_ping_times(file_path: str) -> List[Optional[float]]:
    """
    Extracts ping times from a ping result file, caps them at 800 ms,
    and returns a list of ping times where lost pings are represented as None.

    :param file_path: Path to the ping result file.
    :return: List of ping times with None for lost pings.
    """
    ping_times: List[Optional[float]] = []

    try:
        with open(file_path, "r") as file:
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
                            f"Unexpected line format in {file_path}: {line}"
                        )
        logging.info(f"Extracted {len(ping_times)} ping attempts from {file_path}")
    except FileNotFoundError:
        logging.error(f"Ping result file {file_path} not found.")
    except Exception as e:
        logging.error(f"Error extracting ping times from {file_path}: {e}")

    return ping_times


def aggregate_ping_times(
    ping_times: List[Optional[float]], interval: int
) -> List[Tuple[float, float, float]]:
    """
    Aggregates ping times over specified intervals and assigns aggregate points at the midpoint of each interval.

    :param ping_times: List of ping times where None represents a lost ping.
    :param interval: Interval in seconds to aggregate pings.
    :return: List of tuples containing (Midpoint Time Interval, Mean Latency, Packet Loss Percentage)
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

        if lost_pings == interval:
            logging.warning(
                f"All pings lost in interval {start}-{end} seconds. Mean Latency set to 0.0 ms at {midpoint_time}s."
            )
        else:
            logging.debug(
                f"Interval {start}-{end}s: Mean Latency = {mean_latency} ms, Packet Loss = {packet_loss}% at {midpoint_time}s"
            )

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
        else:
            logging.debug(
                f"Remaining Interval {total_intervals * interval}-{total_intervals * interval + len(remaining_pings)}s: Mean Latency = {mean_latency} ms, Packet Loss = {packet_loss}% at {midpoint_time}s"
            )

    return aggregated_data


def process_ping_file(
    file_path: str,
    config: dict,
    no_aggregation: bool,
    duration: int,
    latency_threshold: float,
) -> None:
    """
    Processes a single ping result file and generates the corresponding plot.

    :param file_path: Path to the ping result file.
    :param config: Configuration dictionary.
    :param no_aggregation: Boolean flag to disable aggregation.
    :param duration: Total duration of the ping monitoring in seconds.
    """
    ip_address = os.path.basename(file_path).split("_")[2]  # Extract IP from filename
    ping_times = extract_ping_times(file_path)

    if not ping_times:
        logging.warning(f"No ping times extracted from {file_path}. Skipping plot.")
        return

    # Determine if aggregation should be enforced based on duration
    if duration < 60:
        logging.info(
            f"Duration ({duration}s) is less than 60 seconds. Aggregation disabled for {ip_address}."
        )
        aggregate = False
    else:
        aggregate = not no_aggregation

    if aggregate:
        aggregated_data = aggregate_ping_times(ping_times, interval=60)
        agg_df = pd.DataFrame(
            aggregated_data, columns=["Time (s)", "Mean Latency (ms)"]
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

    # Create plot subdirectory
    plots_folder = config.get("plots_folder", "plots")
    current_date = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
    plot_subfolder = os.path.join(plots_folder, f"plots_{current_date}")
    os.makedirs(plot_subfolder, exist_ok=True)
    logging.info(f"Created plot subdirectory: {plot_subfolder}")

    # Generate and save the plot
    generate_plots(config, data_dict, latency_threshold)
