# Job Management

This guide covers everything you need to know about submitting, monitoring, and managing computational jobs on DesignSafe using dapi.

## 🎯 Overview

dapi provides a high-level interface for working with TAPIS v3 jobs on DesignSafe. You can:

- **Discover** available applications
- **Generate** job requests with automatic parameter mapping
- **Submit** jobs to DesignSafe compute resources
- **Monitor** job progress with real-time updates
- **Manage** job outputs and results

## 🔍 Application Discovery

### Finding Applications

```python
from dapi import DSClient

client = DSClient()

# Find all applications
all_apps = client.apps.find("", verbose=False)
print(f"Found {len(all_apps)} applications")

# Search for specific applications
matlab_apps = client.apps.find("matlab", verbose=True)
opensees_apps = client.apps.find("opensees", verbose=True)
mpm_apps = client.apps.find("mpm", verbose=True)
```

### Getting Application Details

```python
# Get detailed information about an application
app_details = client.apps.get_details("mpm-s3", verbose=True)

print(f"App: {app_details.id}")
print(f"Version: {app_details.version}")
print(f"Description: {app_details.description}")
print(f"Execution System: {app_details.jobAttributes.execSystemId}")
print(f"Max Runtime: {app_details.jobAttributes.maxMinutes} minutes")
print(f"Default Cores: {app_details.jobAttributes.coresPerNode}")
```

### Popular Applications

| Application | App ID | Description |
|-------------|--------|-------------|
| MATLAB | `matlab-r2023a` | MATLAB computational environment |
| OpenSees | `opensees-express` | Structural analysis framework |
| MPM | `mpm-s3` | Material Point Method simulations |
| ADCIRC | `adcirc-v55` | Coastal circulation modeling |
| LS-DYNA | `ls-dyna` | Explicit finite element analysis |

## 🚀 Job Submission

### Basic Job Submission

```python
# 1. Prepare input directory
input_path = "/MyData/analysis/input/"
input_uri = client.files.translate_path_to_uri(input_path, verify_exists=True)

# 2. Generate job request
job_request = client.jobs.generate_request(
    app_id="matlab-r2023a",
    input_dir_uri=input_uri,
    script_filename="run_analysis.m",
    max_minutes=60,
    allocation="your_tacc_allocation"
)

# 3. Submit job
job = client.jobs.submit_request(job_request)
print(f"Job submitted: {job.uuid}")
```

### Advanced Job Configuration

```python
job_request = client.jobs.generate_request(
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
# Generate base request
job_request = client.jobs.generate_request(...)

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

# Submit modified request
job = client.jobs.submit_request(job_request)
```

## 📊 Job Monitoring

### Real-time Monitoring

```python
# Submit job
job = client.jobs.submit_request(job_request)

# Monitor with progress bars
final_status = job.monitor(
    interval=15,           # Check every 15 seconds
    timeout_minutes=240    # Timeout after 4 hours
)

# Interpret results
client.jobs.interpret_status(final_status, job.uuid)
```

### Manual Status Checking

```python
# Check current status
current_status = job.get_status()
print(f"Current status: {current_status}")

# Check if job is complete
if current_status in job.TERMINAL_STATES:
    print("Job has finished")
else:
    print("Job is still running")

# Get detailed job information
details = job.details
print(f"Submitted: {details.created}")
print(f"Started: {details.started}")
print(f"Last Updated: {details.lastUpdated}")
```

### Job Status Overview

| Status | Description |
|--------|-------------|
| `PENDING` | Job submitted but not yet processed |
| `PROCESSING_INPUTS` | Input files being staged |
| `STAGING_INPUTS` | Files being transferred to compute system |
| `STAGING_JOB` | Job being prepared for execution |
| `SUBMITTING_JOB` | Job being submitted to scheduler |
| `QUEUED` | Job waiting in scheduler queue |
| `RUNNING` | Job actively executing |
| `ARCHIVING` | Output files being archived |
| `FINISHED` | Job completed successfully |
| `FAILED` | Job failed during execution |
| `CANCELLED` | Job was cancelled |
| `STOPPED` | Job was stopped |

## 📈 Job Analysis

### Runtime Summary

```python
# Get runtime breakdown
job.print_runtime_summary(verbose=False)

# Detailed history (verbose mode)
job.print_runtime_summary(verbose=True)
```

Example output:
```
Runtime Summary
---------------
QUEUED  time: 00:05:30
RUNNING time: 01:23:45
TOTAL   time: 01:29:15
---------------
```

### Status Messages

```python
# Get last status message
last_message = job.last_message
if last_message:
    print(f"Last message: {last_message}")
else:
    print("No status message available")
```

