# ping_manager.py

import asyncio
import logging
import subprocess
import sys
import re
from rich.progress import Progress


async def run_ping(
    ip_address: str,
    duration: int,
    interval: int,
    results_file: str,
    progress: Progress,
    task_id: int,
):
    """
    Asynchronously pings an IP address, extracts latency, and updates the progress bar.

    :param ip_address: IP address to ping.
    :param duration: Total duration to run the ping in seconds.
    :param interval: Interval between pings in seconds.
    :param results_file: File path to save ping results.
    :param progress: Rich Progress instance for updating the progress bar.
    :param task_id: Task ID associated with the progress bar.
    """
    end_time = asyncio.get_event_loop().time() + duration

    # Determine the ping command based on the operating system
    if sys.platform.startswith("win"):
        ping_cmd = ["ping", "-n", "1", "-w", str(interval * 1000), ip_address]
    else:
        ping_cmd = ["ping", "-c", "1", "-W", str(interval), ip_address]

    # Regular expression to extract latency
    if sys.platform.startswith("win"):
        # Example output line: "Reply from 8.8.8.8: bytes=32 time=14ms TTL=117"
        latency_regex = re.compile(r"time[=<]\s*(\d+\.?\d*)ms")
    else:
        # Example output line: "64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=14.2 ms"
        latency_regex = re.compile(r"time\s*=\s*(\d+\.?\d*)\s*ms")

    while asyncio.get_event_loop().time() < end_time:
        try:
            # Execute the ping command
            proc = await asyncio.create_subprocess_exec(
                *ping_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            raw_output = stdout.decode().strip()
            error_output = stderr.decode().strip()

            # Log raw output for debugging
            if error_output:
                logging.debug(f"Ping Error for {ip_address}: {error_output}")

            if proc.returncode == 0:
                match = latency_regex.search(raw_output)
                if match:
                    current_latency = float(match.group(1))
                else:
                    # If latency not found, assume packet loss or unknown latency
                    current_latency = None
                    logging.warning(
                        f"Could not parse latency from ping output for {ip_address}. Output: {raw_output}"
                    )
            else:
                # Non-zero return code indicates an error or packet loss
                current_latency = None
                logging.error(f"Ping failed for {ip_address}. Error: {error_output}")

            # Update progress bar
            if current_latency is not None:
                # Cap latency at 800 ms for display purposes
                display_latency = min(current_latency, 800.0)
                description = f"[cyan]{ip_address} - {display_latency} ms"
                progress.update(task_id, advance=interval, description=description)
                logging.info(f"Ping to {ip_address}: {current_latency} ms")
            else:
                description = f"[cyan]{ip_address} - Lost"
                progress.update(task_id, advance=interval, description=description)
                logging.warning(f"Ping to {ip_address} lost or latency not measurable.")

            # Write the result to the file
            with open(results_file, "a") as f:
                if current_latency is not None:
                    f.write(f"{current_latency}\n")
                else:
                    f.write("Lost\n")

        except Exception as e:
            logging.error(f"Exception occurred while pinging {ip_address}: {e}")
            progress.update(
                task_id, advance=interval, description=f"[cyan]{ip_address} - Error"
            )
            with open(results_file, "a") as f:
                f.write(f"Error: {e}\n")

        await asyncio.sleep(interval)
