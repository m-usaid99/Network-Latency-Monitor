import argparse
import logging
import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yaml

# Use the Agg backend for matplotlib to improve performance in non-interactive environments
matplotlib.use("Agg")


@dataclass
class Config:
    figsize: Tuple[int, int] = (25, 15)
    aggregation_interval: int = 60  # seconds
    plot_dpi: int = 100
    plot_theme: str = "darkgrid"
    plot_font_sizes: Dict[str, int] = field(
        default_factory=lambda: {"title": 24, "label": 22, "tick": 20, "legend": 20}
    )
    aggregation_method: str = "mean"
    segmentation_hourly: bool = True
    results_folder: str = "results"
    plots_folder: str = "plots"
    log_folder: str = "logs"


class PingPlotGenerator:
    def __init__(self, config: Config, no_aggregation: bool = False):
        self.config = config
        self.no_aggregation = no_aggregation
        self.setup_logging()

    def setup_logging(self):
        """
        Sets up logging to file and console.
        """
        os.makedirs(self.config.log_folder, exist_ok=True)
        current_date = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = Path(self.config.log_folder) / f"generate_plots_{current_date}.log"

        # Create logger
        self.logger = logging.getLogger("PingPlotGenerator")
        self.logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

        self.logger.info("PingPlotGenerator initialized.")

    def read_config(self, config_file: str = "config.yaml") -> Config:
        """
        Reads configuration from a YAML file.

        :param config_file: Path to the configuration file.
        :return: Config object with settings.
        """
        try:
            with open(config_file, "r") as file:
                cfg = yaml.safe_load(file)
            config = Config(
                figsize=tuple(
                    cfg.get("plot", {}).get("figure_size", self.config.figsize)
                ),
                aggregation_interval=cfg.get("aggregation", {}).get(
                    "interval", self.config.aggregation_interval
                ),
                plot_dpi=cfg.get("plot", {}).get("dpi", self.config.plot_dpi),
                plot_theme=cfg.get("plot", {}).get("theme", self.config.plot_theme),
                plot_font_sizes={
                    "title": cfg.get("plot", {})
                    .get("font", {})
                    .get("title_size", self.config.plot_font_sizes["title"]),
                    "label": cfg.get("plot", {})
                    .get("font", {})
                    .get("label_size", self.config.plot_font_sizes["label"]),
                    "tick": cfg.get("plot", {})
                    .get("font", {})
                    .get("tick_size", self.config.plot_font_sizes["tick"]),
                    "legend": cfg.get("plot", {})
                    .get("font", {})
                    .get("legend_size", self.config.plot_font_sizes["legend"]),
                },
                aggregation_method=cfg.get("aggregation", {}).get(
                    "method", self.config.aggregation_method
                ),
                segmentation_hourly=cfg.get("segmentation", {}).get(
                    "hourly", self.config.segmentation_hourly
                ),
                results_folder=cfg.get("results_folder", self.config.results_folder),
                plots_folder=cfg.get("plots_folder", self.config.plots_folder),
                log_folder=cfg.get("log_folder", self.config.log_folder),
            )
            self.logger.info(f"Configuration loaded from {config_file}.")
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file {config_file} not found.")
            sys.exit(1)
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)

    def parse_arguments(self) -> argparse.Namespace:
        """
        Parses command-line arguments.

        :return: Parsed arguments namespace.
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

    def read_ping_results(self, file_path: str) -> List[str]:
        """
        Reads a .txt file containing ping results.

        :param file_path: Path to the .txt file containing results from the ping command.
        :return: List of lines from the file.
        """
        self.logger.info(f"Reading ping results from {file_path}")
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
            if not lines:
                self.logger.error(f"Results file {file_path} is empty.")
                sys.exit(1)
            return lines
        except FileNotFoundError:
            self.logger.error(f"Results file {file_path} not found.")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Error reading results file {file_path}: {e}")
            sys.exit(1)

    def extract_ping_data(self, lines: List[str]) -> Tuple[List[float], int]:
        """
        Parses lines from the ping results to extract ping times and packet loss.

        :param lines: List of lines from the ping results file.
        :return: Tuple containing list of ping times and packet loss percentage.
        """
        ping_times = []
        packet_loss = 0

        try:
            for line in lines:
                time_match = re.search(r"time=(\d+\.?\d*) ms", line)
                if time_match:
                    ping_times.append(float(time_match.group(1)))

                loss_match = re.search(r"(\d+)% packet loss", line)
                if loss_match:
                    packet_loss = int(loss_match.group(1))

            self.logger.info(f"Extracted {len(ping_times)} ping times.")
            self.logger.info(f"Packet loss: {packet_loss}%")
        except Exception as e:
            self.logger.error(f"Error processing ping data: {e}")
            sys.exit(1)

        return ping_times, packet_loss

    def aggregate_data(self, ping_times: List[float]) -> List[float]:
        """
        Aggregates ping times using the specified method over the aggregation interval.

        :param ping_times: List of ping times.
        :return: Aggregated ping times.
        """
        if self.config.aggregation_method == "mean":
            aggregation_func = pd.Series.mean
        elif self.config.aggregation_method == "median":
            aggregation_func = pd.Series.median
        elif self.config.aggregation_method == "min":
            aggregation_func = pd.Series.min
        elif self.config.aggregation_method == "max":
            aggregation_func = pd.Series.max
        else:
            self.logger.warning(
                f"Unknown aggregation method '{self.config.aggregation_method}'. Using mean."
            )
            aggregation_func = pd.Series.mean

        try:
            series = pd.Series(ping_times)
            aggregated = (
                series.resample(f"{self.config.aggregation_interval}S", origin="start")
                .apply(aggregation_func)
                .tolist()
            )
            self.logger.info(f"Aggregated data using {self.config.aggregation_method}.")
            return aggregated
        except Exception as e:
            self.logger.error(f"Error during data aggregation: {e}")
            sys.exit(1)

    def create_plots(
        self,
        ping_data_dict: Dict[str, List[float]],
        interval: int,
        plots_folder: str,
    ):
        """
        Generates and saves plots based on the ping data.

        :param ping_data_dict: Dictionary with IP addresses as keys and list of ping times as values.
        :param interval: Interval between each ping in seconds.
        :param plots_folder: Directory to save the plots.
        """
        sns.set_theme(style=self.config.plot_theme)
        plt.rcParams.update(
            {
                "font.size": self.config.plot_font_sizes["label"],
                "axes.titlesize": self.config.plot_font_sizes["title"],
                "axes.labelsize": self.config.plot_font_sizes["label"],
                "xtick.labelsize": self.config.plot_font_sizes["tick"],
                "ytick.labelsize": self.config.plot_font_sizes["tick"],
                "legend.fontsize": self.config.plot_font_sizes["legend"],
            }
        )

        try:
            current_date = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
            plot_subfolder = Path(plots_folder) / f"plots_{current_date}"
            plot_subfolder.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Plots will be saved to {plot_subfolder}")

            samples_per_aggregation = self.config.aggregation_interval // interval
            color_palette = sns.color_palette("muted", len(ping_data_dict))
            colors = {
                ip: color_palette[i] for i, ip in enumerate(ping_data_dict.keys())
            }

            for ip, ping_times in ping_data_dict.items():
                self.logger.info(f"Generating plot for IP: {ip}")
                time_stamps = [i * interval for i in range(len(ping_times))]

                df = pd.DataFrame({"Time (s)": time_stamps, "Ping (ms)": ping_times})

                plt.figure(figsize=self.config.figsize)
                sns.lineplot(
                    x="Time (s)",
                    y="Ping (ms)",
                    data=df,
                    label="Raw Data",
                    color=colors[ip],
                )

                if (
                    not self.no_aggregation
                    and len(ping_times) >= self.config.aggregation_interval
                ):
                    df["Time"] = pd.to_datetime(df["Time (s)"], unit="s")
                    df.set_index("Time (s)", inplace=True)
                    df_agg = (
                        df.resample(f"{self.config.aggregation_interval}S")
                        .agg({"Ping (ms)": self.config.aggregation_method})
                        .reset_index()
                    )
                    sns.lineplot(
                        x="Time (s)",
                        y="Ping (ms)",
                        data=df_agg,
                        label=f"Aggregated ({self.config.aggregation_method})",
                        linestyle="--",
                        marker="o",
                        color=colors[ip],
                    )

                plt.title(f"WiFi Network Ping Over Time - {ip}")
                plt.xlabel("Time (seconds)")
                plt.ylabel("Ping (ms)")
                plt.legend()
                plt.tight_layout()

                plot_path = plot_subfolder / f"wifi_ping_plot_{ip}.png"
                plt.savefig(plot_path, dpi=self.config.plot_dpi)
                plt.close()
                self.logger.info(f"Plot saved: {plot_path}")

        except Exception as e:
            self.logger.error(f"Error generating plots: {e}")
            sys.exit(1)

    def report_packet_loss(self, ping_data_dict: Dict[str, List[float]]):
        """
        Logs and prints the total packet loss for each IP address.

        :param ping_data_dict: Dictionary with IP addresses as keys and list of ping times as values.
        """
        for ip, ping_times in ping_data_dict.items():
            # Assuming that a ping time of 0 indicates packet loss
            lost_packets = ping_times.count(0)
            total_pings = len(ping_times)
            packet_loss_percent = (
                (lost_packets / total_pings) * 100 if total_pings > 0 else 0
            )
            self.logger.info(f"Total Packet Loss for {ip}: {packet_loss_percent:.2f}%")
            print(f"Total Packet Loss for {ip}: {packet_loss_percent:.2f}%")

    def run(self):
        """
        Main execution method.
        """
        args = self.parse_arguments()
        self.no_aggregation = args.no_aggregation or self.no_aggregation

        # Update plots_folder from arguments
        self.config.plots_folder = args.plots_folder

        # Read configuration
        config = self.read_config()

        # Override aggregation setting if command-line flag is set
        self.no_aggregation = args.no_aggregation or self.no_aggregation

        self.logger.info(
            f"Arguments received: results_files={args.results_files}, "
            f"plots_folder={args.plots_folder}, no_aggregation={self.no_aggregation}"
        )

        ping_data_dict = {}
        for results_file in args.results_files:
            lines = self.read_ping_results(results_file)
            ping_times, packet_loss = self.extract_ping_data(lines)
            ip = Path(results_file).stem.split("_")[2]
            ping_data_dict[ip] = ping_times

        self.create_plots(
            ping_data_dict,
            config.aggregation_interval,
            self.config.plots_folder,
        )

        self.report_packet_loss(ping_data_dict)
        self.logger.info("PingPlotGenerator completed successfully.")


def main():
    # Initialize default config
    default_config = Config()
    # Initialize generator with default config
    generator = PingPlotGenerator(config=default_config)
    generator.run()


if __name__ == "__main__":
    main()

