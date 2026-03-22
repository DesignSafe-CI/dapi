# Installation

## Requirements

- Python 3.10+
- A DesignSafe account ([register](https://www.designsafe-ci.org/account/register/))

## Install from PyPI

```bash
pip install dapi
```

## Install Development Version

```bash
pip install git+https://github.com/DesignSafe-CI/dapi.git@dev
```

## Install for Development

```bash
git clone https://github.com/DesignSafe-CI/dapi.git
cd dapi

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
virtualenv env && source env/bin/activate
poetry install
```

Or install an editable local copy:
```
pip install -e .
```

## DesignSafe Jupyter Hub

Install dapi in a notebook:

```python
# Remove any previous installations (optional)
!pip uninstall dapi -y

# Install the latest version
!pip install dapi --quiet

# Restart kernel after installation
# Kernel >> Restart Kernel (in Jupyter menu)
```

:::{tip} Kernel Restart Required
After installing dapi in a Jupyter notebook, restart the kernel for changes to take effect. Go to **Kernel -> Restart Kernel**.
:::

For a persistent installation across sessions:

```bash
# SSH into your DesignSafe workspace terminal
pip install --user dapi
```

## Verify Installation

```python
import dapi
print(dapi.__version__)
```

## Updating

```bash
pip install --upgrade dapi
```

## Troubleshooting

**Permission errors:**
```bash
pip install --user dapi
```

**SSL certificate errors:**
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org dapi
```

**Version conflicts:**
```bash
pip install dapi --force-reinstall
```

## Next Steps

1. [Set up authentication](authentication.md)
2. [Quick start guide](quickstart.md)
