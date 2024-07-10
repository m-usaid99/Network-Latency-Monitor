#!/bin/bash

# Default values
duration=10800  # 3 hours in seconds
ip_address="8.8.8.8"
text_file=""
log_file=""

show_help() {
  echo "Usage: $0 [-t duration] [-i ip_address] [-f text_file]"
  echo
  echo "Options:"
  echo "  -t duration    Duration of the ping monitoring in seconds (default: 10800 seconds)"
  echo "  -i ip_address  IP address to ping (default: 8.8.8.8)"
  echo "  -f text_file   Path to an existing text file with ping results"
  echo "  -h             Show this help message and exit"
}

# Parse arguments
while getopts "t:i:f:h" opt; do
  case $opt in
    t) duration=$OPTARG ;;
    i) ip_address=$OPTARG ;;
    f) text_file=$OPTARG ;;
    h) show_help; exit 0 ;;
    \?) show_help; exit 1 ;;
  esac
done

# Get the current date and time in a more user-friendly format
current_date=$(date +%Y-%m-%d_%H-%M-%S)
log_file="logs/monitor_ping_$current_date.log"
mkdir -p logs

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

log "Parsed arguments: duration=$duration, ip_address=$ip_address, text_file=$text_file"

# Create directories for results and plots
results_folder="results"
plots_folder="plots/plots_$current_date"
mkdir -p $results_folder
mkdir -p $plots_folder

# Define the filename for the ping results
results_file="$results_folder/ping_results_$current_date.txt"

# If a text file is provided, use it, otherwise run the ping command
if [ -n "$text_file" ]; then
  cp "$text_file" "$results_file"
  log "Copied text file $text_file to $results_file"
else
  log "Running ping command: ping -i 1 -w $duration $ip_address"
  ping -i 1 -w $duration $ip_address > $results_file
  log "Ping command completed and results saved to $results_file"
fi

# Run the Python script to generate the plots
log "Running Python script to generate plots"
python3 generate_plots.py $results_file $plots_folder $duration $ip_address 2>&1 | tee -a $log_file
log "Python script completed"
