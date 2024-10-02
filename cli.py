# cli.py

import argparse


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    :return: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="WiFi Ping Monitor: Monitor and visualize network latency.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Positional arguments
    parser.add_argument(
        "ip_addresses",
        nargs="*",
        help="IP addresses to ping.\n\nExample:\n  python3 main.py 8.8.8.8 1.1.1.1",
    )

    # Optional arguments
    optional = parser.add_argument_group("Optional Arguments")

    optional.add_argument(
        "-d",
        "--duration",
        type=int,
        default=10800,  # Default duration: 3 hours
        help="Duration for the ping monitoring in seconds (default: 10800).\n\nExample:\n  -d 3600",
    )
    optional.add_argument(
        "-i",
        "--ping_interval",
        type=int,
        default=1,  # Default interval: 1 second
        help="Interval between each ping in seconds (default: 1).\n\nExample:\n  -i 2",
    )
    optional.add_argument(
        "-f",
        "--file",
        type=str,
        help="Path to an existing ping result file to process.\n\nExample:\n  -f results/results_2024-04-27_12-34-56/ping_results_8.8.8.8.txt",
    )

    optional.add_argument(
        "--latency-threshold",
        type=float,
        default=150.0,
        help="Latency threshold in milliseconds for highlighting high latency regions.",
    )

    # Aggregation arguments
    aggregation = parser.add_argument_group("Aggregation Options")

    aggregation.add_argument(
        "--no-aggregation",
        action="store_true",
        help="Disable data aggregation.\n\nExample:\n  --no-aggregation",
    )

    # Clear operations
    clear_group = parser.add_mutually_exclusive_group()

    clear_group.add_argument(
        "--clear",
        action="store_true",
        help="Clear all data (results, plots, logs).\n\nExample:\n  --clear",
    )
    clear_group.add_argument(
        "--clear-results",
        action="store_true",
        help="Clear only the results folder.\n\nExample:\n  --clear-results",
    )
    clear_group.add_argument(
        "--clear-plots",
        action="store_true",
        help="Clear only the plots folder.\n\nExample:\n  --clear-plots",
    )
    clear_group.add_argument(
        "--clear-logs",
        action="store_true",
        help="Clear only the logs folder.\n\nExample:\n  --clear-logs",
    )

    # Confirmation flag
    optional.add_argument(
        "--yes",
        action="store_true",
        help="Automatically confirm prompts.\n\nExample:\n  --yes",
    )

    return parser.parse_args()
