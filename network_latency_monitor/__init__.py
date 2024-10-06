# __init__.py

"""
Network Latency Monitor (NLM)

A comprehensive tool to monitor network latency by pinging specified IP addresses.
NLM provides real-time visualizations, progress tracking, and generates detailed reports.

Modules:
    - cli: Handles command-line argument parsing.
    - config: Manages configuration loading, merging, validation, and regeneration.
    - logger: Sets up logging configurations.
    - ping_manager: Manages ping operations and monitoring.
    - plot_generator: Processes ping results and generates plots.
    - utils: Contains utility functions for data clearing, confirmations, and more.

Usage:
    Importing key functions directly from the package for ease of use.

    ```python
    from network_latency_monitor import (
        parse_arguments,
        load_config,
        setup_logging,
        run_ping_monitoring,
        process_ping_results,
        display_plots_and_summary,
    )
    ```

Author:
    Your Name <your.email@example.com>

License:
    MIT License
"""

from .cli import parse_arguments
from .config import (
    load_config,
    merge_args_into_config,
    validate_config,
    regenerate_default_config,
)
from .logger import setup_logging
from .ping_manager import run_ping_monitoring
from .plot_generator import display_plots_and_summary
from .utils import (
    handle_clear_operations,
    validate_and_get_ips,
    create_results_directory,
    ask_confirmation,
)
from .data_processing import process_file_mode, process_ping_results

__all__ = [
    "parse_arguments",
    "load_config",
    "merge_args_into_config",
    "validate_config",
    "regenerate_default_config",
    "setup_logging",
    "run_ping_monitoring",
    "process_file_mode",
    "process_ping_results",
    "display_plots_and_summary",
    "handle_clear_operations",
    "validate_and_get_ips",
    "create_results_directory",
    "ask_confirmation",
]
