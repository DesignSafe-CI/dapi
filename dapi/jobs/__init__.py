"""
`dapi` job submodule simplifies the process of submitting, running, and monitoring [TAPIS v2 / AgavePy](https://agavepy.readthedocs.io/en/latest/index.html) jobs on [DesignSafe](https://designsafe-ci.org) via [Jupyter Notebooks](https://jupyter.designsafe-ci.org).


## Features

* Simplified TAPIS v2 Calls: No need to fiddle with complex API requests. `dapi` abstracts away the complexities.

* Seamless Integration with DesignSafe Jupyter Notebooks: Launch DesignSafe applications directly from the Jupyter environment.

## Installation

```shell
pip3 install dapi
```

"""
from .dir import get_ds_path_uri
from .jobs import get_status, runtime_summary, generate_job_info, get_archive_path
