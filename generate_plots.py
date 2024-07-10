import re
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# Use the Agg backend for matplotlib to improve performance in non-interactive environments
matplotlib.use('Agg')

# Get the command-line arguments
results_file = sys.argv[1]
plots_folder = sys.argv[2]
duration = int(sys.argv[3])
ip_address = sys.argv[4]

# Read the ping results file
with open(results_file, 'r') as file:
    lines = file.readlines()

# Extract the ping times and packet loss
ping_times = []
packet_loss = 0

for line in lines:
    # Extract ping times
    match = re.search(r'time=(\d+\.?\d*) ms', line)
    if match:
        ping_times.append(float(match.group(1)))

    # Extract packet loss (usually found at the end of the file)
    loss_match = re.search(r'(\d+)% packet loss', line)
    if loss_match:
        packet_loss = int(loss_match.group(1))

# Cap the maximum ping time at 1000 ms
ping_times = [min(1000, time) for time in ping_times]

# Create a DataFrame
df = pd.DataFrame(ping_times, columns=['Ping (ms)'])

# Calculate the number of full hours and remaining time
full_hours = duration // 3600
remaining_time = duration % 3600

if full_hours < 1:
    # Plot the entire duration as a single plot if less than one hour
    plt.figure(figsize=(25, 25))  # Increase the width and height of the graph
    plt.plot(df['Ping (ms)'])
    plt.title(f'WiFi Network Ping Over Time (Duration: {duration // 60} minutes, Max Value Capped at 1000 ms)')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Ping (ms)')
    plt.savefig(os.path.join(plots_folder, 'wifi_ping_plot.png'))
    plt.close()
else:
    # Calculate the number of samples per hour
    samples_per_hour = len(df) // full_hours

    # Split the DataFrame into parts for each full hour
    split_dfs = [df.iloc[i * samples_per_hour:(i + 1) * samples_per_hour] for i in range(full_hours)]

    # Plot each full hour separately
    for i, split_df in enumerate(split_dfs):
        plt.figure(figsize=(20, 15))  # Increase the width and height of the graph
        plt.plot(split_df['Ping (ms)'])
        plt.title(f'WiFi Network Ping Over Time (Hour {i + 1}, Max Value Capped at 1000 ms)')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Ping (ms)')
        plt.savefig(os.path.join(plots_folder, f'wifi_ping_plot_hour_{i + 1}.png'))
        plt.close()

    # Plot the remaining time if there is any
    if remaining_time > 0:
        remaining_samples = len(df) - full_hours * samples_per_hour
        remaining_df = df.iloc[-remaining_samples:]
        plt.figure(figsize=(25, 15))
        plt.plot(remaining_df['Ping (ms)'])
        plt.title(f'WiFi Network Ping Over Time (Remaining {remaining_time // 60} minutes, Max Value Capped at 1000 ms)')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Ping (ms)')
        plt.savefig(os.path.join(plots_folder, 'wifi_ping_plot_remaining.png'))
        plt.close()

# Print packet loss
print(f'Total Packet Loss: {packet_loss}%')
