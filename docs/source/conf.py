# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import logging

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "NLM: Network Latency Manager"
copyright = "2024, M. Usaid Rehman"
author = "M. Usaid Rehman"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

# Add the network_latency_monitor directory to sys.path
sys.path.insert(0, os.path.abspath("../../"))

# -- Autodoc settings ---------------------------------------------------------

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": False,
    "special-members": "__init__",
    "inherited-members": True,
    "show-inheritance": True,
}

autodoc_typehints = "description"

# -- Intersphinx configuration ------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    # Add other mappings if needed, e.g.,
    # 'pandas': ('https://pandas.pydata.org/docs/', None),
}

# -- Suppress Matplotlib debug logs -------------------------------------------

logging.getLogger("matplotlib").setLevel(logging.WARNING)

