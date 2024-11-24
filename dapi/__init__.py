"""
dapi` is a library that simplifies the process of submitting, running, and monitoring [TAPIS v3](https://tapis.readthedocs.io/en/latest/) jobs on [DesignSafe](https://designsafe-ci.org) via [Jupyter Notebooks](https://jupyter.designsafe-ci.org).

## Features

### Jobs

* Get TAPIS v3 templates for jobs: No need to fiddle with complex API requests. `dapi` abstracts away the complexities.

* Seamless Integration with DesignSafe Jupyter Notebooks: Launch DesignSafe applications directly from the Jupyter environment.

### Database

Connects to SQL databases on DesignSafe:

| Database | dbname | env_prefix |
|----------|--------|------------|
| NGL | `ngl`| `NGL_` |
| Earthake Recovery | `eq` | `EQ_` |
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
pip3 install dapi
```

"""
# from . import apps
# from . import auth
# from . import db
# from . import jobs

from .core import DesignSafeAPI

__all__ = ["DesignSafeAPI", "apps", "auth", "db", "jobs", "core"]
