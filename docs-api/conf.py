"""Sphinx configuration for dapi API reference docs."""

project = "dapi"
copyright = "2024, Krishna Kumar, Pedro Arduino, Scott Brandenberg"
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

# Google Analytics (GA4). Furo has no analytics option, so load gtag.js
# directly. The measurement ID also appears in _static/ga4.js and in
# myst.yml (the narrative docs); keep all three in sync.
ga_measurement_id = "G-D96RT1T24K"
html_static_path = ["_static"]
html_js_files = [
    (
        f"https://www.googletagmanager.com/gtag/js?id={ga_measurement_id}",
        {"async": "async"},
    ),
    "ga4.js",
]

# Suppress warnings for missing type stubs
nitpicky = False
