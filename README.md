# DesignSafe API (dapi)

[![build and test](https://github.com/DesignSafe-CI/dapi/actions/workflows/build-test.yml/badge.svg)](https://github.com/DesignSafe-CI/dapi/actions/workflows/build-test.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)
[![PyPI version](https://badge.fury.io/py/dapi.svg)](https://badge.fury.io/py/dapi)
[![Docs](https://img.shields.io/badge/view-docs-8A2BE2?color=8A2BE2)](https://designsafe-ci.github.io/dapi/)

`dapi` is a Python library for submitting, running, and monitoring [TAPIS v3](https://tapis.readthedocs.io/en/latest/) jobs on [DesignSafe](https://designsafe-ci.org) via [Jupyter Notebooks](https://jupyter.designsafe-ci.org) or the command line.

<img src="https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/dapi.png" alt="dapi" width="300">

## Features

### Jobs
- Generate TAPIS v3 job requests with automatic app parameter mapping
- Submit, monitor (with progress bars), and manage jobs
- Access and download job outputs
- Discover and explore available DesignSafe applications

### TMS Credentials
- Establish, check, and revoke SSH keys on TACC execution systems (Frontera, Stampede3, LS6)
- Works from any environment -- DesignSafe JupyterHub, command line, CI/CD

### Files
- Translate DesignSafe paths (`/MyData`, `/CommunityData`, `/projects`) to TAPIS URIs
- Upload, download, and list files on DesignSafe storage

### Database
Connects to SQL databases on DesignSafe:

| Database | dbname | env_prefix |
|----------|--------|------------|
| NGL | `ngl`| `NGL_` |
| Earthquake Recovery | `eq` | `EQ_` |
| Vp | `vp` | `VP_` |

Define the following environment variables:
```
{env_prefix}DB_USER
{env_prefix}DB_PASSWORD
{env_prefix}DB_HOST
{env_prefix}DB_PORT
```

For e.g., to add the environment variable `NGL_DB_USER` edit `~/.bashrc`, `~/.zshrc`, or a similar shell-specific configuration file for the current user and add `export NGL_DB_USER="dspublic"`.

## Installation

```shell
pip install dapi
```

To install the development version:

```shell
pip install git+https://github.com/DesignSafe-CI/dapi.git@dev --quiet
```

In Jupyter notebooks:

```python
%pip install dapi --quiet
```

To test the latest dev branch in a notebook:

```python
%pip uninstall dapi --yes
%pip install git+https://github.com/DesignSafe-CI/dapi.git@dev --quiet
```

For local development (editable install — changes to source are reflected immediately):

```shell
pip install -e .
```

## Quick Start

### Authentication

Create a `.env` file with your DesignSafe credentials:

```shell
DESIGNSAFE_USERNAME=your_username
DESIGNSAFE_PASSWORD=your_password
```

### Setup and submit a job

```python
from dapi import DSClient

# Authenticate
client = DSClient()

# Establish TMS credentials (one-time per system)
client.systems.establish_credentials("frontera")

# Submit a job
job_request = client.jobs.generate(
    app_id="matlab-r2023a",
    input_dir_uri="/MyData/analysis/input/",
    script_filename="run_analysis.m",
    max_minutes=30,
    allocation="your_allocation"
)
job = client.jobs.submit(job_request)
final_status = job.monitor()
```

### Database

```python
from dapi import DSClient

client = DSClient()
df = client.db.ngl.read_sql("SELECT * FROM SITE LIMIT 10")
print(df)
```

## Support

For any questions, issues, or feedback submit an [issue](https://github.com/DesignSafe-CI/dapi/issues/new).

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```shell
uv venv
uv pip install -e ".[dev]"
```

Run tests:
```shell
pytest tests/ -v
```

Build the package:
```shell
uv build
```

### Documentation

Documentation uses [Jupyter Book v2](https://mystmd.org). To build and serve locally:

```shell
uv pip install -e ".[docs]"
jupyter-book start
```

## License

`dapi` is licensed under the [MIT License](LICENSE.md).

## Authors

- Prof. Krishna Kumar, University of Texas at Austin
- Prof. Pedro Arduino, University of Washington
- Prof. Scott Brandenberg, University of California Los Angeles
