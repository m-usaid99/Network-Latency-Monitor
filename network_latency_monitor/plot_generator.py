# plot_generator.py

"""
Plot Generator

Handles the creation of visual plots and summary statistics based on ping results
for the Network Latency Monitor (NLM) tool. This module provides functions to
display summary tables, generate latency plots with optional segmentation, and
combine both functionalities to present comprehensive results to the user.

Functions:
    - display_summary: Displays summary statistics in a formatted table.
    - generate_plots: Generates latency plots based on configuration and data.
    - display_plots_and_summary: Generates plots and displays summary statistics.
"""

import logging
import os
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
import seaborn as sns
import pandas as pd
from typing import Dict, Optional
from rich.table import Table
from rich.console import Console

console = Console()


def display_summary(data_dict: dict) -> None:
    """
    Displays summary statistics for each IP address in a formatted table.

    This function creates a Rich table that summarizes key metrics such as total pings,
    successful pings, packet loss percentage, and latency statistics (average, min, max)
    for each monitored IP address.

    Args:
        data_dict (Dict[str, Dict[str, pd.DataFrame]]): A nested dictionary where each key is
            an IP address, and its value is another dictionary containing 'raw' and 'aggregated'
            pandas DataFrames with ping data.

    Example:
        >>> data = {
        ...     '8.8.8.8': {
        ...         'raw': pd.DataFrame({'Ping (ms)': [23.5, 24.1, None, 25.0]}),
        ...         'aggregated': pd.DataFrame({'Mean Latency (ms)': [24.2], 'Packet Loss (%)': [25.0]})
        ...     }
        ... }
        >>> display_summary(data)
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


def generate_plots(
    config: Dict[str, str],
    data_dict: Dict[str, Dict[str, Optional[pd.DataFrame]]],
    latency_threshold: float,
    no_segmentation: bool = False,
) -> None:
    """
    Generates latency plots based on the provided configuration and data.

    This function creates latency plots for each IP address, optionally segmented into
    hourly intervals. It highlights high latency regions based on the specified threshold
    and saves the generated plots in a timestamped subdirectory within the plots folder.

    Args:
        config (Dict[str, str]): Configuration dictionary containing settings like
            plots folder path and segmentation preferences.
        data_dict (Dict[str, Dict[str, Optional[pd.DataFrame]]]): A nested dictionary where each key
            is an IP address, and its value is another dictionary containing 'raw' and 'aggregated'
            pandas DataFrames with ping data.
        latency_threshold (float): Latency threshold in milliseconds for highlighting high latency regions.
        no_segmentation (bool, optional): If True, generates a single plot for the entire duration
            without segmentation. Defaults to False.

    Raises:
        OSError: If the plots subdirectory cannot be created.
        Exception: For any other errors that occur during plot generation.
    """
    # Retrieve the base plots folder from the configuration
    plots_folder = config.get("plots_folder", "plots")

    # Generate a timestamp for the subdirectory name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Create a timestamped subdirectory within the plots folder
    plots_subfolder = os.path.join(plots_folder, f"plots_{timestamp}")
    os.makedirs(plots_subfolder, exist_ok=True)
    logging.info(f"Created plots subdirectory: {plots_subfolder}")

    # Determine the maximum duration based on the data
    max_duration = max(data["raw"]["Time (s)"].max() for data in data_dict.values())
    max_duration = int(max_duration)
    logging.info(f"Maximum monitoring duration: {max_duration} seconds")

    # If no segmentation is requested, generate a single plot
    if no_segmentation:
        segment_starts = [0]
        segment_ends = [max_duration]
        segment_labels = ["entire_duration"]
    else:
        # Segmentation into hourly intervals
        segment_duration = 3600  # 1 hour in seconds
        segment_starts = list(range(0, max_duration, segment_duration))
        segment_ends = [
            min(start + segment_duration, max_duration) for start in segment_starts
        ]
        segment_labels = [f"hour_{i+1}" for i in range(len(segment_starts))]

    for segment_start, segment_end, segment_label in zip(
        segment_starts, segment_ends, segment_labels
    ):
        plt.figure(figsize=(14, 8))
        # Define a darker color palette
        palette = sns.color_palette("deep", n_colors=len(data_dict))
        high_latency_times = []

        for idx, (ip, data) in enumerate(data_dict.items()):
            raw_df = data["raw"]
            agg_df = data["aggregated"]
            color = palette[idx % len(palette)]
            plot_raw_df = raw_df.copy()
            plot_raw_df["Ping (ms)"] = plot_raw_df["Ping (ms)"].fillna(800.0)
            plot_raw_df["Ping (ms)"] = plot_raw_df["Ping (ms)"].clip(upper=800.0)

            # Filter data for the current segment
            segment_data = plot_raw_df[
                (plot_raw_df["Time (s)"] >= segment_start)
                & (plot_raw_df["Time (s)"] < segment_end)
            ]

            # Plot Raw Ping with increased opacity
            sns.lineplot(
                x="Time (s)",
                y="Ping (ms)",
                data=segment_data,
                label=f"{ip} Raw Ping",
                color=color,
                alpha=0.6,
            )

            # Identify High Latency Times from Raw Data
            high_latency_raw = segment_data[
                segment_data["Ping (ms)"] > latency_threshold
            ]
            if not high_latency_raw.empty:
                high_latency_times.extend(high_latency_raw["Time (s)"].tolist())

            if agg_df is not None:
                # Filter aggregated data for the current segment
                agg_segment = agg_df[
                    (agg_df["Time (s)"] >= segment_start)
                    & (agg_df["Time (s)"] < segment_end)
                ]

                # Plot Mean Latency
                sns.lineplot(
                    x="Time (s)",
                    y="Mean Latency (ms)",
                    data=agg_segment,
                    label=f"{ip} Mean Latency",
                    linestyle="--",
                    marker="o",
                    color=color,
                    alpha=0.8,
                )

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
            by_label.values(),
            by_label.keys(),
            loc="upper left",
            bbox_to_anchor=(1.05, 1),
        )

        # Adjust plot title and labels
        if no_segmentation:
            plt.title("Ping Monitoring - Entire Duration")
        else:
            segment_start_formatted = str(timedelta(seconds=segment_start))
            segment_end_formatted = str(timedelta(seconds=segment_end))
            plt.title(
                f"Ping Monitoring - {segment_label.replace('_', ' ').title()} ({segment_start_formatted} to {segment_end_formatted})"
            )

        plt.xlabel("Time (s)")
        plt.ylabel("Latency (ms)")
        plt.grid(
            color="lightgray", linestyle="--", linewidth=0.5, alpha=0.7
        )  # Customized grid
        plt.tight_layout()

        # Define the plot filename with date and time
        plot_filename = f"ping_plot_{timestamp}_{segment_label}.png"
        plot_path = os.path.join(plots_subfolder, plot_filename)

        # Save the plot
        plt.savefig(plot_path)
        plt.close()
        logging.info(f"Generated plot: {plot_path}")

        # Notify the user
        console.print(f"[bold green]Generated plot:[/bold green] {plot_path}")


def display_plots_and_summary(data_dict, config):
    """
    Coordinates plot generation and summary statistics display.

    This function checks if data is available and then calls `generate_plots` to create
    visualizations and `display_summary` to present statistics in a table. It handles
    scenarios where data may be missing.

    Args:
        data_dict (Dict[str, Dict[str, Optional[pd.DataFrame]]]): Nested dictionary containing ping data.
        config (Dict): Configuration dictionary containing settings.

    Example:
        >>> display_plots_and_summary(data_dict, config)
        # Generates plots and displays summary statistics.
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
