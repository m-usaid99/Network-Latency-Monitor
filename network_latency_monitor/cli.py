# cli.py

import argparse


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    :return: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="NLM: Network Latency Monitor - Monitor and visualize network latency.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  1. Monitor two IP addresses for 1 hour with a 2-second interval between pings:\n"
            "     nlm 8.8.8.8 1.1.1.1 --duration 3600 --ping-interval 2\n\n"
            "  2. Process an existing ping results file and disable data aggregation:\n"
            "     nlm --file results/ping_results_8.8.8.8.txt --no-aggregation\n\n"
            "  3. Clear all data (results, plots, logs) without confirmation:\n"
            "     nlm --clear --yes\n\n"
            "  4. Monitor a single IP address with a custom latency threshold:\n"
            "     nlm 8.8.4.4 --latency-threshold 150.0\n"
        ),
    )

    # Positional arguments
    parser.add_argument(
        "ip_addresses",
        nargs="*",
        help="IP addresses to ping.",
    )

    # Optional arguments
    optional = parser.add_argument_group("Optional Arguments")

    optional.add_argument(
        "-d",
        "--duration",
        type=int,
        default=10800,  # Default duration: 3 hours
        help="Duration for the ping monitoring in seconds (default: 10800).",
    )
    optional.add_argument(
        "-i",
        "--ping-interval",
        type=int,
        default=1,  # Default interval: 1 second
        help="Interval between each ping in seconds (default: 1).",
    )
    optional.add_argument(
        "-f",
        "--file",
        type=str,
        help="Path to an existing ping result file to process.",
    )
    optional.add_argument(
        "--latency-threshold",
        type=float,
        default=200.0,
        help="Latency threshold in milliseconds for highlighting high latency regions (default: 200.0).",
    )
    optional.add_argument(
        "--no-segmentation",
        action="store_true",
        help="Generate a single plot for the entire duration without segmentation.",
    )

    # Aggregation arguments
    aggregation = parser.add_argument_group("Aggregation Options")

    aggregation.add_argument(
        "--no-aggregation",
        action="store_true",
        help="Disable data aggregation.",
    )

    # Clear operations
    clear_group = parser.add_mutually_exclusive_group()

    clear_group.add_argument(
        "--clear",
        action="store_true",
        help="Clear all data (results, plots, logs).",
    )
    clear_group.add_argument(
        "--clear-results",
        action="store_true",
        help="Clear only the results folder.",
    )
    clear_group.add_argument(
        "--clear-plots",
        action="store_true",
        help="Clear only the plots folder.",
    )
    clear_group.add_argument(
        "--clear-logs",
        action="store_true",
        help="Clear only the logs folder.",
    )

    # Confirmation flag
    optional.add_argument(
        "--yes",
        action="store_true",
        help="Automatically confirm prompts.",
    )

    return parser.parse_args()

