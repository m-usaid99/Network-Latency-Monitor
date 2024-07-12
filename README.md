# Ping Plotting Script

This project provides a way to monitor the ping of your WiFi network over a specified period and visualize the results. The script pings a specified IP address at regular intervals, saves the results to a text file, and generates plots to visualize the data.  

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


    ./monitor_ping.sh [-t duration_in_seconds] [-i ip_address] [-f file_to_ping_results.txt] [-p ping_interval] [--no-aggregation]

- ``` -t duration_in_seconds ```: The amount of time to collect data for, in seconds. The default value is 10,800 seconds (3 hours). 
- ```-i ip_address```: The IP address to ping; Default: 8.8.8.8.
- ```-f file_to_ping_results.txt```: If a user wants to use a previously generated results file, they can specify it. By default, the script will generate a new results file.
- ```-p ping_interval```: The time interval in seconds after which each ping is sent. 1 second by default. 
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

Note: The ```-f``` flag will cause the script to ignore any ```-i``` and ```-t``` flags.


Make sure to remember to grant the script permission to run in case it doesn't work by:

    chmod +x monitor_ping.sh

### Example

To run the script for one hour, and to ping the IP address 1.1.1.1:

    ./monitor_ping.sh -t 3600 -i 1.1.1.1

### Output

The script generates the following outputs:

- Ping Results: A text file in the ```results``` folder containing the raw ping data.
- Plots: A set of plots in the ```plots``` folder showing the ping times over the monitoring period.
The output files are named based on the current date and time to avoid conflicts.

### File Structure
- ```monitor_ping.sh```: The main script to run the monitoring.
- ```generate_plots.py```: The Python script that processes the ping results and generates plots.
- ```config.yaml```: Generated after first run. 
- ```results/```: Directory containing the ping results text files.
- ```plots/```: Directory containing the plots.
- `logs/`: Directory containing log files.

### Example File Structure
    .
    ├── monitor_ping.sh 
    ├── generate_plots.py 
    ├── config.yaml
    ├── results/
    │   └── ping_results_2024-07-08_14-23-45.txt
    ├── plots/
    │    └── plots_2024-07-08_14-23-45/
    │        ├── wifi_ping_plot_hour_1.png
    │        ├── wifi_ping_plot_hour_2.png
    │        ├── wifi_ping_plot_hour_3.png
    │        └── wifi_ping_plot_remaining.png	
    └── logs/
        └── monitor_ping_2024-07-08_14-23-45.log

## Configuration File

The script uses a configuration file (`config.yaml`) to manage default settings. If the configuration file does not exist, it will be created with default values.

### Example Configuration File

```yaml
duration: 10800
ip_address: "8.8.8.8"
ping_interval: 1
aggregation_interval: 60

plot:
  figure_size: [20, 15]
  dpi: 100
  theme: "darkgrid"
  font:
    title_size: 24
    label_size: 22
    tick_size: 20
    legend_size: 20

aggregation:
  method: "mean"  # Options: mean, median, min, max
  interval: 60    # Aggregation interval in seconds

segmentation:
  hourly: true

results_folder: "results"
plots_folder: "plots"
log_folder: "logs"
```
Users can modify this config file to handle default behavior, although some edge cases might cause irregular behavior. 

### Reset Configuration File
To reset the configuration file to default values, use the `-r` option:

```bash
./monitor_ping.sh -r
```

## Future Work

- Implement option to change ping interval (provide both default and user-defined option).
- Add extensive error handling.
- Find ways to optimize script, reduce runtime. 
- Find a nicer looking charting library.
- Contributions are welcome.