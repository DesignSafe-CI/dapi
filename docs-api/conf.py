"""Sphinx configuration for dapi API reference docs."""

project = "dapi"
copyright = "2024, Krishna Kumar, Pedro Arduino, Scott Brandenberg, Silvia Mazzoni"
author = "Krishna Kumar"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

# Napoleon settings (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# Theme
html_theme = "furo"
html_title = "dapi API Reference"
html_theme_options = {
    "navigation_with_keys": True,
}

# Suppress warnings for missing type stubs
nitpicky = False
