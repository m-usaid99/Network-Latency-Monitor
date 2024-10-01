# main.py

import asyncio
import logging
import os
import sys
import time
from datetime import datetime

from cli import parse_arguments
from config import load_config
from logger import setup_logging
from ping_manager import run_ping  # Ensure this function is defined correctly
from tqdm.asyncio import tqdm

from plot_generator import (
    extract_ping_times,
    aggregate_ping_times,
    generate_plots,
    process_ping_file,
)
from utils import clear_data

import pandas as pd


def ask_confirmation(message: str, auto_confirm: bool) -> bool:
    """
    Prompts the user for a yes/no confirmation unless auto_confirm is True.

    :param message: The confirmation message to display.
    :param auto_confirm: If True, automatically confirm without prompting.
    :return: True if user confirms or auto_confirm is True, False otherwise.
    """
    if auto_confirm:
        return True

    while True:
        response = input(f"{message} [y/N]: ").strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no", ""]:
            return False
        else:
            print("Please respond with 'y' or 'n'.")


async def run_pings_with_progress(args, config, results_subfolder):
    """
    Executes ping tasks and displays a progress bar.

    :param args: Parsed command-line arguments.
    :param config: Configuration dictionary.
    :param results_subfolder: Subdirectory to store ping result files.
    """
    duration = args.duration
    ping_interval = args.ping_interval

    tasks = []
    for ip in args.ip_addresses:
        results_file = os.path.join(results_subfolder, f"ping_results_{ip}.txt")
        task = asyncio.create_task(
            run_ping(
                ip_address=ip,
                duration=duration,
                interval=ping_interval,
                results_file=results_file,
            )
        )
        tasks.append(task)

    with tqdm(total=duration, desc="Ping Monitoring Progress", unit="s") as pbar:

        async def update_progress():
            start_time = time.time()
            while True:
                elapsed = int(time.time() - start_time)
                if elapsed >= duration:
                    pbar.update(duration - pbar.n)
                    break
                pbar.update(elapsed - pbar.n)
                await asyncio.sleep(1)

        await asyncio.gather(asyncio.gather(*tasks), update_progress())


async def main():
    args = parse_arguments()
    config = load_config()
    setup_logging(config.get("log_folder", "logs"))  # Initialize logging

    # Handle clear operations if any
    if args.clear or args.clear_plots or args.clear_results or args.clear_logs:
        # Build a list of folders to clear based on arguments
        folders_to_clear = []
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
                logging.info("Clear operation completed.")
            else:
                logging.info("Clear operation canceled by user.")
            return  # Exit after clearing

    # If file mode is enabled, process the file directly
    if args.file:
        process_ping_file(
            file_path=args.file,
            config=config,
            no_aggregation=args.no_aggregation,
            duration=args.duration,
        )
        return

    # Determine IP addresses
    if not args.ip_addresses:
        default_ip = config.get("ip_address", "8.8.8.8")
        args.ip_addresses = [default_ip]
        logging.info(f"No IP addresses provided. Using default IP: {default_ip}")

    # Create results subdirectory with timestamp
    results_folder = config.get("results_folder", "results")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_subfolder = os.path.join(results_folder, f"results_{timestamp}")
    os.makedirs(results_subfolder, exist_ok=True)

    # Run pings with progress tracking
    await run_pings_with_progress(args, config, results_subfolder)

    logging.info("All ping tasks completed.")

    # After pinging, read all result files in the subdirectory and build data_dict
    data_dict = {}
    ip_files = [
        f
        for f in os.listdir(results_subfolder)
        if f.startswith("ping_results_") and f.endswith(".txt")
    ]

    for file_name in ip_files:
        file_path = os.path.join(results_subfolder, file_name)
        # Correct IP parsing without splitting on '.'
        ip_address = file_name[len("ping_results_") : -len(".txt")]
        ping_times = extract_ping_times(file_path)
        if not ping_times:
            logging.warning(f"No ping times extracted from {file_path}. Skipping.")
            continue

        # Determine if aggregation should be enforced based on duration
        if args.duration < 60:
            aggregate = False
        else:
            aggregate = not args.no_aggregation

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

        # Store data
        data_dict[ip_address] = {"raw": raw_df, "aggregated": agg_df}

    # Generate plots
    if data_dict:
        generate_plots(config=config, data_dict=data_dict)
        logging.info("Plot generation completed.")
    else:
        logging.warning("No data available for plotting.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Ping monitoring interrupted by user.")
        sys.exit(0)

