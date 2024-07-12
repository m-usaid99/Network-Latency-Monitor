import re
import sys
import os
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import logging
import argparse

# Use the Agg backend for matplotlib to improve performance in non-interactive environments
matplotlib.use('Agg')

# Global configuration
FIGSIZE = (20, 15)
AGGREGATION_INTERVAL = 60

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
    parser.add_argument("--no-aggregation", action='store_true', help="Disable data aggregation")
    return parser.parse_args()

def read_config(config_file='config.yaml'):
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        sys.exit(1)

def read_ping_results(file_path):
    logging.info(f"Reading ping results from {file_path}")
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        if not lines:
            logging.error("Error: Results file is empty.")
            sys.exit(1)
        return lines
    except FileNotFoundError:
        logging.error(f"Results file {file_path} not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading results file: {e}")
        sys.exit(1)

def extract_ping_data(lines):
    ping_times = []
    packet_loss = 0

    try:
        for line in lines:
            match = re.search(r'time=(\d+\.?\d*) ms', line)
            if match:
                ping_times.append(float(match.group(1)))

            loss_match = re.search(r'(\d+)% packet loss', line)
            if loss_match:
                packet_loss = int(loss_match.group(1))

        logging.info(f"Extracted {len(ping_times)} ping times from the results file")
        logging.info(f"Packet loss: {packet_loss}%")
    except Exception as e:
        logging.error(f"Error processing data: {e}")
        sys.exit(1)

    return ping_times, packet_loss

def aggregate_data(ping_times, interval, method='mean'):
    aggregated_data = []
    num_intervals = len(ping_times) // interval
    
    for i in range(num_intervals):
        chunk = ping_times[i * interval:(i + 1) * interval]
        if method == 'mean':
            aggregated_data.append(sum(chunk) / len(chunk))
        elif method == 'min':
            aggregated_data.append(min(chunk))
        elif method == 'max':
            aggregated_data.append(max(chunk))
    
    remaining_chunk = ping_times[num_intervals * interval:]
    if remaining_chunk:
        if method == 'mean':
            aggregated_data.append(sum(remaining_chunk) / len(remaining_chunk))
        elif method == 'min':
            aggregated_data.append(min(remaining_chunk))
        elif method == 'max':
            aggregated_data.append(max(remaining_chunk))
    
    return aggregated_data

def create_plots(ping_times, duration, interval, plots_folder, aggregation_method, aggregation_interval, no_aggregation):
    sns.set(style="darkgrid")
    try:
        # Cap the max value at 800 ms
        ping_times = [min(800, time) for time in ping_times]
        
        aggregated_data = []
        if not no_aggregation:
            aggregated_data = aggregate_data(ping_times, aggregation_interval, method=aggregation_method)
        
        time_stamps = [i * interval for i in range(len(ping_times))]
        df_raw = pd.DataFrame({'Time (s)': time_stamps, 'Ping (ms)': ping_times})

        if aggregated_data:
            agg_time_stamps = [(i * aggregation_interval) + (aggregation_interval / 2) for i in range(len(aggregated_data))]
            df_agg = pd.DataFrame({'Time (s)': agg_time_stamps, 'Ping (ms)': aggregated_data})

        current_date = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
        plot_subfolder = os.path.join(plots_folder, f'plots_{current_date}')
        os.makedirs(plot_subfolder, exist_ok=True)

        plt.figure(figsize=FIGSIZE)
        sns.lineplot(x='Time (s)', y='Ping (ms)', data=df_raw, label='Raw Data')
        if aggregated_data:
            sns.lineplot(x='Time (s)', y='Ping (ms)', data=df_agg, label=f'Aggregated Data ({aggregation_method})', linestyle='dotted', marker='o', linewidth=2.5)
        plt.title(f'WiFi Network Ping Over Time (Max Value Capped at 800 ms)')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Ping (ms)')
        plt.legend()
        plt.xticks(range(0, time_stamps[-1] + interval, max(1, (time_stamps[-1] + interval) // 10)))  # Adjust x-axis labels
        plt.savefig(os.path.join(plot_subfolder, 'wifi_ping_plot.png'))
        plt.close()
        logging.info("Generated plot for the entire duration")
    except Exception as e:
        logging.error(f"Error generating plots: {e}")
        sys.exit(1)

def main():
    initialize_logging()
    args = parse_arguments()
    config = read_config()
    
    logging.info(f"Arguments received: results_file={args.results_file}, plots_folder={args.plots_folder}, no_aggregation={args.no_aggregation}")
    
    # Update global configuration from config file
    global FIGSIZE, AGGREGATION_INTERVAL
    FIGSIZE = tuple(config['plot']['figure_size'])
    AGGREGATION_INTERVAL = config['aggregation']['interval']
    
    lines = read_ping_results(args.results_file)
    ping_times, packet_loss = extract_ping_data(lines)
    create_plots(ping_times, config['duration'], config['ping_interval'], args.plots_folder, config['aggregation']['method'], AGGREGATION_INTERVAL, args.no_aggregation)

    print(f'Total Packet Loss: {packet_loss}%')
    logging.info("Python script completed")

if __name__ == "__main__":
    main()
