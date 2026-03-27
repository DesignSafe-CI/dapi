# Job Management

## Listing Jobs

Browse your job history as a pandas DataFrame with optional filtering.

```python
from dapi import DSClient

ds = DSClient()

# List all recent jobs (default: last 100, returns DataFrame)
df = ds.jobs.list()
print(df[["name", "uuid", "status", "appId", "created_dt"]])

# Filter by application
df = ds.jobs.list(app_id="opensees-mp-s3")

# Filter by status
df = ds.jobs.list(status="FINISHED")

# Combine filters and increase limit
df = ds.jobs.list(app_id="matlab-r2023a", status="FAILED", limit=500)

# Use pandas for further analysis
finished = df[df["status"] == "FINISHED"]
print(f"Finished jobs: {len(finished)}")
print(finished.groupby("appId").size())
```

### Output Formats

By default `list()` returns a pandas DataFrame. Use the `output` parameter for other formats:

```python
# DataFrame (default) -- includes formatted datetime columns
df = ds.jobs.list()

# List of dicts -- lightweight, no pandas dependency
jobs = ds.jobs.list(output="list")
for job in jobs:
    print(f"{job['name']}: {job['status']}")

# Raw TapisResult objects -- for advanced Tapis API usage
raw = ds.jobs.list(output="raw")
```

For finding applications and their IDs, see [Apps](apps.md).

## Job Submission

### Basic Submission

```python
# 1. Prepare input directory
input_path = "/MyData/analysis/input/"
input_uri = ds.files.to_uri(input_path, verify_exists=True)

# 2. Generate job request
job_request = ds.jobs.generate(
 app_id="matlab-r2023a",
 input_dir_uri=input_uri,
 script_filename="run_analysis.m",
 max_minutes=60,
 allocation="your_tacc_allocation"
)

# 3. Submit job
job = ds.jobs.submit(job_request)
print(f"Job submitted: {job.uuid}")
```

### `generate()` Parameters

| Parameter | Type | Description |
|---|---|---|
| `app_id` | str | Tapis application ID (see [Apps](apps.md)) |
| `input_dir_uri` | str | Tapis URI of the input directory (use `ds.files.to_uri()`) |
| `script_filename` | str | Main script file in the input directory |
| `max_minutes` | int | Wall-clock time limit |
| `allocation` | str | TACC project allocation code |
| `node_count` | int | Number of compute nodes |
| `cores_per_node` | int | CPU cores per node |
| `memory_mb` | int | Memory per node in MB |
| `queue` | str | SLURM queue/partition name |
| `job_name` | str | Human-readable job name |
| `description` | str | Job description |
| `tags` | list | List of string tags for filtering |
| `archive_system` | str | Tapis system for output archiving (default: DesignSafe storage) |
| `archive_path` | str | Path on archive system for outputs |
| `input_dir_param_name` | str | Name of the file input parameter (default: `"Input Directory"`, some apps use different names like `"Case Directory"` for OpenFOAM) |
| `extra_file_inputs` | list | Additional file inputs beyond the main input directory |
| `extra_env_vars` | list | Environment variables as `[{"key": "...", "value": "..."}]` |
| `extra_scheduler_options` | list | SLURM scheduler options as `[{"name": "...", "arg": "..."}]` |

### Advanced Configuration

```python
job_request = ds.jobs.generate(
 app_id="mpm-s3",
 input_dir_uri=input_uri,
 script_filename="mpm.json",

 # Resource requirements
 max_minutes=120,
 node_count=2,
 cores_per_node=48,
 memory_mb=96000,
 queue="normal",
 allocation="your_allocation",

 # Job metadata
 job_name="mpm_parametric_study_001",
 description="Parametric study of soil behavior under seismic loading",
 tags=["research", "mpm", "seismic"],

 # Additional file inputs
 extra_file_inputs=[
 {
 "name": "Material Library",
 "sourceUrl": "tapis://designsafe.storage.default/shared/materials/",
 "targetPath": "materials"
 }
 ],

 # Environment variables
 extra_env_vars=[
 {"key": "OMP_NUM_THREADS", "value": "48"},
 {"key": "ANALYSIS_TYPE", "value": "SEISMIC"}
 ],

 # Scheduler options
 extra_scheduler_options=[
 {"name": "Email Notification", "arg": "-m be"},
 {"name": "Job Array", "arg": "-t 1-10"}
 ]
)
```

