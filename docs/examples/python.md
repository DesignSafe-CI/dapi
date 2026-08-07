# Generic Python Job Submission Example

This example runs a plain Python computation on a TACC Stampede3 compute node using [`python-s3`](https://designsafe-ci.github.io/ds-workflows/apps/python), DesignSafe's general-purpose execution app — no dedicated Tapis app required. The demo estimates π by Monte Carlo sampling across all 48 cores of one SKX node with `concurrent.futures`: no MPI, no pip installs, one input file.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/python/python-s3-pi.ipynb)

For general job submission concepts, see [Jobs](../jobs.md). For resource sizing, see [DesignSafe Workflows](https://designsafe-ci.github.io/ds-workflows/guide/job-resources).

## Complete Example

### Step 1: Install and Import dapi

```python
%pip install dapi --quiet

import json
from pathlib import Path

from dapi import DSClient
```

### Step 2: Initialize Client

```python
ds = DSClient()
```

**Authentication:** dapi supports environment variables, .env files, and interactive prompts. See the [authentication guide](../authentication.md).

### Step 3: Create the Input Script

`python-s3` needs an input directory containing the main script. On DesignSafe JupyterHub, My Data is mounted at `~/MyData`:

```python
input_dir = Path.home() / "MyData" / "dapi-examples" / "pi-demo"
input_dir.mkdir(parents=True, exist_ok=True)

pi_script = '''\
"""Monte Carlo estimate of pi across all cores of one node."""
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor


def count_hits(n: int) -> int:
    rng = random.Random(os.getpid())
    return sum(rng.random() ** 2 + rng.random() ** 2 <= 1.0 for _ in range(n))


if __name__ == "__main__":
    samples = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000_000
    workers = len(os.sched_getaffinity(0))
    chunk = samples // workers
    with ProcessPoolExecutor(workers) as pool:
        hits = sum(pool.map(count_hits, [chunk] * workers))
    total = chunk * workers
    print(f"pi ~= {4 * hits / total:.6f}  ({workers} workers, {total:,} samples)")
'''

(input_dir / "pi.py").write_text(pi_script)
```

Running from a local machine instead of JupyterHub? Upload the file with `ds.files.upload(str(input_dir / "pi.py"), f"{input_uri}/pi.py")` after Step 5 — the rest is identical.

### Step 4: Configure Job Parameters

```python
ds_path: str = "/MyData/dapi-examples/pi-demo"  # Path to input files
input_filename: str = "pi.py"  # Main input script filename
max_job_minutes: int = 10  # Maximum runtime in minutes
tacc_allocation: str = (
    "DS-Portal-SPARC2026"  # TACC allocation to charge — change to yours
)
app_id_to_use: str = "python-s3"  # General-purpose Python application ID
```

### Step 5: Convert Path to URI

```python
input_uri = ds.files.to_uri(ds_path)
print(f"Input Directory Tapis URI: {input_uri}")
```

### Step 6: Generate Job Request

```python
job_dict = ds.jobs.generate(
    app_id=app_id_to_use,
    input_dir_uri=input_uri,
    script_filename=input_filename,
    max_minutes=max_job_minutes,
    allocation=tacc_allocation,
    queue="skx-dev",  # development queue: fast turnaround for short runs
    archive_system="designsafe",
    archive_path="python-s3-results",
    job_name="mc-pi",
    description="Monte Carlo pi on one Stampede3 node",
    tags=["demo"],
)
print(json.dumps(job_dict, indent=2, default=str))
```

### Step 7: Customize (Optional)

The app is configured entirely through the job request — arguments, a different executable, modules, pip installs, input bundles, and pre/post scripts. See the [app documentation](https://designsafe-ci.github.io/ds-workflows/apps/python) for all options.

```python
# Pass command-line arguments to the script (more samples)
job_dict["parameterSet"]["appArgs"].append({"name": "Arguments", "arg": "50000000"})

# Run something other than Python, e.g. OpenSees-MP (Tcl) on 2 nodes
job_dict["nodeCount"] = 2
job_dict["coresPerNode"] = 48
job_dict["parameterSet"]["envVariables"] = [
    {"key": "BINARY", "value": "OpenSeesMP"},
    {"key": "EXTRA_MODULES", "value": "opensees,hdf5/1.14.4"},
    {"key": "USE_MPI", "value": "True"},
]

# Many small input files? Ship ONE zip instead — Tapis stages each file as its
# own transfer (~40s/file under load). The app expands it before anything else
# runs, so even the pre-script can live inside the bundle.
job_dict["parameterSet"]["envVariables"] = [
    {"key": "UNZIP_INPUTS", "value": "inputs"},  # inputs.zip in the Input Directory
]
```

### Step 8: Submit Job

```python
submitted_job = ds.jobs.submit(job_dict)
print(f"Job UUID: {submitted_job.uuid}")
```

### Step 9: Monitor Job

```python
# timeout_minutes bounds the monitoring, not the job — it defaults to the
# job's max_minutes, which queue and staging waits can exhaust.
final_status = submitted_job.monitor(interval=15, timeout_minutes=60)
print(f"Job {submitted_job.uuid} finished with status: {final_status}")
```

### Step 10: Check Results

```python
ds.jobs.interpret_status(final_status, submitted_job.uuid)
submitted_job.print_runtime_summary(verbose=False)

stdout_content = submitted_job.get_output_content("tapisjob.out", max_lines=30)
if stdout_content:
    print(stdout_content)
```

Expected output (from a verified run — job `03c94346-56a2-4f6d-9161-edaebdc18a19-007`, 37 s running, 3:08 total):

```
pi ~= 3.142032  (48 workers, 9,999,984 samples)
```

### Step 11: The Run Record

Unlike most apps, every `python-s3` job writes a machine-readable run record — per-stage exit codes and timings, the exact command, the resolved binary, the Python environment, and the loaded modules:

```python
summary_content = submitted_job.get_output_content("job-summary.json")
if summary_content:
    print(summary_content)
```

```json
{
  "app_id": "python-s3",
  "app_version": "1.0.0",
  "job_uuid": "03c94346-56a2-4f6d-9161-edaebdc18a19-007",
  "hostname": "c454-003.stampede3.tacc.utexas.edu",
  "input_script": "pi.py",
  "binary": "/opt/apps/python/3.12.11/bin/python3",
  "python_env": null,
  "command": "/opt/apps/python/3.12.11/bin/python3 pi.py",
  "python_version": "Python 3.12.11",
  "stages": {
    "setup": {"seconds": 0},
    "pre_script": {"script": null, "exit_code": null, "seconds": null},
    "main": {"exit_code": 0, "seconds": 1},
    "post_script": {"script": null, "exit_code": null, "seconds": null}
  },
  "exit_code": 0
}
```

### Step 12: Access Results

```python
archive_uri = submitted_job.archive_uri
print(f"Archive URI: {archive_uri}")
for item in ds.files.list(archive_uri):
    print(f"- {item.name} ({item.type})")
```

The archive in My Data contains the input directory, `tapisjob.out`, and `job-summary.json` — everything needed to document what ran.