## 📁 Output Management

### Listing Job Outputs

```python
# List all files in job archive
outputs = job.list_outputs()
for output in outputs:
    print(f"- {output.name} ({output.type}, {output.size} bytes)")

# List files in subdirectory
results = job.list_outputs(path="results/")
```

### Accessing Job Archive

```python
# Get archive URI
archive_uri = job.archive_uri
print(f"Job archive: {archive_uri}")

# Use files interface to browse archive
files = client.files.list(archive_uri)
for file in files:
    print(f"- {file.name}")
```

### Reading Output Files

```python
# Read job output log
stdout = job.get_output_content("tapisjob.out")
if stdout:
    print("Job Output:")
    print(stdout)

# Read last 50 lines of output
recent_output = job.get_output_content("tapisjob.out", max_lines=50)

# Read error log (if job failed)
stderr = job.get_output_content("tapisjob.err", missing_ok=True)
if stderr:
    print("Error Output:")
    print(stderr)

# Read custom output files
results = job.get_output_content("results.txt", missing_ok=True)
```

### Downloading Files

```python
# Download specific files
job.download_output("results.mat", "/local/path/results.mat")
job.download_output("output_data.csv", "/local/analysis/data.csv")

# Download using files interface
client.files.download(
    f"{archive_uri}/results.mat",
    "/local/path/results.mat"
)
```

## 🔄 Job Management

### Job Cancellation

```python
# Cancel a running job
job.cancel()

# Check status after cancellation
status = job.get_status()
print(f"Status after cancel: {status}")
```

The `cancel()` method sends a cancellation request to Tapis. Note that:
- Cancellation may not be immediate and depends on the job's current state
- Jobs already in terminal states (FINISHED, FAILED, etc.) cannot be cancelled
- The job status will eventually change to "CANCELLED" if the cancellation is successful

### Resuming Monitoring

```python
# If you lose connection, resume monitoring with job UUID
from dapi import SubmittedJob

job_uuid = "12345678-1234-1234-1234-123456789abc"
resumed_job = SubmittedJob(client._tapis, job_uuid)

# Continue monitoring
final_status = resumed_job.monitor()
```

### Bulk Job Operations

```python
# Monitor multiple jobs
job_uuids = ["uuid1", "uuid2", "uuid3"]
jobs = [SubmittedJob(client._tapis, uuid) for uuid in job_uuids]

# Check all statuses
for job in jobs:
    status = job.get_status()
    print(f"Job {job.uuid}: {status}")

# Wait for all to complete
for job in jobs:
    if job.get_status() not in job.TERMINAL_STATES:
        print(f"Monitoring {job.uuid}...")
        final_status = job.monitor()
        print(f"Final status: {final_status}")
```

## 🖥️ System Information

### Queue Information

```python
# List available queues for a system
frontera_queues = client.systems.list_queues("frontera")
for queue in frontera_queues:
    print(f"Queue: {queue.name}")
    print(f"  Max runtime: {queue.maxRequestedTime} minutes")
    print(f"  Max nodes: {queue.maxNodesPerJob}")

# Check if specific queue exists
dev_queue_exists = any(q.name == "development" for q in frontera_queues)
print(f"Development queue available: {dev_queue_exists}")
```

### System Status

```python
# Get system information
try:
    queues = client.systems.list_queues("stampede3")
    print(f"Stampede3 has {len(queues)} available queues")
except Exception as e:
    print(f"Cannot access Stampede3: {e}")
```

## 🔧 Advanced Patterns

### Parametric Studies

```python
# Submit multiple jobs with different parameters
base_request = client.jobs.generate_request(
    app_id="mpm-s3",
    input_dir_uri=input_uri,
    script_filename="template.json",
    max_minutes=60,
    allocation="your_allocation"
)

# Parameter variations
parameters = [
    {"friction": 0.1, "density": 2000},
    {"friction": 0.2, "density": 2200},
    {"friction": 0.3, "density": 2400},
]

submitted_jobs = []
for i, params in enumerate(parameters):
    # Modify job request for this parameter set
    job_req = base_request.copy()
    job_req["name"] = f"parametric_study_{i:03d}"
    job_req["description"] = f"Friction: {params['friction']}, Density: {params['density']}"
    
    # Add parameters as environment variables
    if "parameterSet" not in job_req:
        job_req["parameterSet"] = {}
    if "envVariables" not in job_req["parameterSet"]:
        job_req["parameterSet"]["envVariables"] = []
    
    job_req["parameterSet"]["envVariables"].extend([
        {"key": "FRICTION", "value": str(params["friction"])},
        {"key": "DENSITY", "value": str(params["density"])}
    ])
    
    # Submit job
    job = client.jobs.submit_request(job_req)
    submitted_jobs.append(job)
    print(f"Submitted job {i+1}/{len(parameters)}: {job.uuid}")

# Monitor all jobs
print("Monitoring all jobs...")
for i, job in enumerate(submitted_jobs):
    print(f"\nMonitoring job {i+1}/{len(submitted_jobs)}: {job.uuid}")
    final_status = job.monitor()
    print(f"Job {i+1} final status: {final_status}")
```

