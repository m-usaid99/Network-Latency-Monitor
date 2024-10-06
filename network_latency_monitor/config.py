# config.py

import yaml
import os
import shutil
from typing import Dict


def deep_merge_dicts(source: Dict, overrides: Dict) -> Dict:
    """
    Recursively merges two dictionaries.
    Values from 'overrides' take precedence over those in 'source'.
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and key in source and isinstance(source[key], dict):
            deep_merge_dicts(source[key], value)
        else:
            source[key] = value
    return source


def load_config(
    config_file: str = "config.yaml", template_file: str = "config.example.yaml"
) -> Dict:
    # Default configuration values
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
                # Deep merge user_config into default_config
                config = deep_merge_dicts(default_config.copy(), user_config)
            except yaml.YAMLError as e:
                print(f"Error parsing the config file: {e}")
                config = default_config
    else:
        # Check if template exists
        if os.path.exists(template_file):
            shutil.copy(template_file, config_file)
            print(
                f"Default configuration file created at '{config_file}'. Please review and modify it as needed."
            )
        else:
            # Create the default config file
            with open(config_file, "w") as f:
                yaml.dump(default_config, f, sort_keys=False)
            print(
                f"Default configuration file created at '{config_file}'. Please review and modify it as needed."
            )
        config = default_config

    return config


def regenerate_default_config(config_file: str = "config.yaml"):
    """
    Regenerates the config.yaml file with default settings.

    :param config_file: Path to the config file.
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

    with open(config_file, "w") as f:
        yaml.dump(default_config, f, sort_keys=False)
    print(
        f"Default configuration file regenerated at '{config_file}'. Please review and modify it as needed."
    )
