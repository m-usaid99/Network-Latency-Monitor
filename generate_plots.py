import argparse
import logging
import os
import re
import sys
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yaml

# Use the Agg backend for matplotlib to improve performance in non-interactive environments
matplotlib.use("Agg")

# Global configuration
FIGSIZE = (25, 15)
AGGREGATION_INTERVAL = 60  # seconds

plt.rcParams.update(
    {
        "font.size": 22,
        "axes.titlesize": 24,
        "axes.labelsize": 22,
        "xtick.labelsize": 20,
        "ytick.labelsize": 20,
        "legend.fontsize": 20,
    }
)


def initialize_logging():
    """
    Sets up logging using the python logging library. Logs are saved into a file in the logs/ directory for each run.
    """
    current_date = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = f"logs/generate_plots_{current_date}.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info("Python script started")


def parse_arguments():
    """
    Parses command line arguments passed from the shell script, and added to the parser object.
    """
    parser = argparse.ArgumentParser(
        description="WiFi Ping Monitor - Generate Plots from Ping Results"
    )
    parser.add_argument(
        "results_files", nargs="+", help="Path to the ping results file(s)"
    )
    parser.add_argument("plots_folder", help="Directory to save the plots")
    parser.add_argument(
        "--no-aggregation", action="store_true", help="Disable data aggregation"
    )
    return parser.parse_args()


def read_config(config_file="config.yaml"):
    """
    Reads a config.yaml file and gets different parameters from there.

    :param config_file string: Path to the config file.
    """
    try:
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        sys.exit(1)


def read_ping_results(file_path):
    """
    Reads a .txt file containing ping results.

    :param file_path string: File path to the .txt file containing results from the ping command.
    """
    logging.info(f"Reading ping results from {file_path}")
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
        if not lines:
            logging.error("Error: Results file is empty.")
            sys.exit(1)
        return lines
    except FileNotFoundError:
        logging.error(f"Results file {file_path} not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading results file: {e}")
        sys.exit(1)


def extract_ping_data(lines):
    """
    Parses a line from the text file, and obtains relevant ping data.

    :param lines string: Each line from the ping results text file.
    """
    ping_times = []
    packet_loss = 0

    try:
        for line in lines:
            match = re.search(r"time=(\d+\.?\d*) ms", line)
            if match:
                ping_times.append(float(match.group(1)))

            loss_match = re.search(r"(\d+)% packet loss", line)
            if loss_match:
                packet_loss = int(loss_match.group(1))

        logging.info(f"Extracted {len(ping_times)} ping times from the results file")
        logging.info(f"Packet loss: {packet_loss}%")
    except Exception as e:
        logging.error(f"Error processing data: {e}")
        sys.exit(1)

    return ping_times, packet_loss


def aggregate_data(ping_times, interval) -> list:
    """
    Computes aggregate (mean) ping data over a specified time interval.

    :param ping_times list: A list containing all processed ping data for an IP address.
    :param interval int: The time interval over which aggregation takes place.
    """
    aggregated_data = []
    num_intervals = len(ping_times) // interval

    for i in range(num_intervals):
        chunk = ping_times[i * interval : (i + 1) * interval]
        aggregated_data.append(sum(chunk) / len(chunk))

    remaining_chunk = ping_times[num_intervals * interval :]
    if remaining_chunk:
        aggregated_data.append(sum(remaining_chunk) / len(remaining_chunk))

    return aggregated_data


