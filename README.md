# Ping Plotting Script

This project provides a way to monitor the ping of your WiFi network over a specified period and visualize the results. The script pings a specified IP address at regular intervals, saves the results to a text file, and generates plots to visualize the data.  

## Prerequisites

- Bash (to run the shell script)
- Python 3.x
- ```matplotlib``` and ```pandas```

You can install the required python libraries using pip:

    pip install matplotlib pandas

or 

    pip3 install matplotlib pandas

## Usage

### Running the Script

To monitor the ping of your WiFi network, run the monitor_ping.sh script. The script accepts optional arguments for the duration of the monitoring period and the IP address to ping.

    ./monitor_ping.sh [-t duration_in_seconds] [-i ip_address]

- ``` -t duration_in_seconds ```: The amount of time to collect data for, in seconds. The default value is 10,800 seconds (3 hours). 
- ```-i ip_address```: THe IP address to ping; Default: 8.8.8.8.


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
- ```results/```: Directory containing the ping results text files.
- ```plots/```: Directory containing the plots.

### Example File Structure
    .
    ├── monitor_ping.sh 
    ├── generate_plots.py 
    ├── results 
    │   └── ping_results_2024-07-08_14-23-45.txt
    └── plots/
        └── plots_2024-07-08_14-23-45/
            ├── wifi_ping_plot_hour_1.png
            ├── wifi_ping_plot_hour_2.png
            ├── wifi_ping_plot_hour_3.png
            └──	wifi_ping_plot_remaining.png	

## Future Work

- Implement option to change ping interval (provide both default and user-defined option).
- Find ways to optimize script, reduce runtime. 
- Find a nicer looking charting library, experiment with seaborn.
- Contributions are welcome.