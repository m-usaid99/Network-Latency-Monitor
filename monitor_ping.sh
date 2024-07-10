#!/bin/bash

# Default values
duration=10800  # 3 hours in seconds
ip_address="8.8.8.8"
text_file=""
interval=1  # Default interval for ping command
results_file="ping_results.txt"

show_help() {
  echo "Usage: $0 [-t duration_in_seconds] [-i ip_address] [-f file_to_ping_results.txt] [-p ping_interval]"
  echo
  echo "Options:"
  echo "  -t duration_in_seconds  The amount of time to collect data for, in seconds. Default: 10800 seconds (3 hours)"
  echo "  -i ip_address           The IP address to ping. Default: 8.8.8.8"
  echo "  -f file_to_ping_results.txt  Path to an existing text file with ping results"
  echo "  -p ping_interval        The interval between each ping in seconds. Default: 1 second"
  echo "  -h                      Show this help message and exit"
}

# Parse arguments
while getopts "t:i:f:p:h" opt; do
  case $opt in
    t) duration=$OPTARG ;;
    i) ip_address=$OPTARG ;;
    f) text_file=$OPTARG ;;
    p) interval=$OPTARG ;;
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

log "Parsed arguments: duration=$duration, ip_address=$ip_address, text_file=$text_file, interval=$interval"

# Create directories for results and plots
results_folder="results"
plots_folder="plots/plots_$current_date"
mkdir -p $results_folder
mkdir -p $plots_folder

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
