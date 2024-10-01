# ping_manager.py

import subprocess
import asyncio
import logging


async def run_ping(ip_address, duration, interval, results_file):
    try:
        # Build the ping command based on the platform
        # For simplicity, we'll assume a Unix-like system
        # On Windows, the command and parameters would differ
        cmd = ["ping", ip_address, "-i", str(interval), "-w", str(duration)]

        with open(results_file, "w") as f:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=f, stderr=asyncio.subprocess.PIPE
            )
            await process.wait()

        logging.info(f"Ping completed for {ip_address}")
    except Exception as e:
        logging.error(f"Error running ping for {ip_address}: {e}")
