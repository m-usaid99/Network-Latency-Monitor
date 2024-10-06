# config.py

import yaml
import os
import sys
from typing import Dict
from rich.console import Console
from rich.prompt import Prompt

# Initialize Rich Console
console = Console()


def load_config(config_file: str = "config.yaml") -> Dict:
    """
    Loads the configuration from config.yaml. If the file does not exist,
    it creates one with default settings.

    :param config_file: Path to the config file.
    :return: Configuration dictionary.
    """
    default_config = {
        "duration": 10800,  # in seconds
        "ip_addresses": ["8.8.8.8"],
        "ping_interval": 1,  # in seconds
        "latency_threshold": 200.0,  # in ms
        "no_aggregation": False,
        "no_segmentation": False,
        "results_folder": "results",
        "log_folder": "logs",
        "file": None,  # Optional: Specify a ping result file to process
        "clear": False,  # Set to True to clear all data
        "clear_results": False,  # Set to True to clear results folder
        "clear_logs": False,  # Set to True to clear logs folder
        "yes": False,  # Set to True to auto-confirm prompts
    }

    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            try:
                user_config = yaml.safe_load(f) or {}
                # Merge user_config into default_config
                config = {**default_config, **user_config}
            except yaml.YAMLError as e:
                console.print(
                    f"[bold red]Error parsing the config file: {e}[/bold red]"
                )
                config = default_config
    else:
        # Create config.yaml with default settings
        with open(config_file, "w") as f:
            yaml.dump(default_config, f, sort_keys=False)
        console.print(
            f"[bold green]Default configuration file created at '{config_file}'. Please review and modify it as needed.[/bold green]"
        )
        config = default_config

    return config


def regenerate_default_config(config_file: str = "config.yaml"):
    """
    Regenerates the config.yaml file with default settings after user confirmation.

    :param config_file: Path to the config file.
    """
    if os.path.exists(config_file):
        # Prompt for confirmation
        confirmation = Prompt.ask(
            f"[bold yellow]Are you sure you want to regenerate the default '{config_file}'? This will overwrite your current configuration.[/bold yellow]",
            choices=["y", "n"],
            default="n",
        )
        if confirmation.lower() not in ["y", "yes"]:
            console.print(
                "[bold green]Configuration regeneration canceled.[/bold green]"
            )
            return

    default_config = {
        "duration": 10800,  # in seconds
        "ip_addresses": ["8.8.8.8"],
        "ping_interval": 1,  # in seconds
        "latency_threshold": 200.0,  # in ms
        "no_aggregation": False,
        "no_segmentation": False,
        "results_folder": "results",
        "log_folder": "logs",
        "file": None,  # Optional: Specify a ping result file to process
        "clear": False,  # Set to True to clear all data
        "clear_results": False,  # Set to True to clear results folder
        "clear_logs": False,  # Set to True to clear logs folder
        "yes": False,  # Set to True to auto-confirm prompts
    }

    with open(config_file, "w") as f:
        yaml.dump(default_config, f, sort_keys=False)
    console.print(
        f"[bold green]Default configuration file regenerated at '{config_file}'. Please review and modify it as needed.[/bold green]"
    )


def merge_args_into_config(args, config):
    """
    Merges command-line arguments into the configuration dictionary,
    giving precedence to CLI arguments over config file settings.
    """
    # Map CLI argument names to config keys
    arg_to_config_map = {
        "duration": "duration",
        "ping_interval": "ping_interval",
        "latency_threshold": "latency_threshold",
        "no_aggregation": "no_aggregation",
        "no_segmentation": "no_segmentation",
        "file": "file",
        "clear": "clear",
        "clear_results": "clear_results",
        "clear_plots": "clear_plots",  # Added clear_plots mapping
        "clear_logs": "clear_logs",
        "yes": "yes",
        # Add more mappings if needed
    }

    for arg_name, config_key in arg_to_config_map.items():
        arg_value = getattr(args, arg_name, None)
        if arg_value is not None:
            config[config_key] = arg_value

    # Handle positional arguments like ip_addresses
    if args.ip_addresses:
        config["ip_addresses"] = args.ip_addresses

    return config


def validate_config(config):
    """
    Validates configuration values.
    """
    # Validate duration
    if not isinstance(config.get("duration"), int) or config["duration"] <= 0:
        console.print("[bold red]Invalid duration in configuration.[/bold red]")
        sys.exit(1)

    # Validate ping_interval
    if not isinstance(config.get("ping_interval"), int) or config["ping_interval"] <= 0:
        console.print("[bold red]Invalid ping_interval in configuration.[/bold red]")
        sys.exit(1)

    # Validate latency_threshold
    if (
        not isinstance(config.get("latency_threshold"), float)
        or config["latency_threshold"] <= 0
    ):
        console.print(
            "[bold red]Invalid latency_threshold in configuration.[/bold red]"
        )
        sys.exit(1)

    # Add more validations as needed