### Modifying Job Requests

```python
job_request = ds.jobs.generate(...)

# Modify before submission
job_request["name"] = "custom_job_name"
job_request["description"] = "Updated description"
job_request["nodeCount"] = 4
job_request["maxMinutes"] = 180

# Add custom parameters
if "parameterSet" not in job_request:
 job_request["parameterSet"] = {}
if "envVariables" not in job_request["parameterSet"]:
 job_request["parameterSet"]["envVariables"] = []

job_request["parameterSet"]["envVariables"].append({
 "key": "CUSTOM_PARAM",
 "value": "custom_value"
})

job = ds.jobs.submit(job_request)
```

## Job Monitoring

### Real-time Monitoring

```python
job = ds.jobs.submit(job_request)

final_status = job.monitor(
 interval=15, # Check every 15 seconds
 timeout_minutes=240 # Timeout after 4 hours
)

ds.jobs.interpret_status(final_status, job.uuid)
```

### Manual Status Checking

```python
current_status = job.get_status()
print(f"Current status: {current_status}")

if current_status in job.TERMINAL_STATES:
 print("Job has finished")
else:
 print("Job is still running")

details = job.details
print(f"Submitted: {details.created}")
print(f"Started: {details.started}")
print(f"Last Updated: {details.lastUpdated}")
```

### Job Statuses

| Status | Description |
|--------|-------------|
| `PENDING` | Submitted, not yet processed |
| `PROCESSING_INPUTS` | Input files being staged |
| `STAGING_INPUTS` | Files transferring to compute system |
| `STAGING_JOB` | Job being prepared for execution |
| `SUBMITTING_JOB` | Submitting to scheduler |
| `QUEUED` | Waiting in scheduler queue |
| `RUNNING` | Executing |
| `ARCHIVING` | Output files being archived |
| `FINISHED` | Completed successfully |
| `FAILED` | Failed |
| `CANCELLED` | Cancelled |
| `STOPPED` | Stopped |

## Job Analysis

### Runtime Summary

```python
job.print_runtime_summary(verbose=False)

# Detailed history
job.print_runtime_summary(verbose=True)
```

Example output:
```
Runtime Summary
---------------
QUEUED time: 00:05:30
RUNNING time: 01:23:45
TOTAL time: 01:29:15
---------------
```

### Status Messages

```python
last_message = job.last_message
if last_message:
 print(f"Last message: {last_message}")
```

## Output Management

### Listing Outputs

```python
outputs = job.list_outputs()
for output in outputs:
 print(f"- {output.name} ({output.type}, {output.size} bytes)")

# Subdirectory
results = job.list_outputs(path="results/")
```

### Reading Output Files

```python
stdout = job.get_output_content("tapisjob.out")
if stdout:
 print(stdout)

# Last 50 lines
recent_output = job.get_output_content("tapisjob.out", max_lines=50)

# Error log
stderr = job.get_output_content("tapisjob.err", missing_ok=True)
if stderr:
 print(stderr)
```

### Downloading Files

```python
job.download_output("results.mat", "/local/path/results.mat")

ds.files.download(
 f"{archive_uri}/results.mat",
 "/local/path/results.mat"
)
```

## Job Cancellation

```python
job.cancel()
status = job.get_status()
print(f"Status after cancel: {status}")
```

Cancellation may not be immediate. Jobs in terminal states (FINISHED, FAILED, etc.) cannot be cancelled.

## Resuming Monitoring

Reconnect to a previously submitted job using its UUID.

```python
job = ds.jobs.get("12345678-1234-1234-1234-123456789abc")
final_status = job.monitor()
```

