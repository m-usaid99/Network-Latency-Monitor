# config.py

import yaml
import os


def load_config(config_file="config.yaml"):
    # Default configuration values
    default_config = {
        "duration": 10800,
        "ip_address": "8.8.8.8",
        "ping_interval": 1,
        "aggregation_interval": 60,
        "plot": {
            "figure_size": [20, 15],
            "dpi": 100,
            "theme": "darkgrid",
            "font": {
                "title_size": 24,
                "label_size": 22,
                "tick_size": 20,
                "legend_size": 20,
            },
        },
        "aggregation": {"method": "mean", "interval": 60},
        "segmentation": {"hourly": True},
        "results_folder": "results",
        "plots_folder": "plots",
        "log_folder": "logs",
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
