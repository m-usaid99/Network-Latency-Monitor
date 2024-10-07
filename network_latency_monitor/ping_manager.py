# ping_manager.py

"""
Ping Manager

Handles the core functionality of pinging IP addresses, managing asynchronous tasks,
and providing real-time feedback through progress bars and latency graphs.

Functions:
    - run_ping: Executes ping commands and records latency.
    - run_ping_monitoring: Initiates ping monitoring for multiple IP addresses with real-time visualizations.
"""

import asyncio
import re
import sys
from collections import deque
from pathlib import Path
from typing import Dict

import asciichartpy
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.text import Text

console = Console()


async def run_ping(
    ip_address: str,
    duration: int,
    interval: int,
    results_file: Path,
    progress: Progress,
    task_id: TaskID,
    latency_data: Dict[str, deque],
):
    """
    Executes the ping command for a specific IP address, records latency, and updates progress.

    This asynchronous function pings the specified IP address at regular intervals, records
    the latency results, updates the corresponding progress bar, and handles any errors
    or lost packets.

    Args:
        ip_address (str): The IP address to ping.
        duration (int): Total duration for which to ping, in seconds.
        interval (int): Interval between consecutive pings, in seconds.
        results_file (Path): Path to the file where ping results are recorded.
        progress (Progress): Rich Progress instance to update the progress bar.
        task_id (TaskID): Identifier for the specific progress task.
        latency_data (Dict[str, deque]): Dictionary storing latency data for each IP address.
    """
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

            raw_output = stdout.decode("utf-8").strip()
            error_output = stderr.decode("utf-8").strip()

            # Log raw output for debugging
            if error_output:
                # Use logging as per your central logging setup
                pass  # Replace with logging.debug(...) if needed

            if proc.returncode == 0:
                match = latency_regex.search(raw_output)
                if match:
                    current_latency = float(match.group(1))
                else:
                    current_latency = None
                    # Use logging as per your central logging setup
                    pass  # Replace with logging.warning(...) if needed
            else:
                current_latency = None
                # Use logging as per your central logging setup
                pass  # Replace with logging.error(...) if needed

            # Write the result to the file with explicit encoding
            with results_file.open("a", encoding="utf-8") as f:
                if current_latency is not None:
                    f.write(f"{current_latency}\n")
                else:
                    f.write("Lost\n")

        except Exception as e:
            # Use logging as per your central logging setup
            pass  # Replace with logging.error(...) if needed
            current_latency = None  # Ensure current_latency is defined
            # Write the error to the file with explicit encoding
            with results_file.open("a", encoding="utf-8") as f:
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
                # Update in-memory latency data
                latency_data[ip_address].append(current_latency)
            else:
                description = f"[cyan]{ip_address} - Lost"
                progress.update(
                    task_id,
                    advance=elapsed_since_last_update,
                    description=description,
                )
                # Append 0 to represent lost ping
                latency_data[ip_address].append(0)

        # Calculate time until next ping
        iteration_end_time = loop.time()
        time_taken = iteration_end_time - iteration_start_time
        sleep_time = interval - time_taken
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)

    # Ensure the progress bar reaches 100%
    progress.update(task_id, completed=duration)


async def run_ping_monitoring(config, results_subfolder, latency_data):
    """
    Initiates ping monitoring for multiple IP addresses with progress bars and real-time graphs.

    This asynchronous function sets up ping tasks for each IP address based on the provided configuration.
    It manages the execution of these tasks, updates progress bars, and renders real-time ASCII-based
    latency graphs using Rich and asciichartpy.

    Args:
        config (dict): Configuration dictionary containing settings like duration, ping intervals, IP addresses, etc.
        results_subfolder (Path): Path to the directory where ping results will be stored.
        latency_data (Dict[str, deque]): Dictionary to store latency data for each IP address.
    """
    duration = config.get("duration", 10800)
    ping_interval = config.get("ping_interval", 1)
    ips = config["ip_addresses"]
    tasks = []

    # Initialize Rich Progress
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )

    # Create tasks for each IP
    task_id_map = {}
    for ip in ips:
        results_file = results_subfolder / f"ping_results_{ip}.txt"
        task_id = progress.add_task(f"Pinging [cyan]{ip}[/cyan]", total=duration)
        task_id_map[ip] = task_id
        task = asyncio.create_task(
            run_ping(
                ip_address=ip,
                duration=duration,
                interval=ping_interval,
                results_file=results_file,
                progress=progress,
                task_id=task_id,
                latency_data=latency_data,
            )
        )
        tasks.append(task)

    # Calculate dynamic graph dimensions
    terminal_width = console.size.width
    terminal_height = console.size.height
    reserved_height = 10  # Reserve some lines for margins and other info
    progress_bar_height = len(ips) * 3  # Approximate progress bar height
    available_height = terminal_height - reserved_height - progress_bar_height
    graph_height = (
        max(5, available_height // len(ips)) if len(ips) > 0 else 5
    )  # Ensure a minimum height

    # Define a sliding window size
    window_size = 50  # Number of recent data points to display

    # Start the Live context
    with Live(console=console, refresh_per_second=4) as live:
        while not all(task.done() for task in tasks):
            # Generate ASCII charts
            charts = []
            for ip in ips:
                data = list(latency_data[ip])[-window_size:]
                current_max = max(data) if data else 100
                plot_max = max(current_max, 100)  # Ensure plot max is at least 100ms

                # Determine graph width based on number of columns
                if len(ips) == 1:
                    graph_width = (
                        terminal_width - 10
                    )  # Use most of the terminal width for a single IP
                elif len(ips) <= 2:
                    graph_width = (
                        terminal_width // 2
                    ) - 10  # Split the terminal width between two IPs
                else:
                    graph_width = (
                        terminal_width // 3
                    ) - 10  # Adjust as needed for more IPs

                chart = asciichartpy.plot(
                    data,
                    {
                        "height": graph_height,
                        "min": 0,
                        "max": plot_max,
                        "format": "{:>6.1f}",
                        "padding": 1,
                        "width": graph_width,
                    },
                )

                # Determine color based on current max latency
                if current_max < 75:
                    color = "green"
                elif current_max < 125:
                    color = "yellow"
                else:
                    color = "red"

                colored_chart = f"[{color}]{chart}[/{color}]"
                charts.append(
                    Panel(colored_chart, title=f"IP: {ip}", border_style=color)
                )

            # Organize charts into columns
            if len(charts) > 1:
                charts_renderable = Columns(charts, equal=True)
            else:
                charts_renderable = (
                    charts[0]
                    if charts
                    else Panel(
                        "No Data", title="Real-time Latency Graphs", border_style="grey"
                    )
                )

            # Create the legend panel with markup enabled
            legend_text = Text.from_markup(
                "Legend: [green]Green[/green] < 75ms | [yellow]Yellow[/yellow] 75ms-125ms | [red]Red[/red] > 125ms",
                style="bold",
            )
            legend_panel = Panel(legend_text, border_style="none", expand=False)

            # Combine charts and legend
            charts_renderable = Group(charts_renderable, legend_panel)

            # Render the progress bars
            progress_renderable = Panel(
                progress, title="Ping Progress", border_style="blue", expand=False
            )

            # Combine progress and charts into a single renderable
            combined = Group(progress_renderable, charts_renderable)

            # Update the Live display
            live.update(combined)

            await asyncio.sleep(0.5)  # Adjust the sleep time as needed

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

