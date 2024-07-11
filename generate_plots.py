import re
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import logging
import argparse
import statistics

# Use the Agg backend for matplotlib to improve performance in non-interactive environments
matplotlib.use('Agg')

# Global configuration
FIGSIZE = (20, 15)  # Smaller figure size for better text readability

plt.rcParams.update({
    'font.size': 22,       # Default text size
    'axes.titlesize': 24,  # Title font size
    'axes.labelsize': 22,  # X and Y label font size
    'xtick.labelsize': 20, # X tick labels font size
    'ytick.labelsize': 20, # Y tick labels font size
    'legend.fontsize': 20, # Legend font size
})

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
    parser.add_argument("interval", type=int, help="Interval between pings in seconds")
    parser.add_argument("--aggregation_method", choices=['mean', 'min', 'max'], default='mean', help="Method for aggregating data")
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

def aggregate_data(ping_times, interval, method='mean'):
    aggregated_data = []
    if interval >= len(ping_times):
        if method == 'mean':
            aggregated_data.append(sum(ping_times) / len(ping_times))
        elif method == 'min':
            aggregated_data.append(min(ping_times))
        elif method == 'max':
            aggregated_data.append(max(ping_times))
    else:
        for i in range(0, len(ping_times), interval):
            chunk = ping_times[i:i+interval]
            if method == 'mean':
                aggregated_data.append(sum(chunk) / len(chunk))
            elif method == 'min':
                aggregated_data.append(min(chunk))
            elif method == 'max':
                aggregated_data.append(max(chunk))
    return aggregated_data

def create_plots(ping_times, duration, interval, plots_folder, aggregation_method):
    sns.set(style="darkgrid")  # Set the Seaborn style
    aggregated_data = aggregate_data(ping_times, interval, method=aggregation_method)
    time_stamps = [i for i in range(len(ping_times))]
    agg_time_stamps = [i for i in range(len(aggregated_data))]
    
    df_raw = pd.DataFrame({'Time (s)': time_stamps, 'Ping (ms)': ping_times})
    df_agg = pd.DataFrame({'Time (s)': agg_time_stamps, 'Ping (ms)': aggregated_data})
    
    full_hours = duration // 3600
    remaining_time = duration % 3600

    # Create subdirectory for plots
    current_date = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
    plot_subfolder = os.path.join(plots_folder, f'plots_{current_date}')
    os.makedirs(plot_subfolder, exist_ok=True)

    if full_hours < 1:
        logging.info("Duration is less than 1 hour, generating a single plot")
        plt.figure(figsize=FIGSIZE)
        sns.lineplot(x='Time (s)', y='Ping (ms)', data=df_raw, label='Raw Data')
        sns.lineplot(x='Time (s)', y='Ping (ms)', data=df_agg, label=f'Aggregated Data ({aggregation_method})', linestyle='dotted')
        plt.title(f'WiFi Network Ping Over Time (Duration: {duration // 60} minutes, Method: {aggregation_method})')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Ping (ms)')
        plt.legend()
        plt.savefig(os.path.join(plot_subfolder, 'wifi_ping_plot.png'))
        plt.close()
        logging.info("Generated plot for the entire duration")
    else:
        samples_per_hour = len(df_raw) // full_hours
        split_dfs_raw = [df_raw.iloc[i * samples_per_hour:(i + 1) * samples_per_hour] for i in range(full_hours)]
        split_dfs_agg = [df_agg.iloc[i * samples_per_hour:(i + 1) * samples_per_hour] for i in range(full_hours)]

        for i, (split_df_raw, split_df_agg) in enumerate(zip(split_dfs_raw, split_dfs_agg)):
            plt.figure(figsize=FIGSIZE)
            sns.lineplot(x='Time (s)', y='Ping (ms)', data=split_df_raw, label='Raw Data')
            sns.lineplot(x='Time (s)', y='Ping (ms)', data=split_df_agg, label=f'Aggregated Data ({aggregation_method})', linestyle='dotted')
            plt.title(f'WiFi Network Ping Over Time (Hour {i + 1}, Method: {aggregation_method})')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Ping (ms)')
            plt.legend()
            plt.savefig(os.path.join(plot_subfolder, f'wifi_ping_plot_hour_{i + 1}.png'))
            plt.close()
            logging.info(f"Generated plot for hour {i + 1}")

        if remaining_time > 0:
            remaining_samples = len(df_raw) - full_hours * samples_per_hour
            remaining_df_raw = df_raw.iloc[-remaining_samples:]
            remaining_df_agg = df_agg.iloc[-remaining_samples:]
            plt.figure(figsize=FIGSIZE)
            sns.lineplot(x='Time (s)', y='Ping (ms)', data=remaining_df_raw, label='Raw Data')
            sns.lineplot(x='Time (s)', y='Ping (ms)', data=remaining_df_agg, label=f'Aggregated Data ({aggregation_method})', linestyle='dotted')
            plt.title(f'WiFi Network Ping Over Time (Remaining {remaining_time // 60} minutes, Method: {aggregation_method})')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Ping (ms)')
            plt.legend()
            plt.savefig(os.path.join(plot_subfolder, 'wifi_ping_plot_remaining.png'))
            plt.close()
            logging.info(f"Generated plot for remaining {remaining_time // 60} minutes")

def main():
    initialize_logging()
    args = parse_arguments()
    logging.info(f"Arguments received: results_file={args.results_file}, plots_folder={args.plots_folder}, duration={args.duration}, ip_address={args.ip_address}, interval={args.interval}, aggregation_method={args.aggregation_method}")

    lines = read_ping_results(args.results_file)
    ping_times, packet_loss = extract_ping_data(lines)
    create_plots(ping_times, args.duration, args.interval, args.plots_folder, args.aggregation_method)

    print(f'Total Packet Loss: {packet_loss}%')
    logging.info("Python script completed")

if __name__ == "__main__":
    main()
