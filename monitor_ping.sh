#!/bin/bash

# Default values
duration=10800  # 3 hours in seconds
ip_address="8.8.8.8"
text_file=""

# Parse arguments
while getopts "t:i:f:" opt; do
  case $opt in
    t) duration=$OPTARG ;;
    i) ip_address=$OPTARG ;;
    f) text_file=$OPTARG ;;
    \?) echo "Invalid option -$OPTARG" >&2 ;;
  esac
done

# Check for conflicting options
if [ -n "$text_file" ]; then
  if [ -n "$duration" ] || [ -n "$ip_address" ]; then
    echo "Warning: Ignoring -t and -i options because a file was provided with -f"
  fi
fi

# Get the current date and time
current_date=$(date +%Y-%m-%d_%H-%M-%S)

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
else
  # Run the ping command for the specified duration and save the results
  ping -i 1 -w $duration $ip_address > $results_file
fi

# Run the Python script to generate the plots
python3 generate_plots.py $results_file $plots_folder $duration $ip_address
