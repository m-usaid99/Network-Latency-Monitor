# plot_generator.py

import re
import logging
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Tuple, Dict, Optional


def extract_ping_times(file_path: str) -> List[float]:
    """
    Extracts ping times from a ping result file, caps them at 800 ms,
    and returns a list of ping times.

    :param file_path: Path to the ping result file.
    :return: List of capped ping times.
    """
    ping_times = []
    pattern = re.compile(r"time=(\d+\.?\d*) ms")

    try:
        with open(file_path, "r") as file:
            for line in file:
                match = pattern.search(line)
                if match:
                    ping_time = float(match.group(1))
                    if ping_time > 800.0:
                        ping_time = 800.0
                        logging.warning(
                            f"Capped ping time at 800 ms in file {file_path}"
                        )
                    ping_times.append(ping_time)
        logging.info(f"Extracted {len(ping_times)} ping times from {file_path}")
    except FileNotFoundError:
        logging.error(f"Ping result file {file_path} not found.")
    except Exception as e:
        logging.error(f"Error extracting ping times from {file_path}: {e}")

    return ping_times


def aggregate_ping_times(
    ping_times: List[float], interval: int = 60
) -> List[Tuple[float, float]]:
    """
    Aggregates ping times into mean latencies per specified interval.

    :param ping_times: List of capped ping times.
    :param interval: Aggregation interval in seconds (default: 60).
    :return: List of tuples (timestamp, mean_latency).
    """
    aggregated_data: List[Tuple[float, float]] = []
    total_pings = len(ping_times)
    num_full_intervals = total_pings // interval

    for i in range(num_full_intervals):
        start_idx = i * interval
        end_idx = start_idx + interval
        interval_pings = ping_times[start_idx:end_idx]
        mean_latency = sum(interval_pings) / len(interval_pings)
        # Timestamp at the center of the interval
        timestamp = (start_idx + end_idx) / 2
        aggregated_data.append((timestamp, mean_latency))

    # Handle remaining pings that don't form a full interval
    remaining_pings = ping_times[num_full_intervals * interval :]
    if remaining_pings:
        mean_latency = sum(remaining_pings) / len(remaining_pings)
        # Timestamp at the center of the remaining interval
        timestamp = num_full_intervals * interval + len(remaining_pings) / 2
        aggregated_data.append((timestamp, mean_latency))

    logging.info(f"Aggregated ping times into {len(aggregated_data)} intervals.")

    return aggregated_data


def generate_plots(
    config: dict, data_dict: Dict[str, Dict[str, Optional[pd.DataFrame]]]
) -> None:
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
    # Extract IP from filename
    base_name = os.path.basename(file_path)
    parts = base_name.split("_")
    if len(parts) < 3:
        logging.error(
            f"Filename {base_name} does not conform to expected format. Skipping."
        )
        return
    ip_address = parts[2].split(".")[0]  # Extract IP from filename

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

    # Generate and save the plot
    generate_plots(config=config, data_dict=data_dict)

