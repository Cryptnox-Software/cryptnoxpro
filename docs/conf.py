# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath(".."))

project = 'cryptnoxpro'
copyright = '2025, Cryptnox'
author = 'Cryptnox'
release = '2.9.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_mock_imports = [
    'winsdk',
    'cryptnoxpy',
    'boto3',
    'botocore',
    'cryptography',
    'stdiomask',
    'tabulate',
    'requests',
    'web3',
    'eth_typing',
    'eth_account',
    'eth_account.transactions',
    'eth_account.account',
    'eth_account._utils',
    'eth_account.datastructures',
    'pydantic',
    'pydantic_core',
    'eth_utils',
    'hexbytes',
    'enums',
    'config'
]

# Handle ambiguous cross-references
nitpicky = False
nitpick_ignore = [
    ('py:class', 'Command'),
    ('py:class', 'Cards'),
]

# Suppress specific warnings
suppress_warnings = [
    'ref.python',
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

# Custom CSS and JS
html_css_files = [
    'custom.css',
]

html_js_files = [
    'custom.js',
]

# Theme options
html_theme_options = {
    'analytics_id': '',  # Provided by Google Analytics
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}
