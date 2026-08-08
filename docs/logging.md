# Logging and Verbosity

dapi reports what it is doing through Python's standard `logging` module, under the `dapi` logger namespace. By default you see concise milestones; turn the detail up or down globally with one call.

## Levels

```python
import dapi

dapi.set_log_level("DEBUG")  # full step-by-step trace
dapi.set_log_level("INFO")  # default: concise milestones
dapi.set_log_level("WARNING")  # problems only
dapi.set_log_level("QUIET")  # silence dapi entirely
```

Or set it before import with an environment variable:

```bash
export DAPI_LOG_LEVEL=WARNING
```

What each level shows:

| Level | You see |
|---|---|
| `INFO` (default) | Staging relocations, bundles built, uploads completed, job submitted (UUID), monitoring started, warnings and errors |
| `DEBUG` | Everything above plus path translations, per-file transfers, job-request construction, app-profile dispatch, module-level detail |
| `WARNING` | Only problems (missing optional inputs, skipped credentials, failures) |
| `QUIET` | Nothing |

Example — the same read-only-source `prepare_inputs` call:

```
# INFO (default)
'/home/jupyter/CommunityData/...' is not writable (e.g. CommunityData); staging to /tmp/dapi-staging-.../DS_input_staged
Bundled 12 files into /tmp/dapi-staging-.../DS_input_staged/tmpSimCenter.zip
Uploading staged files to your DesignSafe storage (tapis://designsafe.storage.default/...) ...
Uploaded 1 file(s); staged_dir is now /MyData/dapi-staging/DS_input_staged
```

At `DEBUG` the run also traces each path translation and per-file transfer; at `QUIET` it prints nothing.

## Notebook and terminal behavior

The dapi handler writes to **stdout**, not stderr — so log lines render as normal output in Jupyter (no red boxes) and stay in order with your prints and the job-monitoring progress bars. The same configuration works identically in a terminal.

## For applications embedding dapi

dapi never touches the root logger. All output flows through the `dapi` logger hierarchy (`dapi.jobs`, `dapi.files`, `dapi.simcenter`, ...), so standard `logging` configuration applies:

```python
import logging

logging.getLogger("dapi").setLevel(logging.WARNING)  # quiet dapi only
logging.getLogger("dapi.files").setLevel(logging.DEBUG)  # trace one module
```

Functions whose purpose *is* output — `job.print_runtime_summary()`, `ds.jobs.interpret_status()`, `ds.apps.find(..., verbose=True)` — print directly regardless of log level, since you called them to see their report.
