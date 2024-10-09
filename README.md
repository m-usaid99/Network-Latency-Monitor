# NLM: Network Latency Monitor

## Introduction

Welcome to the **Network Latency Monitor (NLM)** documentation.

NLM is a tool designed to monitor network latency across specified IP
addresses, providing real-time feedback through progress bars and
latency graphs.

**Features include:**

- **Asynchronous Ping Monitoring**: Efficiently pings multiple IP
  addresses simultaneously.
- **Real-time ASCII-based Latency Graphs**: Visualizes latency data
  directly in the terminal.
- **OS-specific Directory Management**: Manages logs, results, and
  plots in OS-specific directories.
- **Comprehensive Documentation**: Generated from code docstrings for
  accuracy and consistency.

## Installation

You can install **NLM** (Network Latency Monitor) using
`pip` from PyPI.

**Installation via pip**

```bash
pip install network-latency-monitor
```

### Install from Source

To install **NLM** from source, follow these steps:

**Prerequisites**

- Python
- Poetry

1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/network-latency-monitor.git
cd network-latency-monitor
```

2. **Install Dependencies with Poetry**

```bash
 poetry install
```

3. **Activate the Virtual Environment**

```bash
poetry shell
```

4. **Verify Installation**

```bash
poetry shell
poetry run nlm --help
```

4. **Build the Documentation (Optional)**

```bash
cd docs
make html
```

5. **View the Documentation**

   Open `docs/build/html/index.html` in your web browser

## Usage

After installing **NLM**, you can start monitoring network latency.

## Configuration

Before running NLM, configure your settings in the
[config.yaml]{.title-ref} file.

**Sample `config.yaml`:**

```yaml
"duration": 10800,  # in seconds
"ip_addresses": ["8.8.8.8"],
"ping_interval": 1,  # in seconds
"latency_threshold": 200.0,  # in ms
"no_aggregation": False,
"no_segmentation": False,
"file": None,  # Optional: Specify a ping result file to process
"clear": False,  # Set to True to clear all data
"clear_results": False,  # Set to True to clear results folder
"clear_plots": False,  # Set to True to clear plots folder
"clear_logs": False,  # Set to True to clear logs folder
"yes": False,  # Set to True to auto-confirm prompts
```

The `config.yaml` file is auto-generated the first time that
the program is run. It is saved in default directories based on your
operating system.

For Linux users: `/home/username/.config/network_latency_monitor/config.yaml`
For Windows users: `%APPDATA%\nlm\config.yaml`
For MacOS users: `~/Library/Application Support/nlm/config.yaml`

## Running the Program

**Running from Source**

If you have installed from source using [poetry]{.title-ref}, then you
can run the program using [poetry run]{.title-ref}.

To run the program with all default parameters (as obtained from [config.yaml]{.title-ref}):

```bash
poetry run nlm
```

**Running from Pip Installation**

If you are running the program after installing it through
`pip`, you can run it simply by:

```bash
nlm
```

This will run the program with default parameters as obtained from
`config.yaml`.

To view all command-line options and a simple guide, run

```bash
nlm --help
```

### Usage Examples

- Monitor two IP addresses for 1 hour with a 2-second interval between pings:

  ```bash
  nlm 8.8.8.8 1.1.1.1 --duration 3600 --ping-interval 2
  ```

- Process an existing ping results file and disable data aggregation:

  ```bash
  nlm --file results/ping_results_8.8.8.8.txt --no-aggregation
  ```

- Clear all data (results, plots, logs) without confirmation:

  ```bash
  nlm --clear --yes
  ```

- Monitor a single IP address with a custom latency threshold:

  ```bash
  nlm 8.8.4.4 --latency-threshold 150.0
  ```

- Regenerate the default `config.yaml` file:

  ```bash
  nlm --regen-config
  ```

- Disable segmentation of latency plots:

  ```bash
  nlm 8.8.8.8 --no-segmentation
  ```

- Monitor a single IP for 2 hours, with default settings:

  ```bash
  nlm 8.8.8.8 --duration 7200
  ```

- Clear only the plots folder:

  ```bash
  nlm --clear-plots
  ```
