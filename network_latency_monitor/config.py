# config.py

"""
Configuration Management

Handles loading, merging, validating, and regenerating configuration settings for NLM.

Functions:
    - load_config: Loads configuration from a YAML file.
    - merge_args_into_config: Merges CLI arguments into the configuration.
    - validate_config: Validates the configuration values.
    - regenerate_default_config: Regenerates the default configuration file.
    - get_standard_directories: Retrieves standard directories based on the operating system.
"""

import yaml
from pathlib import Path
import sys
from typing import Dict, Tuple
from rich.console import Console
from rich.prompt import Prompt
from appdirs import AppDirs

# Initialize Rich Console
console = Console()


def get_standard_directories(app_name: str) -> Tuple[Path, Path, Path, Path, Path]:
    """
    Retrieve standard directories based on the operating system.

    Args:
        app_name (str): The name of the application.

    Returns:
        Tuple[Path, Path, Path, Path, Path]: Paths for config_dir, data_dir, log_dir, plots_dir, and results_dir.
    """
    dirs = AppDirs(app_name)
    config_dir = Path(dirs.user_config_dir)
    data_dir = Path(dirs.user_data_dir)
    log_dir = Path(dirs.user_log_dir)
    plots_dir = data_dir / "plots"
    results_dir = data_dir / "results"
    return config_dir, data_dir, log_dir, plots_dir, results_dir


def load_config(config_file: str = "config.yaml") -> Dict:
    """
    Load configuration from a YAML file. Create one with default settings if it does not exist.

    Args:
        config_file (str, optional): Path to the config file. Defaults to "config.yaml".

    Returns:
        Dict: Configuration dictionary.
    """
    app_name = "NLM"  # Replace with your actual application name
    config_dir, data_dir, log_dir, plots_dir, results_dir = get_standard_directories(
        app_name
    )

    default_config = {
        "duration": 10800,  # in seconds
        "ip_addresses": ["8.8.8.8"],
        "ping_interval": 1,  # in seconds
        "latency_threshold": 200.0,  # in ms
        "no_aggregation": False,
        "no_segmentation": False,
        "config_dir": str(config_dir),
        "data_dir": str(data_dir),
        "file": None,  # Optional: Specify a ping result file to process
        "clear": False,  # Set to True to clear all data
        "clear_results": False,  # Set to True to clear results folder
        "clear_plots": False,  # Set to True to clear plots folder
        "clear_logs": False,  # Set to True to clear logs folder
        "yes": False,  # Set to True to auto-confirm prompts
    }

    if config_dir.exists():
        config_path = config_dir / config_file
    else:
        config_path = config_dir / config_file
        config_dir.mkdir(parents=True, exist_ok=True)
        console.print(
            f"[bold green]Created configuration directory at '{config_dir}'.[/bold green]"
        )

    if config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            # Merge user_config into default_config
            config = {**default_config, **user_config}
        except yaml.YAMLError as e:
            console.print(f"[bold red]Error parsing the config file: {e}[/bold red]")
            config = default_config
        except Exception as e:
            console.print(
                f"[bold red]Unexpected error loading config file '{config_path}': {e}[/bold red]"
            )
            config = default_config
    else:
        # Create config.yaml with default settings
        try:
            with config_path.open("w", encoding="utf-8") as f:
                yaml.dump(default_config, f, sort_keys=False)
            console.print(
                f"[bold green]Default configuration file created at '{config_path}'. Please review and modify it as needed.[/bold green]"
            )
        except Exception as e:
            console.print(
                f"[bold red]Failed to create default config file '{config_path}': {e}[/bold red]"
            )
            sys.exit(1)
        config = default_config

    # Ensure data directories exist
    for key, path in [
        ("data_dir", data_dir),
        ("log_dir", log_dir),
        ("plots_dir", plots_dir),
        ("results_dir", results_dir),
    ]:
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                console.print(
                    f"[bold green]Created directory '{path}' for '{key}'.[/bold green]"
                )
            except Exception as e:
                console.print(
                    f"[bold red]Failed to create directory '{path}' for '{key}': {e}[/bold red]"
                )
                sys.exit(1)

    return config


