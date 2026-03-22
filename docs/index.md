# DAPI - DesignSafe API

[![build and test](https://github.com/DesignSafe-CI/dapi/actions/workflows/build-test.yml/badge.svg)](https://github.com/DesignSafe-CI/dapi/actions/workflows/build-test.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/DesignSafe-CI/dapi/blob/main/LICENSE.md)
[![PyPI version](https://badge.fury.io/py/dapi.svg)](https://badge.fury.io/py/dapi)

`dapi` is a Python library for submitting, monitoring, and managing [TAPIS v3](https://tapis.readthedocs.io/en/latest/) jobs on [DesignSafe](https://designsafe-ci.org) via [Jupyter Notebooks](https://jupyter.designsafe-ci.org) or the command line. It also provides access to DesignSafe research databases.

<img src="https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/dapi.png" alt="dapi" width="300">

```python
from dapi import DSClient

# Initialize client (handles authentication automatically)
ds = DSClient()

# Submit a job
job_request = ds.jobs.generate(
 app_id="matlab-r2023a",
 input_dir_uri="/MyData/analysis/input/",
 script_filename="run_analysis.m"
)
job = ds.jobs.submit(job_request)

# Monitor progress
final_status = job.monitor()

# Query research databases
df = ds.db.ngl.read_sql("SELECT * FROM SITE LIMIT 10")
```

## Getting Started

- [Installation](installation.md)
- [Authentication](authentication.md)
- [Quick Start](quickstart.md)

## User Guide

- [Jobs](jobs.md) -- submit and monitor computational jobs
- [Database Access](database.md) -- query DesignSafe research databases

## Examples

- [MPM Job Submission](examples/mpm.md)
- [PyLauncher Parameter Sweeps](examples/pylauncher.md)
- [Database Queries](examples/database.md)

## Support

Report bugs or request features on [GitHub Issues](https://github.com/DesignSafe-CI/dapi/issues).

## License

MIT License ([view](https://github.com/DesignSafe-CI/dapi/blob/main/LICENSE.md))
