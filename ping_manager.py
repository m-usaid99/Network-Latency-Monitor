# ping_manager.py

import asyncio
import logging
import sys
import re
from rich.progress import Progress, TaskID


async def run_ping(
    ip_address: str,
    duration: int,
    interval: int,
    results_file: str,
    progress: Progress,
    task_id: TaskID,  # Updated type annotation
):
    loop = asyncio.get_event_loop()
    start_time = loop.time()
    end_time = start_time + duration
    last_update_time = start_time

    if sys.platform.startswith("win"):
        ping_cmd = ["ping", "-n", "1", "-w", str(interval * 1000), ip_address]
        latency_regex = re.compile(r"time[=<]\s*(\d+\.?\d*)ms")
    else:
        ping_cmd = ["ping", "-c", "1", "-W", str(interval), ip_address]
        latency_regex = re.compile(r"time\s*=\s*(\d+\.?\d*)\s*ms")

    while True:
        current_time = loop.time()
        if current_time >= end_time:
            break

        iteration_start_time = current_time

        # Initialize current_latency to None at the start of each iteration
        current_latency = None

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
                    current_latency = None
                    logging.warning(
                        f"Could not parse latency from ping output for {ip_address}. Output: {raw_output}"
                    )
            else:
                current_latency = None
                logging.error(f"Ping failed for {ip_address}. Error: {error_output}")

            # Write the result to the file
            with open(results_file, "a") as f:
                if current_latency is not None:
                    f.write(f"{current_latency}\n")
                else:
                    f.write("Lost\n")

        except Exception as e:
            logging.error(f"Exception occurred while pinging {ip_address}: {e}")
            current_latency = None  # Ensure current_latency is defined
            # Write the error to the file
            with open(results_file, "a") as f:
                f.write(f"Error: {e}\n")

        finally:
            # Update progress bar based on actual elapsed time
            current_time = loop.time()
            elapsed_since_last_update = current_time - last_update_time
            last_update_time = current_time

            if current_latency is not None:
                display_latency = min(current_latency, 800.0)
                description = f"[cyan]{ip_address} - {display_latency} ms"
                progress.update(
                    task_id,
                    advance=elapsed_since_last_update,
                    description=description,
                )
                logging.info(f"Ping to {ip_address}: {current_latency} ms")
            else:
                description = f"[cyan]{ip_address} - Lost"
                progress.update(
                    task_id,
                    advance=elapsed_since_last_update,
                    description=description,
                )
                logging.warning(f"Ping to {ip_address} lost or latency not measurable.")

        # Calculate time until next ping
        iteration_end_time = loop.time()
        time_taken = iteration_end_time - iteration_start_time
        sleep_time = interval - time_taken
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        else:
            logging.warning(
                f"Ping execution took longer than interval for {ip_address}."
            )

    # Ensure the progress bar reaches 100%
    progress.update(task_id, completed=duration)

