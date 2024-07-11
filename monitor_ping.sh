#!/bin/bash

# Configuration file
config_file="config.yaml"

# Default configuration values
default_config=$(cat <<EOL
# Default configuration values
duration: 10800
ip_address: "8.8.8.8"
interval: 1

# Plotting settings
plot:
  figure_size: [30, 25]
  dpi: 100
  theme: "darkgrid"
  font:
    title_size: 20
    label_size: 18
    tick_size: 16
    legend_size: 16

# Data aggregation settings
aggregation:
  method: "mean"  # Options: mean, median, min, max
  interval: 60    # Aggregation interval in seconds

# Data segmentation settings
segmentation:
  hourly: true

# Folder paths
results_folder: "results"
plots_folder: "plots"
log_folder: "logs"
EOL
)

# Function to create a default configuration file
create_default_config() {
  echo "$default_config" > $config_file
  echo "Default configuration file created: $config_file"
}

# Check if configuration file exists
if [ ! -f $config_file ]; then
  create_default_config
fi

# Function to read values from the YAML configuration file using Python
read_config() {
  python3 -c "
import yaml
import sys

config_file = '$config_file'
with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

print(config.get('$1', ''))
"
}

# Load configuration values
duration=$(read_config 'duration')
ip_address=$(read_config 'ip_address')
interval=$(read_config 'interval')
results_folder=$(read_config 'results_folder')
plots_folder=$(read_config 'plots_folder')
log_folder=$(read_config 'log_folder')

# Use default values if variables are empty
results_folder=${results_folder:-"results"}
plots_folder=${plots_folder:-"plots/plots_$(date +%Y-%m-%d_%H-%M-%S)"}
log_folder=${log_folder:-"logs"}

# Parse arguments
while getopts "t:i:f:p:hr" opt; do
  case $opt in
    t) duration=$OPTARG ;;
    i) ip_address=$OPTARG ;;
    f) text_file=$OPTARG ;;
    p) interval=$OPTARG ;;
    r) reset_config=true ;;
    h) show_help; exit 0 ;;
    \?) show_help; exit 1 ;;
  esac
done

# Handle reset configuration file option
if [ "$reset_config" = true ]; then
  create_default_config
  echo "Configuration file has been reset to default values."
  exit 0
fi

# Create necessary directories
mkdir -p $results_folder
mkdir -p $plots_folder
mkdir -p $log_folder

# Get the current date and time in a more user-friendly format
current_date=$(date +%Y-%m-%d_%H-%M-%S)
log_file="$log_folder/monitor_ping_$current_date.log"

# Log function
log() {
  echo "$(date +%Y-%m-%d_%H-%M-%S) - $1" | tee -a $log_file
}

log "Script started"

# Check for conflicting options
if [ -n "$text_file" ]; then
  if [ -n "$duration" ] || [ -n "$ip_address" ]; then
    log "Warning: Ignoring -t and -i options because a file was provided with -f"
  fi
fi

log "Parsed arguments: duration=$duration, ip_address=$ip_address, text_file=$text_file, interval=$interval"

# Define the filename for the ping results
results_file="$results_folder/ping_results_$current_date.txt"

# Function to draw progress bar
draw_progress_bar() {
  local progress=$1
  local total_width=50
  local complete_width=$((progress * total_width / 100))
  local incomplete_width=$((total_width - complete_width))

  # Colors (using ANSI escape codes)
  local green="\033[42m"
  local red="\033[41m"
  local reset="\033[0m"

  # Create progress bar with color
  local bar=""
  for ((i=0; i<complete_width; i++)); do
    bar="${bar}${green} ${reset}"
  done
  for ((i=0; i<incomplete_width; i++)); do
    bar="${bar}${red} ${reset}"
  done

  printf "\rProgress: [${bar}] %d%%" "$progress"
}

# If a text file is provided, use it, otherwise run the ping command
if [ -n "$text_file" ]; then
  cp "$text_file" "$results_file"
  log "Copied text file $text_file to $results_file"
else
  log "Running ping command: ping -i $interval -w $duration $ip_address"
  ping -i $interval -w $duration $ip_address > $results_file &
  ping_pid=$!

  # Track progress
  start_time=$(date +%s)
  while kill -0 $ping_pid 2> /dev/null; do
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    progress=$((elapsed_time * 100 / duration))

    draw_progress_bar $progress
    sleep 1
  done

  # Final progress update to 100%
  draw_progress_bar 100
  echo

  # Wait for ping to complete
  wait $ping_pid
  echo -e "\nPing command completed."

  # Extract packet loss information and append to results file
  packet_loss=$(grep -oP '\d+(?=% packet loss)' $results_file | tail -1)
  echo "Packet Loss: $packet_loss%" >> $results_file
  log "Packet loss information appended to results file"
fi

# Run the Python script to generate the plots
log "Running Python script to generate plots"
python3 generate_plots.py $results_file $plots_folder $duration $ip_address $interval 2>&1 | tee -a $log_file
log "Python script completed"
