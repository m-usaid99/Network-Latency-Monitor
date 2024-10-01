# cli.py

import argparse


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    :return: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="WiFi Ping Monitor: Monitor and visualize network latency."
    )
    parser.add_argument("ip_addresses", nargs="*", help="IP addresses to ping.")
    parser.add_argument(
        "-d",
        "--duration",
        type=int,
        default=10800,  # Default duration: 3 hours
        help="Duration for the ping monitoring in seconds (default: 10800).",
    )
    parser.add_argument(
        "-i",
        "--ping_interval",
        type=int,
        default=1,  # Default interval: 1 second
        help="Interval between each ping in seconds (default: 1).",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Path to an existing ping result file to process.",
    )
    parser.add_argument(
        "--no-aggregation", action="store_true", help="Disable data aggregation."
    )
    parser.add_argument(
        "--clear", action="store_true", help="Clear all data (results, plots, logs)."
    )
    parser.add_argument(
        "--clear-results", action="store_true", help="Clear only the results folder."
    )
    parser.add_argument(
        "--clear-plots", action="store_true", help="Clear only the plots folder."
    )
    parser.add_argument(
        "--clear-logs", action="store_true", help="Clear only the logs folder."
    )

    return parser.parse_args()

