#!/bin/bash

# Function to show help message
show_help() {
  echo "Usage: $0 [-t duration_in_seconds] [-p ping_interval] [-f file_to_ping_results.txt] [--no-aggregation] [-c [all|results|plots|logs]] [-P] [-R] [-L] [-h] [ip_address ...]"
  echo
  echo "Options:"
  echo "  -t duration_in_seconds  The amount of time to collect data for, in seconds. Default: 10800 seconds (3 hours)"
  echo "  -p ping_interval        The interval between each ping in seconds. Default: 1 second"
  echo "  -f file_to_ping_results.txt  Path to an existing text file with ping results"
  echo "  --no-aggregation        Disable data aggregation"
  echo "  -c [all|results|plots|logs] Clear specified data (with confirmation)"
  echo "    all                   Clear all results, plots, and logs"
  echo "    results               Clear all results"
  echo "    plots                 Clear all plots"
  echo "    logs                  Clear all logs"
  echo "  -P                      Clear all plots (with confirmation)"
  echo "  -R                      Clear all results (with confirmation)"
  echo "  -L                      Clear all logs (with confirmation)"
  echo "  -h                      Show this help message and exit"
  echo "  ip_address              One or more IP addresses to ping (space-separated)"
}

# Configuration file
config_file="config.yaml"

# Default configuration values
default_config=$(
  cat <<EOL
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
EOL
)

# Function to create a default configuration file
create_default_config() {
  echo "$default_config" >$config_file
  echo "Default configuration file created: $config_file"
}

# Check if configuration file exists
if [ ! -f $config_file ]; then
  echo "Configuration file not found. Creating a default configuration file."
  create_default_config
fi

# Function to read values from the YAML configuration file using Python
read_config() {
  python3 -c "
import yaml
import sys

config_file = '$config_file'
try:
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        print(config.get('$1', ''))
except FileNotFoundError:
    print(f'Error: Configuration file $config_file not found.', file=sys.stderr)
    sys.exit(1)
except yaml.YAMLError as e:
    print(f'Error parsing configuration file: $e', file=sys.stderr)
    sys.exit(1)
"
}

# Load configuration values
duration=$(read_config 'duration')
default_ip_address=$(read_config 'ip_address')
ping_interval=$(read_config 'ping_interval')
results_folder=$(read_config 'results_folder')
plots_folder=$(read_config 'plots_folder')
log_folder=$(read_config 'log_folder')

# Use default values if variables are empty
results_folder=${results_folder:-"results"}
plots_folder=${plots_folder:-"plots"}
log_folder=${log_folder:-"logs"}

# Initialize variables
no_aggregation=false

# Parse arguments
while getopts "t:p:f:hrc:P:R:L-:" opt; do
  case $opt in
  t) duration=$OPTARG ;;
  p) ping_interval=$OPTARG ;;
  f) text_file=$OPTARG ;;
  r) reset_config=true ;;
  c)
    case "$OPTARG" in
    all) clear_all=true ;;
    results) clear_results=true ;;
    plots) clear_plots=true ;;
    logs) clear_logs=true ;;
    *)
      show_help
      exit 1
      ;;
    esac
    ;;
  P) clear_plots=true ;;
  R) clear_results=true ;;
  L) clear_logs=true ;;
  -)
    case "${OPTARG}" in
    no-aggregation) no_aggregation=true ;;
    *)
      show_help
      exit 1
      ;;
    esac
    ;;
  h)
    show_help
    exit 0
    ;;
  \?)
    show_help
    exit 1
    ;;
  esac
done

# Remaining arguments are the IP addresses
shift $((OPTIND - 1))
ip_addresses=("$@")

# Use default IP address if none provided
if [ ${#ip_addresses[@]} -eq 0 ]; then
  ip_addresses=("$default_ip_address")
fi

# Handle reset configuration file option
if [ "$reset_config" = true ]; then
  create_default_config
  echo "Configuration file has been reset to default values."
  exit 0
fi

# Function to confirm action
confirm() {
  read -p "Are you sure you want to $1? (y/n): " choice
  case "$choice" in
  y | Y) return 0 ;;
  *) return 1 ;;
  esac
}

# Function to clear results
clear_results() {
  rm -rf "$results_folder"/*
  echo "All results have been cleared."
}

# Function to clear plots
clear_plots() {
  rm -rf "$plots_folder"/*
  echo "All plots have been cleared."
}

# Function to clear logs
clear_logs() {
  rm -rf "$log_folder"/*
  echo "All logs have been cleared."
}

# Handle clear options with confirmation
if [ "$clear_all" = true ]; then
  if confirm "clear all results, plots, and logs"; then
    clear_results
    clear_plots
    clear_logs
  else
    echo "Operation cancelled."
  fi
  exit 0
fi

if [ "$clear_results" = true ]; then
  if confirm "clear all results"; then
    clear_results
  else
    echo "Operation cancelled."
  fi
  exit 0
fi

if [ "$clear_plots" = true ]; then
  if confirm "clear all plots"; then
    clear_plots
  else
    echo "Operation cancelled."
  fi
  exit 0
fi

if [ "$clear_logs" = true ]; then
  if confirm "clear all logs"; then
    clear_logs
  else
    echo "Operation cancelled."
  fi
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
  if [ -n "$duration" ] || [ -n "$ip_addresses" ]; then
    log "Warning: Ignoring -t and -i options because a file was provided with -f"
  fi
fi

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
  for ((i = 0; i < complete_width; i++)); do
    bar="${bar}${green} ${reset}"
  done
  for ((i = 0; i < incomplete_width; i++)); do
    bar="${bar}${red} ${reset}"
  done

  printf "\rProgress: [${bar}] %d%%" "$progress"
}

# Run ping for each IP address concurrently
for ip in "${ip_addresses[@]}"; do
  results_file="$results_folder/ping_results_${ip}_$current_date.txt"
  log "Running ping for IP: $ip"
  ping -i $ping_interval -w $duration $ip >"$results_file" &
  pids+=($!)
done

# Track progress
start_time=$(date +%s)
while :; do
  sleep 1
  current_time=$(date +%s)
  elapsed_time=$((current_time - start_time))
  progress=$((elapsed_time * 100 / duration))

  # Draw progress bar
  draw_progress_bar $progress

  all_done=true
  for pid in "${pids[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      all_done=false
    fi
  done
  [[ "$all_done" = true ]] && break
done

# Final progress update to 100%
draw_progress_bar 100
echo

# Wait for all background pings to complete
wait

log "All ping commands completed"

# Check if results files are empty
for ip in "${ip_addresses[@]}"; do
  results_file="$results_folder/ping_results_${ip}_$current_date.txt"
  if [ ! -s "$results_file" ]; then
    log "Error: Results file for IP $ip is empty or not found."
    exit 1
  fi
done

# Determine if no aggregation should be forced based on duration
if [ "$duration" -lt 60 ]; then
  no_aggregation=true
fi

# Expand the glob pattern to get all result files
result_files=$(echo "${results_folder}/ping_results_*_$current_date.txt")

# Run the Python script to generate plots
log "Running Python script to generate plots"
if ! python3 generate_plots.py $result_files "$plots_folder" $([ "$no_aggregation" = true ] && echo "--no-aggregation") 2>&1 | tee -a $log_file; then
  log "Error: Python script failed to generate plots."
  exit 1
fi
log "Python script completed"
