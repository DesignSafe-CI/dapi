# PyLauncher Parameter Sweeps

Run many independent tasks within a single SLURM allocation using [PyLauncher](https://github.com/TACC/pylauncher) and dapi's parameter sweep utilities.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/pylauncher/pylauncher_sweep.ipynb)

## When to Use PyLauncher

- You have many independent serial runs (parameter studies, Monte Carlo, etc.)
- Each run writes to its own output directory
- You want to use multi-core allocations without MPI

## End-to-End Workflow

### 1. Define the Parameter Sweep

```python
from dapi import DSClient

ds = DSClient()

sweep = {
    "ALPHA": [0.3, 0.5, 3.7],
    "BETA":  [1.1, 2.0, 3.0],
}
```

### 2. Preview (dry run)

```python
ds.jobs.parametric_sweep.generate(
    'python3 simulate.py --alpha ALPHA --beta BETA',
    sweep,
    preview=True,
)
```

| | ALPHA | BETA |
|---|-------|------|
| 0 | 0.3 | 1.1 |
| 1 | 0.3 | 2.0 |
| ... | ... | ... |
| 8 | 3.7 | 3.0 |

### 3. Generate Sweep Files

```python
ds.jobs.parametric_sweep.generate(
    'python3 simulate.py --alpha ALPHA --beta BETA '
    '--output "$WORK/sweep_$SLURM_JOB_ID/run_ALPHA_BETA"',
    sweep,
    "/home/jupyter/MyData/pylauncher_demo/",
    debug="host+job",
)
```

### 4. Submit

```python
job = ds.jobs.parametric_sweep.submit(
    "/MyData/pylauncher_demo/",
    app_id="designsafe-agnostic-app",
    allocation="your_allocation",
    node_count=1,
    cores_per_node=48,
    max_minutes=30,
)
job.monitor()
```

## Placeholder Styles

Two styles are supported for command templates:

**Token style** (default) -- bare uppercase placeholders:

```python
"python run.py --mass MASS --length LENGTH"
```

**Braces style** -- for when token names might collide with other text:

```python
"python run.py --mass {MASS} --length {LENGTH}"
# pass placeholder_style="braces"
```

## OpenSees Example

A parameter sweep for a cantilever pushover analysis:

```python
sweep = {
    "NODAL_MASS": [4.19, 4.39, 4.59, 4.79, 4.99],
    "LCOL": [100, 200, 300],
}

ds.jobs.parametric_sweep.generate(
    "python3 cantilever.py --mass NODAL_MASS --lcol LCOL "
    "--outDir out_NODAL_MASS_LCOL",
    sweep,
    "/home/jupyter/MyData/opensees_sweep/",
)

job = ds.jobs.parametric_sweep.submit(
    "/MyData/opensees_sweep/",
    app_id="designsafe-agnostic-app",
    allocation="your_allocation",
    node_count=2,
    cores_per_node=48,
)
job.monitor()
```

## Output Directory Pattern

Use TACC environment variables for collision-free output directories:

```
$WORK/sweep_$SLURM_JOB_ID/run_ALPHA_BETA
```

- `$WORK` -- TACC Work filesystem (avoids archiving overhead)
- `$SLURM_JOB_ID` -- unique per job submission
- `$LAUNCHER_JID` / `$LAUNCHER_TSK_ID` -- unique per PyLauncher task

## Notes

- **PyLauncher is NOT a dapi dependency** -- it's pre-installed on TACC compute nodes. dapi only generates the input files.
- **MPI is disabled** -- PyLauncher's `ClassicLauncher` runs independent serial tasks. The `designsafe-agnostic-app` already has `isMpi: false`.
- **Works with any app** -- OpenSees, Python, MATLAB, Fortran binaries. The task list is just shell commands.