### Job Dependencies

```python
# Submit jobs with dependencies (manual coordination)
# Job 1: Preprocessing
prep_job = client.jobs.submit_request(preprocessing_request)
prep_status = prep_job.monitor()

if prep_status == "FINISHED":
    print("Preprocessing complete, starting main analysis...")
    
    # Job 2: Main analysis (uses outputs from Job 1)
    main_request["fileInputs"].append({
        "name": "Preprocessed Data",
        "sourceUrl": prep_job.archive_uri,
        "targetPath": "preprocessed"
    })
    
    main_job = client.jobs.submit_request(main_request)
    main_status = main_job.monitor()
    
    if main_status == "FINISHED":
        print("Main analysis complete, starting postprocessing...")
        
        # Job 3: Postprocessing
        post_request["fileInputs"].append({
            "name": "Analysis Results",
            "sourceUrl": main_job.archive_uri,
            "targetPath": "results"
        })
        
        post_job = client.jobs.submit_request(post_request)
        final_status = post_job.monitor()
        
        print(f"Pipeline complete. Final status: {final_status}")
```

## 🚨 Error Handling

### Common Issues and Solutions

```python
from dapi import JobSubmissionError, JobMonitorError

try:
    # Job submission
    job = client.jobs.submit_request(job_request)
    final_status = job.monitor()
    
except JobSubmissionError as e:
    print(f"Job submission failed: {e}")
    
    # Check common issues
    if "allocation" in str(e).lower():
        print("💡 Check your TACC allocation is correct and active")
    elif "queue" in str(e).lower():
        print("💡 Check the queue name is valid for the system")
    elif "file" in str(e).lower():
        print("💡 Check input files exist and paths are correct")
        
except JobMonitorError as e:
    print(f"Job monitoring failed: {e}")
    
    # Try to get last known status
    try:
        status = job.get_status()
        print(f"Last known status: {status}")
    except:
        print("Cannot determine job status")

except Exception as e:
    print(f"Unexpected error: {e}")
```

### Debugging Failed Jobs

```python
# For failed jobs, get detailed error information
if final_status == "FAILED":
    print("🔍 Debugging failed job...")
    
    # Get error logs
    stderr = job.get_output_content("tapisjob.err", missing_ok=True)
    if stderr:
        print("Standard Error:")
        print(stderr)
    
    # Get last part of stdout
    stdout = job.get_output_content("tapisjob.out", max_lines=100)
    if stdout:
        print("Last 100 lines of output:")
        print(stdout)
    
    # Check job details
    details = job.details
    print(f"Last message: {details.lastMessage}")
    print(f"Status history available via: job.print_runtime_summary(verbose=True)")
```

## 💡 Best Practices

### 1. Resource Planning
```python
# ✅ Choose appropriate resources
job_request = client.jobs.generate_request(
    app_id="mpm-s3",
    input_dir_uri=input_uri,
    script_filename="analysis.json",
    max_minutes=60,        # Realistic time estimate
    node_count=1,          # Start small, scale up
    cores_per_node=24,     # Match application parallelism
    queue="development",   # Use dev queue for testing
    allocation="your_allocation"
)
```

### 2. Job Organization
```python
# ✅ Use descriptive names and metadata
job_request["name"] = f"seismic_analysis_{site_id}_{datetime.now().strftime('%Y%m%d_%H%M')}"
job_request["description"] = f"Seismic analysis for site {site_id} using {method} method"
job_request["tags"] = ["research", "seismic", site_id, method]
```

### 3. Error Recovery
```python
# ✅ Implement retry logic for transient failures
max_retries = 3
for attempt in range(max_retries):
    try:
        job = client.jobs.submit_request(job_request)
        final_status = job.monitor()
        break
    except JobSubmissionError as e:
        if attempt < max_retries - 1:
            print(f"Attempt {attempt + 1} failed, retrying... ({e})")
            time.sleep(60)  # Wait before retry
        else:
            raise
```

## ➡️ Next Steps

- **[Learn database access](database.md)** for research data integration
- **[Explore complete examples](examples/mpm.md)** showing real workflows  
- **Check API reference** for detailed method documentation
- **Review file operations** for data management