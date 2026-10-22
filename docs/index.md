# DAPI - DesignSafe API

[![build and test](https://github.com/DesignSafe-CI/dapi/actions/workflows/build-test.yml/badge.svg)](https://github.com/DesignSafe-CI/dapi/actions/workflows/build-test.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/DesignSafe-CI/dapi/blob/main/LICENSE.md)
[![PyPI version](https://badge.fury.io/py/dapi.svg)](https://badge.fury.io/py/dapi)

[![Open in DesignSafe](https://img.shields.io/badge/Open%20in%20DesignSafe-clone%20%2B%20open-006FBA?style=for-the-badge&logo=jupyter&logoColor=white)](https://jupyter.designsafe-ci.org/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2FDesignSafe-CI%2Fdapi&branch=main&targetpath=MyData%2Fdapi&urlpath=lab%2Ftree%2FMyData%2Fdapi%2Fexamples%2F)

One click clones this repository, with its `examples/` notebooks, into `MyData/dapi` on DesignSafe JupyterHub and opens the examples folder. Click it again later to pull updates.

`dapi` is a Python library for submitting, monitoring, and managing [TAPIS v3](https://tapis.readthedocs.io/en/latest/) jobs on [DesignSafe](https://designsafe-ci.org) via [Jupyter Notebooks](https://jupyter.designsafe-ci.org) or the command line. It also provides access to DesignSafe research databases.

<img src="https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/dapi.png" alt="dapi" width="300">

```python
from dapi import DSClient

ds = DSClient()

input_uri = ds.files.to_uri("/MyData/analysis/input/")

job_request = ds.jobs.generate(
    app_id="matlab-r2023a",
    input_dir_uri=input_uri,
    script_filename="run_analysis.m",
    allocation="your_allocation",
)
job = ds.jobs.submit(job_request)
job.monitor()
```

For background on DesignSafe compute environments, storage, and workflow design, see the [DesignSafe Workflows guide](https://designsafe-ci.github.io/ds-workflows/).

## Getting Started

- [Quick Start](quickstart.md) -- get running in 5 minutes
- [Installation](installation.md) -- install options and updates
- [Authentication](authentication.md) -- credentials and environment setup

## User Guide

- [Jobs](jobs.md) -- submit, monitor, and manage computational jobs
- [Apps](apps.md) -- find applications and their IDs
- [Files](files.md) -- path translation, upload, download
- [Projects](projects.md) -- list, inspect, and access project files
- [Publications](publications.md) -- search and access published datasets
- [Systems](systems.md) -- queues and TMS credentials
- [Database Access](database.md) -- query DesignSafe research databases

## Examples

- [Examples](examples.md) -- full worked examples with runnable notebooks

## Support

Report bugs or request features on [GitHub Issues](https://github.com/DesignSafe-CI/dapi/issues).

## License

MIT License ([view](https://github.com/DesignSafe-CI/dapi/blob/main/LICENSE.md))