def regenerate_default_config(config_file: str = "config.yaml"):
    """
    Regenerate the config.yaml file with default settings after user confirmation.

    Args:
        config_file (str, optional): Path to the config file. Defaults to "config.yaml".
    """
    app_name = "NLM"  # Replace with your actual application name
    config_dir, data_dir, log_dir, plots_dir, results_dir = get_standard_directories(
        app_name
    )
    config_path = config_dir / config_file

    if config_path.exists():
        # Prompt for confirmation
        confirmation = Prompt.ask(
            f"[bold yellow]Are you sure you want to regenerate the default '{config_path}'? This will overwrite your current configuration.[/bold yellow]",
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
        "config_dir": str(config_dir),
        "data_dir": str(data_dir),
        "file": None,  # Optional: Specify a ping result file to process
        "clear": False,  # Set to True to clear all data
        "clear_results": False,  # Set to True to clear results folder
        "clear_plots": False,  # Set to True to clear plots folder
        "clear_logs": False,  # Set to True to clear logs folder
        "yes": False,  # Set to True to auto-confirm prompts
    }

    try:
        with config_path.open("w", encoding="utf-8") as f:
            yaml.dump(default_config, f, sort_keys=False)
        console.print(
            f"[bold green]Default configuration file regenerated at '{config_path}'. Please review and modify it as needed.[/bold green]"
        )

        # Create necessary directories based on default_config
        for folder_key, path in [
            ("data_dir", data_dir),
            ("log_dir", log_dir),
            ("plots_dir", plots_dir),
            ("results_dir", results_dir),
        ]:
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    console.print(
                        f"[bold green]Created directory '{path}' for '{folder_key}'.[/bold green]"
                    )
                except Exception as e:
                    console.print(
                        f"[bold red]Failed to create directory '{path}' for '{folder_key}': {e}[/bold red]"
                    )
                    sys.exit(1)

    except Exception as e:
        console.print(
            f"[bold red]Failed to regenerate config file '{config_path}': {e}[/bold red]"
        )
        sys.exit(1)


def merge_args_into_config(args, config: Dict) -> Dict:
    """
    Merge command-line arguments into the configuration dictionary, giving precedence to CLI arguments.

    Args:
        args: Parsed command-line arguments.
        config (Dict): Configuration dictionary.

    Returns:
        Dict: Updated configuration dictionary with CLI arguments merged in.
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
        "clear_logs": "clear_logs",
        "yes": "yes",
        # Add more mappings if needed
    }

    for arg_name, config_key in arg_to_config_map.items():
        arg_value = getattr(args, arg_name, None)
        if arg_value is not None:
            config[config_key] = arg_value

    # Handle positional arguments like ip_addresses
    if hasattr(args, "ip_addresses") and args.ip_addresses:
        config["ip_addresses"] = args.ip_addresses

    return config


def validate_config(config: Dict) -> None:
    """
    Validate configuration values and ensure necessary directories exist.

    Args:
        config (Dict): Configuration dictionary.

    Exits:
        SystemExit: If any validation fails or directory creation encounters an error.
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

    # Validate results_dir, plots_dir, and log_dir paths
    for folder_key in ["results_dir", "plots_dir", "log_dir"]:
        folder_path = Path(config.get(folder_key, ""))
        if not folder_path.is_dir() and config.get(folder_key, ""):
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
                console.print(
                    f"[bold green]Created missing folder '{folder_path}' for '{folder_key}'.[/bold green]"
                )
            except Exception as e:
                console.print(
                    f"[bold red]Failed to create folder '{folder_path}' for '{folder_key}': {e}[/bold red]"
                )
                sys.exit(1)

    # Add more validations as needed

