# config.py

import yaml
import os


def load_config(config_file="config.yaml"):
    # Default configuration values
    default_config = {
        "duration": 10800,
        "ip_addresses": ["8.8.8.8"],
        "ping_interval": 1,
        "aggregation": {
            "method": "mean",
            "interval": 60,
        },
        "segmentation": True,
        "results_folder": "results",
        "log_folder": "logs",
        "file": None,  # Added default
        "no_aggregation": False,
        "no_segmentation": False,
        "clear": False,
        "clear_results": False,
        "clear_logs": False,
        "yes": False,
    }

    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            user_config = yaml.safe_load(f)
            # Merge user_config into default_config
            config = {**default_config, **user_config}
    else:
        # If config file doesn't exist, use default config
        config = default_config

    return config
