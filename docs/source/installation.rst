============================
Installation
============================

You can install **NLM** (Network Latency Monitor) using `pip` from PyPI. 

**Installation via pip**

.. code-block:: bash
  
    pip install network-latency-monitor

Install from Source
============================

To install **NLM** from source, follow these steps:

**Prerequisites**

- Python 
- Poetry

1. **Clone the Repository**

  .. code-block:: bash

    git clone https://github.com/yourusername/network-latency-monitor.git
    cd network-latency-monitor

2. **Install Dependencies with Poetry**

  .. code-block:: bash
  
    poetry install

3. **Activate the Virtual Environment**
   
  .. code-block:: bash
    
    poetry shell

4. **Verify Installation**

  .. code-block:: bash
    
    poetry shell
    poetry run nlm --help


4. **Build the Documentation (Optional)**

  .. code-block:: bash

    cd docs
    make html

5. **View the Documentation**

   Open `docs/build/html/index.html` in your web browser
