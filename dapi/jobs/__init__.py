"""
`dapi` job submodule simplifies the process of submitting, running, and monitoring [Tapis v3](https://tapis.readthedocs.io/en/latest/) jobs on [DesignSafe](https://designsafe-ci.org) via [Jupyter Notebooks](https://jupyter.designsafe-ci.org).


## Features

* Simplified TAPIS v3 Calls: No need to fiddle with complex API requests. `dapi` abstracts away the complexities.

* Seamless Integration with DesignSafe Jupyter Notebooks: Launch DesignSafe applications directly from the Jupyter environment.

# Installation

```shell
pip3 install dapi
```

"""
from .dir import get_ds_path_uri
from .jobs import get_status, runtime_summary, generate_job_info
