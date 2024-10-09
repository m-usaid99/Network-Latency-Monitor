# NLM: Network Latency Monitor

![Build Status](https://github.com/m-usaid99/Network-Latency-Monitor/actions/workflows/ci.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/network-latency-monitor.svg)](https://pypi.org/project/network-latency-monitor/)
[![Python Versions](https://img.shields.io/pypi/pyversions/network-latency-monitor.svg)](https://pypi.org/project/network-latency-monitor/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

NLM is a tool designed to monitor network latency across specified IP
addresses, providing real-time feedback through progress bars and
latency graphs.

It also collects data, and plots graphs using `seaborn` to visualize latency data.
Real-time charts are drawn in the terminal using `asciichartpy`.

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

### Installation via pip

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

After installing **NLM**, you can start monitoring network latency.

## Usage

### Configuration

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

## Contributing

Contributions are welcome! If you have suggestions for new features, bug fixes, or improvements, feel free to open an issue or submit a pull request.

### How to Contribute

1. **Fork the repository** to your GitHub account.

2. **Clone your fork** locally:

   ```bash
   git clone https://github.com/yourusername/network-latency-monitor.git
   cd network-latency-monitor
   ```

3. Monitor a single IP for 2 hours, with default settings:

   ```bash
   git checkout -b feature-branch-name
   ```

4. Make your changes and ensure the code passes any pre-existing tests or linters.

5. Push your changes to your forked repository:

   ```bash
   git push origin feature-branch-name
   ```

6. Submit a pull request to the `main` branch.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.

## Roadmap

The following features and improvements are planned for future releases of **NLM (Network Latency Monitor)**:

1. **Improve `argparse` Functionality**:

   - Add Verbosity Levels: Introduce options to control output verbosity (e.g., `-v` for verbose mode, `-q` for quiet mode).
   - Enhanced Error Handling: Improve feedback and error reporting for invalid inputs or failed pings.

    <br/>

2. **Add Support for Multiple Protocols**: Extend support for protocols beyond ICMP (e.g., TCP, UDP) to enable more comprehensive network monitoring.

3. **Data Export Options**: Allow users to export monitoring data in multiple formats such as CSV, JSON, and XML for easier data processing and analysis.

4. **Custom Results and Plots Directory**:
   Add command-line options to specify custom directories for storing results and plots, making the tool more flexible for use in shell scripts and automated environments.

5. **Improved Plotting Options** (Future): Enhance plotting capabilities with customizable graph styles, better scaling, and export options to PNG and other formats.

## Support

If you encounter any issues, feel free to open an issue on [GitHub Issues](https://github.com/m-usaid99/Network-Latency-Monitor/issues).

## Acknowledgments

- [asciichartpy](https://github.com/kroitor/asciichart) for the ASCII-based chart rendering.
- [Poetry](https://python-poetry.org/) for Python packaging and dependency management.

## Documentation

Full documentation for **NLM (Network Latency Monitor)** is available at [Read the Docs](https://network-latency-monitor.readthedocs.io/en/latest/).

The documentation includes:

- **Installation Instructions**: Step-by-step guide for installing the tool.
- **Usage Examples**: Detailed usage examples and advanced configurations.
- **API Reference**: Auto-generated API reference from code docstrings.

For detailed information, visit the [NLM Documentation](https://network-latency-monitor.readthedocs.io/en/latest/).
