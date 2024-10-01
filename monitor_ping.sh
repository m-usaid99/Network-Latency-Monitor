#!/bin/bash

set -e

# Function to show help message
show_help() {
  echo "Usage: $0 [-t duration_in_seconds] [-p ping_interval] [-f file_to_ping_results.txt] [--no-aggregation] [-c [all|results|plots|logs]] [-h] [ip_address ...]"
  echo
  echo "Options:"
  echo "  -t duration_in_seconds     Duration to collect data (default: 10800 seconds)"
  echo "  -p ping_interval           Interval between each ping in seconds (default: 1 second)"
  echo "  -f file_to_ping_results.txt Path to an existing text file with ping results"
  echo "  --no-aggregation           Disable data aggregation"
  echo "  -c [all|results|plots|logs] Clear specified data (with confirmation)"
  echo "  -h                         Show this help message and exit"
  echo "  ip_address                 One or more IP addresses to ping (space-separated)"
}

# Default configuration file
CONFIG_FILE="config.yaml"

# Check if yq is installed
if ! command -v yq &>/dev/null; then
  echo "yq is required but not installed. Please install yq to proceed."
  exit 1
fi

# Function to create default configuration
create_default_config() {
  cat <<EOL >"$CONFIG_FILE"
# Default configuration values

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
  method: "mean"
  interval: 60

segmentation:
  hourly: true

results_folder: "results"
plots_folder: "plots"
log_folder: "logs"
EOL
  echo "Default configuration file created: $CONFIG_FILE"
}

# Create default config if not exists
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Configuration file not found. Creating a default configuration file."
  create_default_config
fi

# Function to read configuration using yq
read_config() {
  yq eval ".$1" "$CONFIG_FILE"
}

# Load configuration values
duration=$(read_config 'duration')
default_ip_address=$(read_config 'ip_address')
ping_interval=$(read_config 'ping_interval')
results_folder=$(read_config 'results_folder')
plots_folder=$(read_config 'plots_folder')
log_folder=$(read_config 'log_folder')

# Set default values if not set
results_folder=${results_folder:-"results"}
plots_folder=${plots_folder:-"plots"}
log_folder=${log_folder:-"logs"}

# Initialize variables
no_aggregation=false
file_mode=false

# Variables for clearing
clear_all=false
clear_results=false
clear_plots=false
clear_logs=false

# Parse arguments
ARGS=$(getopt -o t:p:f:c:h -l no-aggregation -- "$@")
if [ $? -ne 0 ]; then
  show_help
  exit 1
fi

eval set -- "$ARGS"

while true; do
  case "$1" in
  -t)
    duration="$2"
    shift 2
    ;;
  -p)
    ping_interval="$2"
    shift 2
    ;;
  -f)
    text_file="$2"
    file_mode=true
    shift 2
    ;;
  --no-aggregation)
    no_aggregation=true
    shift
    ;;
  -c)
    case "$2" in
    all)
      clear_all=true
      ;;
    results)
      clear_results=true
      ;;
    plots)
      clear_plots=true
      ;;
    logs)
      clear_logs=true
      ;;
    *)
      echo "Invalid option for -c: $2"
      show_help
      exit 1
      ;;
    esac
    shift 2
    ;;
  -h)
    show_help
    exit 0
    ;;
  --)
    shift
    break
    ;;
  *)
    break
    ;;
  esac
done

# Remaining arguments are IP addresses
ip_addresses=("$@")

# Use default IP if none provided
if [ ${#ip_addresses[@]} -eq 0 ]; then
  ip_addresses=("$default_ip_address")
fi

# Function to confirm action
confirm() {
  read -p "Are you sure you want to $1? (y/n): " choice
  case "$choice" in
  y | Y) return 0 ;;
  *) return 1 ;;
  esac
}

# Functions to clear data
clear_all_data() {
  if confirm "clear all results, plots, and logs"; then
    rm -rf "${results_folder:?}/"*
    rm -rf "${plots_folder:?}/"*
    rm -rf "${log_folder:?}/"*
    echo "All results, plots, and logs have been cleared."
  else
    echo "Operation cancelled."
  fi
}

