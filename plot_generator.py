# plot_generator.py

import logging
import os
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from datetime import datetime
import seaborn as sns
import pandas as pd
from typing import List, Tuple, Dict, Optional
from rich.table import Table
from rich.console import Console

console = Console()


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
                        if ping_time > 800.0:
                            ping_time = 800.0
                            logging.warning(
                                f"Capped ping time at 800 ms in file {file_path}"
                            )
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


def display_summary(data_dict: dict) -> None:
    """
    Displays summary statistics for each IP address using Rich's Table.

    :param data_dict: Dictionary containing ping data for each IP.
    """
    console = Console()
    table = Table(title="Ping Summary Statistics")

    table.add_column("IP Address", style="cyan", no_wrap=True)
    table.add_column("Total Pings", style="magenta")
    table.add_column("Successful Pings", style="green")
    table.add_column("Packet Loss (%)", style="red")
    table.add_column("Average Latency (ms)", style="yellow")
    table.add_column("Min Latency (ms)", style="blue")
    table.add_column("Max Latency (ms)", style="blue")

    for ip, data in data_dict.items():
        ping_series = data["raw"]["Ping (ms)"]

        total_pings = ping_series.size
        successful_pings = ping_series.count()
        lost_pings = total_pings - successful_pings
        packet_loss = (lost_pings / total_pings) * 100 if total_pings > 0 else 0

        if successful_pings > 0:
            average_latency = ping_series.mean()
            min_latency = ping_series.min()
            max_latency = ping_series.max()
        else:
            average_latency = "N/A"
            min_latency = "N/A"
            max_latency = "N/A"

        # Format latency values
        average_latency_display = (
            f"{average_latency:.2f}" if average_latency != "N/A" else "N/A"
        )
        min_latency_display = f"{min_latency:.2f}" if min_latency != "N/A" else "N/A"
        max_latency_display = f"{max_latency:.2f}" if max_latency != "N/A" else "N/A"

        table.add_row(
            ip,
            str(total_pings),
            str(successful_pings),
            f"{packet_loss:.2f}%",
            average_latency_display,
            min_latency_display,
            max_latency_display,
        )

    console.print(table)


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


def generate_plots(
    config: Dict[str, str],
    data_dict: Dict[str, Dict[str, Optional[pd.DataFrame]]],
    latency_threshold: float,
) -> None:
    """
    Generates and saves a consolidated latency plot for all IP addresses,
    highlighting regions where latency exceeds the specified threshold.
    The plot is saved inside a timestamped subdirectory within the designated plots folder.

    :param config: Configuration dictionary containing paths and settings.
    :param data_dict: Dictionary containing raw and aggregated ping data for each IP address.
    :param latency_threshold: Latency threshold in milliseconds for highlighting high latency regions.
    """
    # Retrieve the base plots folder from the configuration
    plots_folder = config.get("plots_folder", "plots")

    # Generate a timestamp for the subdirectory name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Create a timestamped subdirectory within the plots folder
    plots_subfolder = os.path.join(plots_folder, f"plots_{timestamp}")
    os.makedirs(plots_subfolder, exist_ok=True)
    logging.info(f"Created plots subdirectory: {plots_subfolder}")

    plt.figure(figsize=(14, 8))

    # Define a color palette with as many colors as IPs
    palette = sns.color_palette("deep", n_colors=len(data_dict))

    # List to collect all high latency times across IPs
    high_latency_times = []

    for idx, (ip, data) in enumerate(data_dict.items()):
        raw_df = data["raw"]
        agg_df = data["aggregated"]
        color = palette[idx % len(palette)]

        # Plot Raw Ping with low opacity
        sns.lineplot(
            x="Time (s)",
            y="Ping (ms)",
            data=raw_df,
            label=f"{ip} Raw Ping",
            color=color,
            alpha=0.5,
        )

        if agg_df is not None:
            # Plot Mean Latency
            sns.lineplot(
                x="Time (s)",
                y="Mean Latency (ms)",
                data=agg_df,
                label=f"{ip} Mean Latency",
                linestyle="--",
                marker="o",
                color=color,
            )

            # Identify High Latency Points
            high_latency = agg_df[agg_df["Mean Latency (ms)"] > latency_threshold]
            if not high_latency.empty:
                # Scatter plot for High Latency Points
                sns.scatterplot(
                    x="Time (s)",
                    y="Mean Latency (ms)",
                    data=high_latency,
                    label=f"{ip} High Latency",
                    color=color,
                    marker="D",
                    s=100,
                )
                # Annotate High Latency Points
                for _, row in high_latency.iterrows():
                    plt.annotate(
                        f"{row['Mean Latency (ms)']} ms",
                        (row["Time (s)"], row["Mean Latency (ms)"]),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha="center",
                        fontsize=8,
                        color=color,
                    )
                # Collect high latency times for shading
                high_latency_times.extend(high_latency["Time (s)"].tolist())

    # Consolidate high latency times into shading regions
    shading_regions = []
    if high_latency_times:
        # Sort and remove duplicates
        sorted_times = sorted(set(high_latency_times))
        # Initialize the first shading region
        start = sorted_times[0]
        end = sorted_times[0]

        for time in sorted_times[1:]:
            if time == end + 1:
                end = time
            else:
                shading_regions.append((start, end))
                start = time
                end = time
        # Append the last shading region
        shading_regions.append((start, end))

        # Shade each high latency region
        for region in shading_regions:
            plt.axvspan(
                region[0] - 0.5,  # Slight padding on the left
                region[1] + 0.5,  # Slight padding on the right
                color="red",
                alpha=0.1,
                label="High Latency" if region == shading_regions[0] else "",
            )

    # Customize Legend to avoid duplicate labels
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(
        by_label.values(), by_label.keys(), loc="upper left", bbox_to_anchor=(1.05, 1)
    )

    plt.title("Ping Monitoring")
    plt.xlabel("Time (s)")
    plt.ylabel("Latency (ms)")
    plt.grid(True)
    plt.tight_layout()

    # Define the plot filename with date and time
    plot_filename = f"ping_plot_{timestamp}.png"
    plot_path = os.path.join(plots_subfolder, plot_filename)

    # Save the plot
    plt.savefig(plot_path)
    plt.close()
    logging.info(f"Generated consolidated plot: {plot_path}")

    # Notify the user
    console.print(f"[bold green]Generated consolidated plot:[/bold green] {plot_path}")


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
