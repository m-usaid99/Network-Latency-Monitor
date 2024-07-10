import re
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import logging
import argparse

# Use the Agg backend for matplotlib to improve performance in non-interactive environments
matplotlib.use('Agg')

def initialize_logging():
    current_date = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = f'logs/generate_plots_{current_date}.log'
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Python script started")

def parse_arguments():
    parser = argparse.ArgumentParser(description="WiFi Ping Monitor - Generate Plots from Ping Results")
    parser.add_argument("results_file", help="Path to the ping results file")
    parser.add_argument("plots_folder", help="Directory to save the plots")
    parser.add_argument("duration", type=int, help="Duration of the ping monitoring in seconds")
    parser.add_argument("ip_address", help="IP address to ping")
    return parser.parse_args()

def read_ping_results(file_path):
    logging.info(f"Reading ping results from {file_path}")
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return lines

def extract_ping_data(lines):
    ping_times = []
    packet_loss = 0

    for line in lines:
        match = re.search(r'time=(\d+\.?\d*) ms', line)
        if match:
            ping_times.append(float(match.group(1)))

        loss_match = re.search(r'(\d+)% packet loss', line)
        if loss_match:
            packet_loss = int(loss_match.group(1))
    
    logging.info(f"Extracted {len(ping_times)} ping times from the results file")
    logging.info(f"Packet loss: {packet_loss}%")

    return ping_times, packet_loss

def create_plots(ping_times, duration, plots_folder):
    ping_times = [min(1000, time) for time in ping_times]
    df = pd.DataFrame(ping_times, columns=['Ping (ms)'])
    full_hours = duration // 3600
    remaining_time = duration % 3600

    if full_hours < 1:
        logging.info("Duration is less than 1 hour, generating a single plot")
        plt.figure(figsize=(20, 15))
        plt.plot(df['Ping (ms)'])
        plt.title(f'WiFi Network Ping Over Time (Duration: {duration // 60} minutes, Max Value Capped at 1000 ms)')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Ping (ms)')
        plt.savefig(os.path.join(plots_folder, 'wifi_ping_plot.png'))
        plt.close()
        logging.info("Generated plot for the entire duration")
    else:
        samples_per_hour = len(df) // full_hours
        split_dfs = [df.iloc[i * samples_per_hour:(i + 1) * samples_per_hour] for i in range(full_hours)]

        for i, split_df in enumerate(split_dfs):
            plt.figure(figsize=(20, 15))
            plt.plot(split_df['Ping (ms)'])
            plt.title(f'WiFi Network Ping Over Time (Hour {i + 1}, Max Value Capped at 1000 ms)')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Ping (ms)')
            plt.savefig(os.path.join(plots_folder, f'wifi_ping_plot_hour_{i + 1}.png'))
            plt.close()
            logging.info(f"Generated plot for hour {i + 1}")

        if remaining_time > 0:
            remaining_samples = len(df) - full_hours * samples_per_hour
            remaining_df = df.iloc[-remaining_samples:]
            plt.figure(figsize=(20, 15))
            plt.plot(remaining_df['Ping (ms)'])
            plt.title(f'WiFi Network Ping Over Time (Remaining {remaining_time // 60} minutes, Max Value Capped at 1000 ms)')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Ping (ms)')
            plt.savefig(os.path.join(plots_folder, 'wifi_ping_plot_remaining.png'))
            plt.close()
            logging.info(f"Generated plot for remaining {remaining_time // 60} minutes")

def main():
    initialize_logging()
    args = parse_arguments()
    logging.info(f"Arguments received: results_file={args.results_file}, plots_folder={args.plots_folder}, duration={args.duration}, ip_address={args.ip_address}")

    lines = read_ping_results(args.results_file)
    ping_times, packet_loss = extract_ping_data(lines)
    create_plots(ping_times, args.duration, args.plots_folder)

    print(f'Total Packet Loss: {packet_loss}%')
    logging.info("Python script completed")

if __name__ == "__main__":
    main()
