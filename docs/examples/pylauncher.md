# PyLauncher Parameter Sweeps

Run many independent tasks within a single SLURM allocation using [PyLauncher](https://github.com/TACC/pylauncher) and dapi's parameter sweep utilities.

Solution: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/pylauncher/pylauncher_sweep.ipynb)

Exercise: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/pylauncher/pylauncher_sweep_exercise.ipynb)

## When to Use PyLauncher

- You have many independent serial runs (parameter studies, Monte Carlo, etc.)
- Each run writes to its own output directory
- You want to use multi-core allocations without MPI

## End-to-End Workflow

The notebook sweeps the forcing frequency of a 5%-damped oscillator, one independent simulation per frequency, and reassembles the resonance curve from the archived results, laying the simulated points over the closed-form amplification curve they must land on.

### 1. Define the Parameter Sweep

```python
from dapi import DSClient

ds = DSClient()

sweep = {
    "RATIO": [round(0.2 + 0.075 * i, 3) for i in range(25)],
}

command = "python3 oscillator.py --ratio RATIO --output out_RATIO"
```

Every value becomes one task, and the `RATIO` placeholder in the command template is replaced per task.

### 2. Preview (dry run)

```python
ds.jobs.parametric_sweep.generate(command, sweep, preview=True)
```

| | RATIO |
|---|-------|
| 0 | 0.2 |
| 1 | 0.275 |
| ... | ... |
| 24 | 2.0 |

### 3. Generate Sweep Files

```python
commands = ds.jobs.parametric_sweep.generate(command, sweep, str(input_dir))
```

### 4. Submit

```python
job = ds.jobs.parametric_sweep.submit(
    str(input_dir),  # local folders upload automatically
    app_id="python-s3",
    allocation="your_allocation",
    node_count=1,
    cores_per_node=48,
    max_minutes=15,
    queue="skx-dev",
)
job.monitor(interval=30)
```

### 5. Reassemble the Curve

Each task archives a `result.json` with its frequency ratio and amplification; the notebook gathers them from the job archive and plots the resonance curve against the closed form, peaked near the natural frequency at roughly `1/(2*damping) = 10`.

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

A parameter sweep for a cantilever pushover analysis. See the full notebook: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/pylauncher/pylauncher_opensees.ipynb)

```python
sweep = {
    "NODAL_MASS": [4.19, 4.39, 4.59, 4.79, 4.99],
    "LCOL": [100, 200, 300],
}

ds.jobs.parametric_sweep.generate(
    "python3 cantilever.py --mass NODAL_MASS --lcol LCOL --outDir out_NODAL_MASS_LCOL",
    sweep,
    "/home/jupyter/MyData/opensees_sweep/",
)

job = ds.jobs.parametric_sweep.submit(
    "/MyData/opensees_sweep/",
    app_id="python-s3",
    allocation="your_allocation",
    node_count=2,
    cores_per_node=48,
)
job.monitor()
```

On Stampede3 (`python-s3` v1.0.0), the 9 tasks completed in 7 seconds, each producing its `out_*/result.json`.

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
- **MPI is disabled** -- PyLauncher's `ClassicLauncher` runs independent serial tasks. The `python-s3` app already has `isMpi: false` and loads the `pylauncher` module automatically.
- **Works with any app** -- OpenSees, Python, MATLAB, Fortran binaries. The task list is just shell commands.