clear_specific_data() {
  local type="$1"
  if confirm "clear all $type"; then
    case "$type" in
    results)
      rm -rf "${results_folder:?}/"*
      echo "All results have been cleared."
      ;;
    plots)
      rm -rf "${plots_folder:?}/"*
      echo "All plots have been cleared."
      ;;
    logs)
      rm -rf "${log_folder:?}/"*
      echo "All logs have been cleared."
      ;;
    esac
  else
    echo "Operation cancelled."
  fi
}

# Handle clearing options
if [ "$clear_all" = true ]; then
  clear_all_data
  exit 0
fi

if [ "$clear_results" = true ]; then
  clear_specific_data "results"
  exit 0
fi

if [ "$clear_plots" = true ]; then
  clear_specific_data "plots"
  exit 0
fi

if [ "$clear_logs" = true ]; then
  clear_specific_data "logs"
  exit 0
fi

# Create necessary directories
mkdir -p "$results_folder" "$plots_folder" "$log_folder"

# Get current timestamp
current_date=$(date +%Y-%m-%d_%H-%M-%S)
log_file="$log_folder/monitor_ping_$current_date.log"

# Log function
log() {
  echo "$(date +%Y-%m-%d_%H-%M-%S) - $1" | tee -a "$log_file"
}

log "Script started"

# If file mode is enabled, process the file directly
if [ "$file_mode" = true ]; then
  log "File mode enabled. Processing file(s) directly with Python script."
  python3 generate_plots.py "$text_file" "$plots_folder" ${no_aggregation:+--no-aggregation} 2>&1 | tee -a "$log_file"
  log "Python script completed"
  exit 0
fi

# Run ping for each IP address concurrently
declare -a pids
for ip in "${ip_addresses[@]}"; do
  results_file="$results_folder/ping_results_${ip}_${current_date}.txt"
  log "Starting ping for IP: $ip (Duration: $duration seconds, Interval: $ping_interval seconds)"
  ping -i "$ping_interval" -w "$duration" "$ip" >"$results_file" &
  pids+=($!)
done

# Function to draw progress bar
draw_progress_bar() {
  local elapsed=$1
  local total=$2
  local percent=$((elapsed * 100 / total))
  local filled=$((percent / 2))
  local empty=$((50 - filled))
  printf "\rProgress: ["
  printf "%0.s#" $(seq 1 $filled)
  printf "%0.s-" $(seq 1 $empty)
  printf "] %d%%" "$percent"
}

# Track progress
start_time=$(date +%s)
while true; do
  sleep 1
  current_time=$(date +%s)
  elapsed=$((current_time - start_time))
  if [ "$elapsed" -ge "$duration" ]; then
    elapsed="$duration"
  fi
  draw_progress_bar "$elapsed" "$duration"

  # Check if all pings are done
  all_done=true
  for pid in "${pids[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      all_done=false
      break
    fi
  done
  if [ "$all_done" = true ]; then
    break
  fi
done
echo

# Wait for all background pings to complete
wait

log "All ping commands completed."

# Validate results files
for ip in "${ip_addresses[@]}"; do
  results_file="$results_folder/ping_results_${ip}_${current_date}.txt"
  if [ ! -s "$results_file" ]; then
    log "Error: Results file for IP $ip is empty or not found."
    exit 1
  fi
done

# Determine if aggregation should be disabled based on duration
if [ "$duration" -lt 60 ]; then
  no_aggregation=true
fi

# Gather all result files
result_files=()
for ip in "${ip_addresses[@]}"; do
  result_files+=("$results_folder/ping_results_${ip}_${current_date}.txt")
done

# Run the Python script to generate plots
log "Running Python script to generate plots."
python3 generate_plots.py "${result_files[@]}" "$plots_folder" ${no_aggregation:+--no-aggregation} 2>&1 | tee -a "$log_file"
log "Python script completed."

log "Script finished successfully."
