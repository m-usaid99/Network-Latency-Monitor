# Ping Plotting Script

This project provides a way to monitor the ping of your WiFi network over a specified period and visualize the results. The script pings a list of specified IP addresses at regular intervals, saves the results to text files, and generates plots to visualize the data.

## Prerequisites

- Bash (to run the shell script)
- Python 3.x
  - `matplotlib` and `pandas`
  - `seaborn`
  - `argparse`
  - `yaml`

You can install the required python libraries using pip:

    pip install matplotlib pandas argparse seaborn pyyaml

or

    pip3 install matplotlib pandas argparse seaborn pyyaml

## Usage

### Running the Script

To monitor the ping of your WiFi network, run the monitor_ping.sh script. The script accepts optional arguments for the duration of the monitoring period and the IP address to ping.

    ./monitor_ping.sh [-t duration_in_seconds] [-f file_to_ping_results.txt] [-p ping_interval] [--no-aggregation] [ip_adresses...]

- `-t duration_in_seconds`: The amount of time to collect data for, in seconds. The default value is 10,800 seconds (3 hours).
- `-f file_to_ping_results.txt`: If a user wants to use a previously generated results file, they can specify it. By default, the script will generate a new results file.
- `-p ping_interval`: The time interval in seconds after which each ping is sent. 1 second by default.
- `--no-aggregation`: Disable data aggregation.
- `-r`
- `-c [all|results|plots|logs]`: Clear specified data (with confirmation)
  - `all`: Clear all results, plots, and logs.
  - `results`: Clear all results.
  - `plots`: Clear all plots.
  - `logs`: Clear all logs.
- `-P`: Clear all plots (with confirmation).
- `-R`: Clear all results (with confirmation).
- `-L`: Clear all logs (with confirmation).
- `-h`: Show this help message and exit.
- `ip_addresses`: List of space-separated IP addresses to ping. No arguments provided will default to 8.8.8.8.

Note: The `-f` flag will cause the script to ignore any `-t` and `-p` flags.

Make sure to remember to grant the script permission to run in case it doesn't work by:

    chmod +x monitor_ping.sh

### Example Usages

#### Default

To run the default script (3 hours with 1 second intervals, 8.8.8.8, with aggregation):

    ./monitor_ping.sh

#### Custom Duration and IP Addresses

To run the script for one hour, and to ping the IP address 1.1.1.1 and 8.8.8.8:

    ./monitor_ping.sh -t 3600 1.1.1.1 8.8.8.8

#### Custom Ping Interval

This command sets the interval between pings to 2 seconds, while retaining default values for other options/arguments.

    ./monitor_ping.sh -p 2

#### Using an Existing Text File with Ping Results

This command uses an existing text file with ping results instead of running the ping command.

    ./monitor_ping.sh -f existing_ping_results.txt

#### Disable Aggregation

This command runs the script without aggregating data.

    ./monitor_ping.sh --no-aggregation

Note: For durations less than 60 seconds, aggregation is disabled by default. 

### Comprehensive Example

This example includes all possible customizable options with a list of IP addresses to ping:

    ./monitor_ping.sh -t 1800 -p 3 --no-aggregation 1.1.1.1 8.8.8.8

This command will ping 1.1.1.1 and 8.8.8.8 for 30 minutes every 3 seconds, without recording/plotting any aggregate data. 

**IMPORTANT:** The list of IP addresses should be passed as a space-separated list as the last argument to the script. 

### Output

The script generates the following outputs:

- Ping Results: A text file in the `results` folder containing the raw ping data.
- Plots: A set of plots in the `plots` folder showing the ping times over the monitoring period.
  The output files are named based on the current date and time to avoid conflicts. The plots will contain graphs for ping results for each IP address specified along with aggregate values plotted on the same graph. 

### File Structure

- `monitor_ping.sh`: The main script to run the monitoring.
- `generate_plots.py`: The Python script that processes the ping results and generates plots.
- `config.yaml`: Generated after first run.
- `results/`: Directory containing the ping results text files.
- `plots/`: Directory containing the plots.
- `logs/`: Directory containing log files.

### Example File Structure

```
.
├── monitor_ping.sh
├── generate_plots.py
├── config.yaml
├── results/
│   ├── ping_results_1.1.1.1_2024-07-08_14-23-45.txt
│   └── ping_results_8.8.8.8_2024-07-08_14-23-45.txt
├── plots/
│    └── plots_2024-07-08_14-23-45/
│        ├── wifi_ping_plot_hour_1.png
│        ├── wifi_ping_plot_hour_2.png
│        ├── wifi_ping_plot_hour_3.png
│        └── wifi_ping_plot_remaining.png
└── logs/
    └── monitor_ping_2024-07-08_14-23-45.log
```

## Configuration File

The script uses a configuration file (`config.yaml`) to manage default settings. If the configuration file does not exist, it will be created with default values.

### Example Configuration File

```yaml
# Default configuration values

# Duration for the ping monitoring in seconds
# Default: 10800 seconds (3 hours)
duration: 10800

# IP address to ping
# Default: "8.8.8.8"
ip_address: "8.8.8.8"

# Interval between each ping in seconds
# Default: 1 second
ping_interval: 1

# Aggregation interval in seconds for data aggregation
# Default: 60 seconds (1 minute)
aggregation_interval: 60

# Plotting settings
plot:
  # Figure size for the plots
  # Default: [20, 15]
  figure_size: [20, 15]

  # Dots per inch (DPI) setting for the plots
  # Default: 100
  dpi: 100

  # Seaborn theme for the plots
  # Options: "darkgrid", "whitegrid", "dark", "white", "ticks"
  # Default: "darkgrid"
  theme: "darkgrid"

  # Font sizes for various elements in the plots
  font:
    # Font size for the plot titles
    # Default: 24
    title_size: 24

    # Font size for the axis labels
    # Default: 22
    label_size: 22

    # Font size for the tick labels
    # Default: 20
    tick_size: 20

    # Font size for the legend
    # Default: 20
    legend_size: 20

# Data aggregation settings
aggregation:
  # Aggregation method
  # Options: "mean", "median", "min", "max"
  # Default: "mean"
  method: "mean"

  # Aggregation interval in seconds
  # Default: 60 seconds (1 minute)
  interval: 60

# Data segmentation settings
segmentation:
  # Segment data by hour
  # Default: true
  hourly: true

# Folder paths
# Directory to save the results
results_folder: "results"

# Directory to save the plots
plots_folder: "plots"

# Directory to save the log files
log_folder: "logs"
```

Users can modify this config file to handle default behavior, although some edge cases might cause irregular behavior.

### Reset Configuration File

To reset the configuration file to default values, use the `-r` option:

```bash
./monitor_ping.sh -r
```

## Future Work

- Remove known bugs when -p option is altered. (Chart labels are mismatched, will be fixed soon.) 
- Enhance data visualization with more advanced charts and interactive features.
- Continue improving error handling and logging for even better robustness.
- Add support for additional customization options for advanced users through the configuration file.
- Add support for different output formats, such as JSON or CSV, for the results data.
- Add automated testing to ensure script reliability and performance.
- Explore packaging, containerization, and deployment options. 
- Contributions are welcome.
