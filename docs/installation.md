# Installation

This guide will help you install the DesignSafe API (dapi) package and set up your environment.

## Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **DesignSafe Account**: Required for authentication ([sign up here](https://www.designsafe-ci.org/account/register/))

## Installation Methods

### 📦 Install from PyPI (Recommended)

The easiest way to install dapi is using pip:

```bash
pip install dapi
```

### 🔄 Install Latest Development Version

To get the latest features and bug fixes:

```bash
pip install git+https://github.com/DesignSafe-CI/dapi.git
```

### 🛠️ Install for Development

If you want to contribute to dapi or modify the source code:

```bash
# Clone the repository
git clone https://github.com/DesignSafe-CI/dapi.git
cd dapi

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies and dapi in editable mode
virtualenv env && source env/bin/activate
poetry install
```

You can also install an editable local version of dapi
```
pip install -e .
```


## 🏗️ DesignSafe Jupyter Environment

### Installing on DesignSafe Jupyter Hub

If you're using [DesignSafe Jupyter](https://jupyter.designsafe-ci.org/), install dapi in your notebook:

```python
# Remove any previous installations (optional)
!pip uninstall dapi -y

# Install the latest version
!pip install dapi --quiet

# Restart kernel after installation
# Kernel >> Restart Kernel (in Jupyter menu)
```

!!! tip "Kernel Restart Required"
    After installing dapi in a Jupyter notebook, you must restart the kernel for the changes to take effect. Go to **Kernel → Restart Kernel** in the Jupyter menu.

### Persistent Installation

For a persistent installation across Jupyter sessions:

```bash
# SSH into your DesignSafe workspace terminal
pip install --user dapi
```

## 🔧 Dependencies

dapi automatically installs the following key dependencies:

- **tapipy**: TAPIS v3 Python SDK
- **pandas**: Data manipulation and analysis
- **sqlalchemy**: Database connections
- **pymysql**: MySQL database connector
- **tqdm**: Progress bars
- **python-dotenv**: Environment variable management

## ✅ Verify Installation

Test your installation by importing dapi:

```python
import dapi
print(f"dapi version: {dapi.__version__}")

# List available functions
print("Available functions:")
print(dir(dapi))
```

Expected output:
```
dapi version: 1.1.0
Available functions:
['DSClient', 'SubmittedJob', 'interpret_job_status', ...]
```

## 🐍 Python Environment Management

### Using Virtual Environments

It's recommended to use virtual environments to avoid conflicts:

```bash
# Create virtual environment
python -m venv dapi-env

# Activate (Linux/macOS)
source dapi-env/bin/activate

# Activate (Windows)
dapi-env\Scripts\activate

# Install dapi
pip install dapi
```

### Using Conda

```bash
# Create conda environment
conda create -n dapi-env python=3.10

# Activate environment
conda activate dapi-env

# Install dapi
pip install dapi
```

## 🚨 Troubleshooting

### Common Installation Issues

#### Permission Errors
If you encounter permission errors:
```bash
pip install --user dapi
```

#### SSL Certificate Errors
If you encounter SSL issues:
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org dapi
```

#### Version Conflicts
If you have conflicting dependencies:
```bash
pip install dapi --force-reinstall
```

### Platform-Specific Issues

#### Windows
- Ensure you have Microsoft Visual C++ Build Tools installed
- Use Anaconda/Miniconda for easier dependency management

#### macOS
- Install Xcode Command Line Tools: `xcode-select --install`
- Consider using Homebrew for Python: `brew install python`

#### Linux
- Install development packages: `sudo apt-get install python3-dev build-essential`

## 🔄 Updating

### Update to Latest Version
```bash
pip install --upgrade dapi
```

### Check Current Version
```python
import dapi
print(dapi.__version__)
```

## 🆘 Getting Help

If you encounter issues during installation:

1. **Check the [Issues page](https://github.com/DesignSafe-CI/dapi/issues)** for known problems
2. **Search existing issues** before creating a new one
3. **Provide details** when reporting issues:
   - Operating system and version
   - Python version
   - Complete error messages
   - Installation method used

## ➡️ Next Steps

After successful installation:

1. **[Set up authentication](authentication.md)** with your DesignSafe credentials
2. **[Try the quick start guide](quickstart.md)** for your first dapi workflow
3. **[Explore examples](examples/mpm.md)** to see dapi in action