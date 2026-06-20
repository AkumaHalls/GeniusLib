# GeniusLib documentation build configuration file
# Sphinx >= 5.0

import os
import sys
sys.path.insert(0, os.path.abspath(".."))

import geniuslib

project = "GeniusLib"
copyright = "2026, AkumaHalls / ClashGenius"
author = "AkumaHalls"
release = geniuslib.__version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
autosummary_generate = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiohttp": ("https://docs.aiohttp.org/en/stable", None),
}

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = f"GeniusLib v{release}"

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