def create_plots(
    ping_data_dict, interval, plots_folder, aggregation_interval, no_aggregation
):
    """
    Uses ping data lists to create plots and save them to a dedicated plot directory.

    :param ping_data_dict dict: A dictionary containing raw data for each ip address.
    :param interval int: The time interval between each ping attempt.
    :param plots_folder string: The directory where the plots subdirectory is going to be created.
    :param aggregation_interval int: The interval over which data aggregation has to take place.
    :param no_aggregation boolean: A flag to disable aggregation (enabled by default).
    """
    sns.set_theme(style="darkgrid")
    try:
        current_date = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        plot_subfolder = os.path.join(plots_folder, f"plots_{current_date}")
        os.makedirs(plot_subfolder, exist_ok=True)

        samples_per_hour = 3600 // interval
        color_palette = sns.color_palette("muted", len(ping_data_dict))
        colors = {ip: color_palette.pop(0) for ip in ping_data_dict}

        for hour in range(
            0, max(len(times) for times in ping_data_dict.values()), samples_per_hour
        ):
            plt.figure(figsize=FIGSIZE)
            for ip, ping_times in ping_data_dict.items():
                color = colors[ip]
                start_idx = hour
                end_idx = hour + samples_per_hour
                time_stamps = [
                    i * interval
                    for i in range(start_idx, min(end_idx, len(ping_times)))
                ]

                df_hourly = pd.DataFrame(
                    {
                        "Time (s)": time_stamps,
                        "Ping (ms)": ping_times[start_idx:end_idx],
                    }
                )
                sns.lineplot(
                    x="Time (s)",
                    y="Ping (ms)",
                    data=df_hourly,
                    label=f"Raw Data ({ip})",
                    color=color,
                )

                if not no_aggregation and len(ping_times) > 60:
                    aggregated_data = aggregate_data(
                        ping_times[start_idx:end_idx], aggregation_interval
                    )
                    agg_time_stamps = [
                        (i * aggregation_interval)
                        + (aggregation_interval // 2)
                        + start_idx
                        for i in range(len(aggregated_data))
                    ]
                    df_agg = pd.DataFrame(
                        {
                            "Time (s)": agg_time_stamps,
                            "Ping (ms)": aggregated_data,
                        }
                    )
                    sns.lineplot(
                        x="Time (s)",
                        y="Ping (ms)",
                        data=df_agg,
                        label=f"Aggregated Data ({ip})",
                        linestyle="dotted",
                        marker="o",
                        color=color,
                    )

            plt.title(
                f"WiFi Network Ping Over Time ({hour // 3600 + 1} Hour{'s' if hour // 3600 + 1 > 1 else ''}, Max Value Capped at 600 ms)"
            )
            plt.xlabel("Time (seconds)")
            plt.ylabel("Ping (ms)")
            plt.legend()
            plt.xticks(
                range(
                    start_idx,
                    min(end_idx, len(ping_times)),
                    max(1, samples_per_hour // 10),
                )
            )
            plot_path = os.path.join(
                plot_subfolder, f"wifi_ping_plot_hour_{hour // 3600 + 1}.png"
            )
            plt.savefig(plot_path)
            plt.close()
            logging.info(f"Generated plot for Hour {hour // 3600 + 1}: {plot_path}")

    except Exception as e:
        logging.error(f"Error generating plots: {e}")
        sys.exit(1)


def main():
    initialize_logging()
    args = parse_arguments()
    config = read_config()

    logging.info(
        f"Arguments received: results_files={args.results_files}, plots_folder={args.plots_folder}, no_aggregation={args.no_aggregation}"
    )

    global FIGSIZE, AGGREGATION_INTERVAL
    FIGSIZE = tuple(config["plot"]["figure_size"])
    AGGREGATION_INTERVAL = config["aggregation"]["interval"]

    ping_data_dict = {}
    for results_file in args.results_files:
        lines = read_ping_results(results_file)
        ping_times, packet_loss = extract_ping_data(lines)
        ip = Path(results_file).stem.split("_")[2]
        ping_data_dict[ip] = ping_times

    create_plots(
        ping_data_dict,
        config["ping_interval"],
        args.plots_folder,
        AGGREGATION_INTERVAL,
        args.no_aggregation,
    )

    for ip, ping_times in ping_data_dict.items():
        logging.info(f"Total Packet Loss for {ip}: {ping_times.count(0)}%")
        print(f"Total Packet Loss for {ip}: {ping_times.count(0)}%")

    logging.info("Python script completed")


if __name__ == "__main__":
    main()
