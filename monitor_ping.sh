#!/bin/bash

# Function to show help message
show_help() {
  echo "Usage: $0 [-t duration_in_seconds] [-i ip_addresses] [-f file_to_ping_results.txt] [-p ping_interval] [--no-aggregation] [-c [all|results|plots|logs]] [-P] [-R] [-L]"
  echo
  echo "Options:"
  echo "  -t duration_in_seconds  The amount of time to collect data for, in seconds. Default: 10800 seconds (3 hours)"
  echo "  -i ip_addresses         Comma-separated list of IP addresses to ping. Default: 8.8.8.8"
  echo "  -f file_to_ping_results.txt  Path to an existing text file with ping results"
  echo "  -p ping_interval        The interval between each ping in seconds. Default: 1 second"
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
}

# Default values
duration=10800  # 3 hours in seconds
ip_addresses="8.8.8.8"
text_file=""
ping_interval=1
no_aggregation=false

# Parse arguments
while getopts "t:i:f:p:h-:c:P:R:L" opt; do
  case $opt in
    t) duration=$OPTARG ;;
    i) ip_addresses=$OPTARG ;;
    f) text_file=$OPTARG ;;
    p) ping_interval=$OPTARG ;;
    h) show_help; exit 0 ;;
    c)
      case "$OPTARG" in
        all) clear_all=true ;;
        results) clear_results=true ;;
        plots) clear_plots=true ;;
        logs) clear_logs=true ;;
        *) show_help; exit 1 ;;
      esac
      ;;
    P) clear_plots=true ;;
    R) clear_results=true ;;
    L) clear_logs=true ;;
    -)
      case "${OPTARG}" in
        no-aggregation) no_aggregation=true ;;
        *) show_help; exit 1 ;;
      esac
      ;;
    \?) show_help; exit 1 ;;
  esac
done

# Create directories for results and plots
results_folder="results"
plots_folder="plots"
log_folder="logs"
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

# Split IP addresses into an array
IFS=',' read -r -a ip_array <<< "$ip_addresses"

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

# Run ping for each IP address concurrently
for ip in "${ip_array[@]}"; do
  results_file="$results_folder/ping_results_${ip}_$current_date.txt"
  log "Running ping for IP: $ip"
  ping -i $ping_interval -w $duration $ip > "$results_file" &
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
for ip in "${ip_array[@]}"; do
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

# Run the Python script to generate plots
log "Running Python script to generate plots"
if ! python3 generate_plots.py "${results_folder}/ping_results_*_$current_date.txt" "$plots_folder" $( [ "$no_aggregation" = true ] && echo "--no-aggregation" ) 2>&1 | tee -a $log_file; then
  log "Error: Python script failed to generate plots."
  exit 1
fi
log "Python script completed"
