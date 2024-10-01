# plot_generator.py

import re
import logging
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Tuple, Dict, Optional
from rich.table import Table
from rich.console import Console


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
        ping_times = data["raw"]["Ping (ms)"].tolist()
        total_pings = len(ping_times)
        successful_pings = len([pt for pt in ping_times if pt is not None])
        lost_pings = total_pings - successful_pings
        packet_loss = (lost_pings / total_pings) * 100 if total_pings > 0 else 0
        average_latency = (
            sum(pt for pt in ping_times if pt is not None) / successful_pings
            if successful_pings > 0
            else 0
        )
        min_latency = (
            min(pt for pt in ping_times if pt is not None)
            if successful_pings > 0
            else 0
        )
        max_latency = (
            max(pt for pt in ping_times if pt is not None)
            if successful_pings > 0
            else 0
        )

        table.add_row(
            ip,
            str(total_pings),
            str(successful_pings),
            f"{packet_loss:.2f}%",
            f"{average_latency:.2f}",
            str(min_latency),
            str(max_latency),
        )

    console.print(table)


def aggregate_ping_times(
    ping_times: List[Optional[float]], interval: int
) -> List[Tuple[int, float]]:
    """
    Aggregates ping times over specified intervals.

    :param ping_times: List of ping times where None represents a lost ping.
    :param interval: Interval in seconds to aggregate pings.
    :return: List of tuples containing (Time Interval, Mean Latency)
    """
    aggregated_data = []
    total_intervals = len(ping_times) // interval

    for i in range(total_intervals):
        start = i * interval
        end = start + interval
        interval_pings = ping_times[start:end]
        # Filter out None values
        successful_pings = [pt for pt in interval_pings if pt is not None]
        if successful_pings:
            mean_latency = sum(successful_pings) / len(successful_pings)
            aggregated_data.append((i * interval, mean_latency))
        else:
            # If all pings in the interval were lost, you can decide how to handle it
            aggregated_data.append(
                (i * interval, 0.0)
            )  # Assuming 0 latency for all lost pings
            logging.warning(
                f"All pings lost in interval {i * interval} to {end} seconds."
            )

    return aggregated_data


def generate_plots(config: dict, data_dict: Dict[str, Dict[str, pd.DataFrame]]) -> None:
    """
    Generates and saves the plot based on the provided data.

    :param config: Configuration dictionary.
    :param data_dict: Dictionary containing raw and aggregated data for each IP.
    """
    plots_folder = config.get("plots_folder", "plots")
    os.makedirs(plots_folder, exist_ok=True)

    # Create a timestamped subdirectory for plots
    current_date = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
    plot_subfolder = os.path.join(plots_folder, f"plots_{current_date}")
    os.makedirs(plot_subfolder, exist_ok=True)
    logging.info(f"Created plot subdirectory: {plot_subfolder}")

    # Set Seaborn theme
    sns.set_theme(style=config["plot"].get("theme", "darkgrid"))

    # Initialize color palette based on number of IPs
    num_ips = len(data_dict)
    if num_ips == 0:
        logging.warning("No data available for plotting.")
        return

    colors = sns.color_palette("husl", n_colors=num_ips)
    ip_color_map = {ip: colors[idx] for idx, ip in enumerate(data_dict.keys())}

    # Determine overall max ping
    overall_max_ping = 0
    for ip, data in data_dict.items():
        raw_max = data["raw"]["Ping (ms)"].max()
        overall_max_ping = max(overall_max_ping, raw_max)
        if data["aggregated"] is not None:
            agg_max = data["aggregated"]["Mean Latency (ms)"].max()
            overall_max_ping = max(overall_max_ping, agg_max)

    # Calculate dynamic y-axis limit
    if overall_max_ping > 800:
        y_max = 800
    else:
        y_max = overall_max_ping * 1.05  # Add 5% padding

    # Create the plot
    plt.figure(figsize=tuple(config["plot"].get("figure_size", [20, 15])))

    for ip, data in data_dict.items():
        color = ip_color_map[ip]
        # Plot raw data
        sns.lineplot(
            data=data["raw"],
            x="Time (s)",
            y="Ping (ms)",
            label=f"Raw Data ({ip})",
            color=color,
            linewidth=1.5,
        )

        # Plot aggregated data if available
        if data["aggregated"] is not None:
            sns.lineplot(
                data=data["aggregated"],
                x="Time (s)",
                y="Mean Latency (ms)",
                label=f"Mean Latency (per minute) ({ip})",
                linestyle="dotted",
                marker="o",
                color=color,
                linewidth=1.5,
            )

    # Customize plot
    plt.title(
        f"WiFi Network Ping Over Time",
        fontsize=config["plot"]["font"].get("title_size", 24),
    )
    plt.xlabel("Time (seconds)", fontsize=config["plot"]["font"].get("label_size", 22))
    plt.ylabel("Ping (ms)", fontsize=config["plot"]["font"].get("label_size", 22))
    plt.legend(fontsize=config["plot"]["font"].get("legend_size", 20))
    plt.ylim(0, y_max)  # Dynamic y-axis limit

    # Customize tick parameters
    plt.xticks(fontsize=config["plot"]["font"].get("tick_size", 20))
    plt.yticks(fontsize=config["plot"]["font"].get("tick_size", 20))

    # Adjust layout for better spacing
    plt.tight_layout()

    # Save the plot
    plot_filename = f"wifi_ping_plot_{current_date}.png"
    plot_path = os.path.join(plot_subfolder, plot_filename)
    plt.savefig(plot_path, dpi=config["plot"].get("dpi", 100))
    plt.close()
    logging.info(f"Generated plot: {plot_path}")


def process_ping_file(
    file_path: str, config: dict, no_aggregation: bool, duration: int
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
    generate_plots(config, data_dict)
