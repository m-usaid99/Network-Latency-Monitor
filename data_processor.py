# data_processor.py

import logging
import pandas as pd
from typing import List, Optional, Dict


def extract_ping_times(file_path: str) -> List[Optional[float]]:
    """
    Extracts ping times from a ping result file.

    :param file_path: Path to the ping result file.
    :return: List of ping times with None for lost pings.
    """
    ping_times: List[Optional[float]] = []

    try:
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line.lower() == "lost":
                    ping_times.append(None)
                else:
                    try:
                        ping_time = float(line)
                        if ping_time > 800.0:
                            ping_time = 800.0
                            logging.warning(
                                f"Capped ping time at 800 ms in file {file_path}"
                            )
                        ping_times.append(ping_time)
                    except ValueError:
                        # Handle unexpected line format
                        ping_times.append(None)
                        logging.warning(
                            f"Unexpected line format in {file_path}: {line}"
                        )
        logging.info(f"Extracted {len(ping_times)} ping attempts from {file_path}")
    except FileNotFoundError:
        logging.error(f"Ping result file {file_path} not found.")
    except Exception as e:
        logging.error(f"Error extracting ping times from {file_path}: {e}")

    return ping_times


def aggregate_ping_times(
    ping_times: List[Optional[float]], interval: int
) -> List[tuple]:
    """
    Aggregates ping times over specified intervals.

    :param ping_times: List of ping times (float) or None for lost pings.
    :param interval: Number of pings to aggregate over.
    :return: List of tuples with (Time (s), Mean Latency (ms))
    """
    aggregated_data = []
    for i in range(0, len(ping_times), interval):
        window = ping_times[i : i + interval]
        successful_pings = [pt for pt in window if pt is not None]
        if successful_pings:
            mean_latency = sum(successful_pings) / len(successful_pings)
        else:
            mean_latency = float("nan")  # Indicate no successful pings in this window
        aggregated_data.append((i + interval, mean_latency))
    return aggregated_data


def create_raw_dataframe(ping_times: List[Optional[float]]) -> pd.DataFrame:
    """
    Converts ping times to a pandas DataFrame.

    :param ping_times: List of ping times.
    :return: DataFrame with Time (s) and Ping (ms).
    """
    return pd.DataFrame(
        {"Time (s)": range(1, len(ping_times) + 1), "Ping (ms)": ping_times}
    )