(pylauncher)=
## Parameter Sweeps with PyLauncher

See the [PyLauncher example](examples/pylauncher.md) for a full walkthrough, or the [PyLauncher OpenSees example](examples/pylauncher_opensees.md) for a structural engineering use case.

## Bulk Operations

```python
job_uuids = ["uuid1", "uuid2", "uuid3"]
jobs = [ds.jobs.get(uuid) for uuid in job_uuids]

for job in jobs:
 status = job.get_status()
 print(f"Job {job.uuid}: {status}")

for job in jobs:
 if job.get_status() not in job.TERMINAL_STATES:
 final_status = job.monitor()
 print(f"Final status: {final_status}")
```

## Multiple Separate Jobs

If each run needs its own full allocation (e.g., MPI jobs that can't share nodes), submit them as separate Tapis jobs:

```python
parameters = [
 {"friction": 0.1, "density": 2000},
 {"friction": 0.2, "density": 2200},
 {"friction": 0.3, "density": 2400},
]

submitted_jobs = []
for i, params in enumerate(parameters):
 job_req = ds.jobs.generate(
 app_id="mpm-s3",
 input_dir_uri=input_uri,
 script_filename="template.json",
 max_minutes=60,
 allocation="your_allocation",
 extra_env_vars=[
 {"key": "FRICTION", "value": str(params["friction"])},
 {"key": "DENSITY", "value": str(params["density"])},
 ],
 )
 job_req["name"] = f"parametric_study_{i:03d}"
 job = ds.jobs.submit(job_req)
 submitted_jobs.append(job)

for job in submitted_jobs:
 job.monitor()
```

For independent serial tasks, [PyLauncher](#pylauncher) is more efficient — it runs all tasks in a single allocation.

## Job Dependencies

```python
# Job 1: Preprocessing
prep_job = ds.jobs.submit(preprocessing_request)
prep_status = prep_job.monitor()

if prep_status == "FINISHED":
 # Job 2: Main analysis (uses outputs from Job 1)
 main_request["fileInputs"].append({
 "name": "Preprocessed Data",
 "sourceUrl": prep_job.archive_uri,
 "targetPath": "preprocessed"
 })

 main_job = ds.jobs.submit(main_request)
 main_status = main_job.monitor()

 if main_status == "FINISHED":
 # Job 3: Postprocessing
 post_request["fileInputs"].append({
 "name": "Analysis Results",
 "sourceUrl": main_job.archive_uri,
 "targetPath": "results"
 })

 post_job = ds.jobs.submit(post_request)
 final_status = post_job.monitor()
```

## Error Handling

```python
from dapi import JobSubmissionError, JobMonitorError

try:
 job = ds.jobs.submit(job_request)
 final_status = job.monitor()

except JobSubmissionError as e:
 print(f"Job submission failed: {e}")

 if "allocation" in str(e).lower():
 print("Check your TACC allocation is correct and active")
 elif "queue" in str(e).lower():
 print("Check the queue name is valid for the system")
 elif "file" in str(e).lower():
 print("Check input files exist and paths are correct")

except JobMonitorError as e:
 print(f"Job monitoring failed: {e}")
 try:
 status = job.get_status()
 print(f"Last known status: {status}")
 except:
 print("Cannot determine job status")
```

### Debugging Failed Jobs

```python
if final_status == "FAILED":
 stderr = job.get_output_content("tapisjob.err", missing_ok=True)
 if stderr:
 print("Standard Error:")
 print(stderr)

 stdout = job.get_output_content("tapisjob.out", max_lines=100)
 if stdout:
 print("Last 100 lines of output:")
 print(stdout)

 details = job.details
 print(f"Last message: {details.lastMessage}")
 print(f"Full history: job.print_runtime_summary(verbose=True)")
```

## System Queues

```python
frontera_queues = ds.systems.queues("frontera")
for queue in frontera_queues:
 print(f"Queue: {queue.name}")
 print(f"Max runtime: {queue.maxMinutes} min")
 print(f"Max nodes: {queue.maxNodeCount}")
```
