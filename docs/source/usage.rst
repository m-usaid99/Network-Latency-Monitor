============================
Usage
============================

After installing **NLM**, you can start monitoring network latency.


Configuration
============================

Before running NLM, configure your settings in the `config.yaml` file.

**Sample `config.yaml`:**

.. code-block:: yaml

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


Running the Program
============================

**Running from Source**

If you have installed from source using `poetry`, then you can run the program using `poetry run`.

To run the program with all default parameters (as obtained from `config.yaml`):
  .. code-block:: bash

    poetry run nlm

**Running from Pip Installation**

If you are running the program after installing it through `pip`, you can run it simply by:

  .. code-block:: bash

    nlm

This will run the program with default parameters as obtained from `config.yaml`.
