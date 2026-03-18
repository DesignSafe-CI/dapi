# Launcher

PyLauncher parameter sweep utilities for generating task lists and launcher scripts.

## Generate Sweep

### `generate_sweep(command, sweep, directory=None, *, placeholder_style="token", debug=None, preview=False)`

Generate sweep commands and write PyLauncher input files.

When `preview` is `True`, returns a DataFrame of all parameter combinations without writing any files -- useful for inspecting the sweep in a notebook before committing.

When `preview` is `False` (default), expands `command` into one command per parameter combination and writes `runsList.txt` and `call_pylauncher.py` into `directory`.

**Args:**
- `command` (str): Command template containing placeholders that match keys in `sweep`. Environment variables like `$WORK` or `$SLURM_JOB_ID` are left untouched.
- `sweep` (Mapping[str, Sequence[Any]]): Mapping of placeholder name to a sequence of values. Example: `{"ALPHA": [0.3, 0.5], "BETA": [1, 2]}`.
- `directory` (str | Path, optional): Directory to write files into. Created if it does not exist. Required when `preview` is `False`.
- `placeholder_style` (str, optional): How placeholders appear in `command`:
  - `"token"` (default): bare tokens, e.g. `ALPHA`
  - `"braces"`: brace-wrapped, e.g. `{ALPHA}`
- `debug` (str, optional): Optional debug string passed to `ClassicLauncher` (e.g., `"host+job"`). Ignored when `preview` is `True`.
- `preview` (bool, optional): If `True`, return a DataFrame of parameter combinations without writing files. Defaults to `False`.

**Returns:** `List[str]` of generated commands when `preview` is `False`, or a `pandas.DataFrame` of parameter combinations when `True`.

**Raises:**
- `TypeError`: If a sweep value is not a non-string sequence.
- `ValueError`: If a sweep value is empty, `placeholder_style` is invalid, or `directory` is missing when `preview` is `False`.

**Example:**

```python
from dapi.launcher import generate_sweep

# Preview parameter combinations
df = generate_sweep(
    command="python run.py --alpha ALPHA --beta BETA",
    sweep={"ALPHA": [0.1, 0.5, 1.0], "BETA": [1, 2]},
    preview=True,
)
print(df)
#    ALPHA  BETA
# 0    0.1     1
# 1    0.1     2
# 2    0.5     1
# 3    0.5     2
# 4    1.0     1
# 5    1.0     2

# Generate files for PyLauncher
commands = generate_sweep(
    command="python run.py --alpha ALPHA --beta BETA",
    sweep={"ALPHA": [0.1, 0.5, 1.0], "BETA": [1, 2]},
    directory="/home/jupyter/MyData/sweep/",
)
# Writes runsList.txt and call_pylauncher.py to the directory
```

## Client Interface

The `ParametricSweepMethods` class is accessible via `ds.jobs.parametric_sweep` on a `DSClient` instance. It wraps `generate_sweep` and adds a `submit` method that handles Tapis URI translation and job submission.

### `ParametricSweepMethods.generate(command, sweep, directory=None, *, placeholder_style="token", debug=None, preview=False)`

Generate PyLauncher sweep files or preview the parameter grid. This is a convenience wrapper around `generate_sweep()`.

**Args:**
- `command` (str): Command template with placeholders matching sweep keys.
- `sweep` (Dict[str, Any]): Mapping of placeholder name to sequence of values.
- `directory` (str, optional): Directory to write files into (created if needed). Required when `preview` is `False`.
- `placeholder_style` (str, optional): `"token"` (default) for bare `ALPHA`, or `"braces"` for `{ALPHA}`.
- `debug` (str, optional): Optional debug string (e.g., `"host+job"`).
- `preview` (bool, optional): If `True`, return a DataFrame (dry run).

**Returns:** `List[str]` of commands, or `pandas.DataFrame` when `preview` is `True`.

**Example:**

```python
ds = DSClient()

# Preview
df = ds.jobs.parametric_sweep.generate(
    command="python run.py --alpha ALPHA",
    sweep={"ALPHA": [0.1, 0.5, 1.0]},
    preview=True,
)

# Write files
commands = ds.jobs.parametric_sweep.generate(
    command="python run.py --alpha ALPHA",
    sweep={"ALPHA": [0.1, 0.5, 1.0]},
    directory="/home/jupyter/MyData/sweep/",
)
```

---

### `ParametricSweepMethods.submit(directory, app_id, allocation, *, node_count=None, cores_per_node=None, max_minutes=None, queue=None, **kwargs)`

Submit a PyLauncher sweep job. Translates `directory` to a Tapis URI, builds a job request with `call_pylauncher.py` as the script, and submits it.

**Args:**
- `directory` (str): Path to the input directory containing `runsList.txt` and `call_pylauncher.py` (e.g., `"/MyData/sweep/"`).
- `app_id` (str): Tapis application ID (e.g., `"openseespy-s3"`).
- `allocation` (str): TACC allocation to charge.
- `node_count` (int, optional): Number of compute nodes.
- `cores_per_node` (int, optional): Cores per node.
- `max_minutes` (int, optional): Maximum runtime in minutes.
- `queue` (str, optional): Execution queue name.
- `**kwargs`: Additional arguments passed to `ds.jobs.generate()`.

**Returns:** `SubmittedJob` -- A job object for monitoring via `.monitor()`.

**Example:**

```python
ds = DSClient()

# Generate sweep files first
ds.jobs.parametric_sweep.generate(
    command="python run.py --alpha ALPHA --beta BETA",
    sweep={"ALPHA": [0.1, 0.5], "BETA": [1, 2]},
    directory="/home/jupyter/MyData/sweep/",
)

# Submit the sweep job
job = ds.jobs.parametric_sweep.submit(
    directory="/MyData/sweep/",
    app_id="openseespy-s3",
    allocation="MyProject-123",
    node_count=2,
    max_minutes=60,
)
job.monitor()
```
