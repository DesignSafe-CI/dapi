# quoFEM Sensitivity Analysis Example

This example runs a quoFEM global sensitivity analysis with the SimCenter UQ engine on TACC Stampede3 using dapi, then post-processes the results in Python. The workflow performs Monte Carlo sampling (500 samples) of three PM4Sand constitutive model parameters (`Dr`, `G0`, `hpo`) in a cyclic direct simple shear simulation and reports Sobol sensitivity indices for the number-of-cycles engineering demand parameters (EDPs).

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/quoFEM-sensitivity/quoFEM-sensitivity-dapi.ipynb)

For general job submission concepts, see [Jobs](../jobs.md). For resource sizing, see [DesignSafe Workflows](https://kks32.github.io/ds-workflows/guide/job-resources.html).

## How dapi handles SimCenter apps

The SimCenter Tapis apps (quoFEM, EE-UQ, WE-UQ backends such as `simcenter-uq-stampede3`) declare no fileInputs or envVariables in their app definitions — their interface contract lives inside the app's wrapper script. dapi (>= 0.5.4) encodes that contract as an app profile that is applied automatically:

- `ds.jobs.prepare_inputs()` points the workflow JSON (`scInput.json`) at the SimCenter backend installation on the execution system and bundles the inputs into a single `tmpSimCenter.zip`, which the app wrapper unpacks natively. Staging one file instead of many avoids the Tapis transfers service's per-file overhead (measured at up to ~40 s per file under tenant load); pass `bundle=False` to stage the loose directory instead.
- `ds.jobs.generate()` exposes the input directory to the wrapper as the `inputDirectory` environment variable and sets the `inputFile`/`driverFile` environment variables.
- `job.get_results()` retrieves `results.zip` from the job archive in memory and parses the sample table and Sobol indices.

## Complete Example

### Step 1: Install and Import dapi

```python
# Install dapi package
%pip install --upgrade dapi --quiet

# Import required modules
from dapi import DSClient
import os
import json
```

### Step 2: Initialize Client

```python
# Initialize DesignSafe client
ds = DSClient()
```

**Authentication:** dapi supports multiple authentication methods including environment variables, .env files, and interactive prompts. For detailed authentication setup instructions, see the [authentication guide](../authentication.md).

### Step 3: Configure Job Parameters

```python
# Job configuration parameters
job_name: str = "quofem-sensitivity-dapi"
app_id: str = "simcenter-uq-stampede3"  # SimCenter UQ application ID
tacc_allocation: str = "your-allocation"  # TACC allocation to charge
archive_system: str = "designsafe"  # Archive results to MyData
archive_path = None

# Resource configuration
queue: str = "skx-dev"
node_count: int = 1
cores_per_node: int = 48
memory_mb: int = 128000
max_job_minutes: int = 120
```

### Step 4: Prepare the SimCenter Inputs

The input directory contains the quoFEM working files (`tmp.SimCenter/templatedir/` with `scInput.json`, the per-sample `driver` script, and the OpenSees model files). `prepare_inputs` rewrites the workflow JSON's backend paths (pass `backend_dir=...` to override the registered installation), reports the UQ workflow, and bundles the inputs.

```python
ds_path = os.getcwd() + "/DS_input"

info = ds.jobs.prepare_inputs(app_id, ds_path)

rv_names = info["random_variables"]  # ['Dr', 'G0', 'hpo']
edp_names = info["edps"]  # ['nCycles010_1', ...]

# Stage the bundled directory (contains only tmpSimCenter.zip)
input_uri = ds.files.to_uri(info["staged_dir"])
```

### Step 5: Generate Job Request

The SimCenter app profile applies the wrapper contract automatically — no manual `envKey`, `targetPath`, or environment variable setup is needed.

```python
job_dict = ds.jobs.generate(
    app_id=app_id,
    input_dir_uri=input_uri,
    archive_system=archive_system,
    archive_path=archive_path,
    max_minutes=max_job_minutes,
    allocation=tacc_allocation,
    queue=queue,
    job_name=job_name,
    node_count=node_count,
    cores_per_node=cores_per_node,
    memory_mb=memory_mb,
)
print(json.dumps(job_dict, indent=2, default=str))
```

### Step 6: Submit and Monitor

```python
submitted_job = ds.jobs.submit(job_dict)
print(f"Job launched with UUID: {submitted_job.uuid}")

final_status = submitted_job.monitor(interval=30)
ds.jobs.interpret_status(final_status, submitted_job.uuid)
submitted_job.print_runtime_summary(verbose=False)
```

### Step 7: Retrieve and Analyze Results

The app wrapper gathers the UQ engine outputs (`dakota.out`, `dakotaTab.out`) into `results.zip` in the job archive. `get_results()` fetches and parses it in memory.

```python
results = submitted_job.get_results()

samples = results.samples  # DataFrame: one row per realization
sobol = results.sobol_indices  # DataFrame: outputs x Sm/St indices per RV
print(samples.head())
print(sobol)
```

### Step 8: Plot Sensitivity Indices

```python
import matplotlib.pyplot as plt
import numpy as np

palette = ["#4269d0", "#efb118", "#ff725c"]  # fixed hue per random variable

fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
x = np.arange(len(sobol.index))
width = 0.25
for ax, prefix, title in zip(axes, ("Sm", "St"), ("Main", "Total")):
    for i, (rv, color) in enumerate(zip(rv_names, palette)):
        ax.bar(
            x + (i - 1) * width,
            sobol[f"{prefix}({rv})"],
            width,
            color=color,
            label=rv if prefix == "Sm" else None,
        )
    ax.set_title(f"{title} Sobol index")
    ax.set_ylim(0, 1)
    ax.set_xticks(x)
    ax.set_xticklabels(sobol.index, rotation=30, ha="right")
    ax.grid(alpha=0.25, axis="y")
    ax.set_axisbelow(True)
axes[0].legend(title="Random variable")
fig.tight_layout()
plt.show()
```

## Archiving Results to a Project

By default results archive to MyData (`tapis-jobs-archive/`). To archive into a shared DesignSafe project instead — so collaborators can see the job and its outputs — point `archive_system` at the project system id:

```python
archive_system = "project-<uuid>"  # from ds.projects.list()
archive_path = f"quoFEM_jobs/{job_name}/${{JobUUID}}"
```

Include `${JobUUID}` (or `${JobCreateDate}`) in the path so repeated runs don't mix files in one folder. You must have write access to the project, and `job.get_results()` works unchanged.

## Why Input Bundling Matters

The Tapis transfers service turns each staged file into its own queued task, so staging time scales with file count rather than bytes. Measured on the same job, same inputs:

| Phase          | 15 loose files | 1 bundled zip |
| -------------- | -------------- | ------------- |
| STAGING_INPUTS | 10:58          | 0:46          |
| TOTAL          | 29:09          | 16:23         |

`prepare_inputs` bundles by default for SimCenter apps because the wrapper natively unpacks `tmpSimCenter.zip` — the original input directory is never modified beyond the workflow-JSON patch.
