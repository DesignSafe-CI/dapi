# MPM Job Submission Example

This example demonstrates how to submit and monitor a Material Point Method (MPM) simulation using dapi. MPM is a particle-based numerical method for simulating large deformation problems in geomechanics and fluid mechanics.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/mpm/mpm-minimal.ipynb)

## 🎯 Overview

This example covers the essential workflow for running MPM simulations:

- Installing and importing dapi
- Setting up MPM job parameters and input files
- Configuring analysis types, materials, and boundary conditions
- Submitting and monitoring MPM jobs
- Post-processing results and output analysis

## 🚀 Complete Example

### Step 1: Install and Import dapi

```python
# Install dapi package
!pip install dapi --user --quiet

# Import required modules
from dapi import DSClient
import json
```

**What this does:**
- Installs the DesignSafe API package from PyPI
- Imports the main client class and JSON for pretty-printing job requests

### Step 2: Initialize Client

```python
# Initialize DesignSafe client
ds = DSClient()
```

**What this does:**

- Creates an authenticated connection to DesignSafe services
- Handles OAuth2 authentication automatically
- Sets up connections to Tapis API, file systems, and job services

**Authentication:** dapi supports multiple authentication methods including environment variables, .env files, and interactive prompts. For detailed authentication setup instructions, see the [authentication guide](../authentication.md).

### Step 3: Configure Job Parameters

```python
# Job configuration parameters
ds_path: str = "/CommunityData/dapi/mpm/uniaxial_stress/"  # Path to MPM input files
input_filename: str = "mpm.json"  # Main MPM configuration file
max_job_minutes: int = 10  # Maximum runtime in minutes
tacc_allocation: str = "ASC25049"  # TACC allocation to charge
app_id_to_use = "mpm-s3"  # MPM application ID
```

**What each parameter does:**

- **`ds_path`**: DesignSafe path to your MPM case directory containing input files
- **`input_filename`**: Main MPM configuration file (typically .json format)
- **`max_job_minutes`**: Maximum wall-clock time for the job (prevents runaway simulations)
- **`tacc_allocation`**: Your TACC allocation account (required for compute time billing)
- **`app_id_to_use`**: Specific MPM application version on DesignSafe

**MPM input json file structure:**
```python
# Typical MPM configuration file contains:
mpm_config = {
    "mesh": "mesh.txt",           # Computational mesh definition
    "particles": "particles.txt", # Material point locations and properties
    "materials": {                # Material constitutive models
        "LinearElastic2D": "For elastic analysis",
        "MohrCoulomb": "For soil mechanics",
        "NeoHookean": "For large deformation"
    },
    "analysis": {
        "type": "MPMExplicit2D",  # Analysis type: 2D or 3D explicit
        "nsteps": 1000,           # Number of time steps
        "dt": 0.001               # Time step size
    }
}
```

### Step 4: Convert Path to URI

```python
# Convert DesignSafe path to Tapis URI format
input_uri = ds.files.translate_path_to_uri(ds_path)
print(f"Input Directory Tapis URI: {input_uri}")
```

**What this does:**

- Converts human-readable DesignSafe paths (like `/MyData/...`) to Tapis URI format
- Tapis URIs are required for job submission and follow the pattern: `tapis://system/path`
- Automatically detects your username and the correct storage system

### Step 5: Generate Job Request

```python
# Generate job request dictionary using app defaults
job_dict = ds.jobs.generate_request(
    app_id=app_id_to_use,
    input_dir_uri=input_uri,
    script_filename=input_filename,
    max_minutes=max_job_minutes,
    allocation=tacc_allocation,
    archive_system="designsafe",
    # MPM-specific job metadata
    job_name=f"mpm_uniaxial_stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    description="MPM simulation of uniaxial stress test",
    tags=["research", "mpm", "geomechanics", "uniaxial-stress"]
)
print(json.dumps(job_dict, indent=2, default=str))
```

**What each parameter does:**

- **`app_id`**: Specifies which MPM application to run
- **`input_dir_uri`**: Location of your MPM input files
- **`script_filename`**: Main MPM configuration file (mpm.json)
- **`max_minutes`**: Job timeout (prevents infinite runs)
- **`allocation`**: TACC account to charge for compute time
- **`archive_system`**: Where to store results ("designsafe" = your MyData folder)

**Additional options you can add:**

```python
# Extended job configuration options
job_dict = ds.jobs.generate_request(
    app_id=app_id_to_use,
    input_dir_uri=input_uri,
    script_filename=input_filename,
    max_minutes=max_job_minutes,
    allocation=tacc_allocation,
    
    # Resource configuration
    node_count=1,              # Number of compute nodes
    cores_per_node=48,         # Cores per node (max depends on system)
    memory_mb=192000,          # Memory in MB per node
    queue="skx-dev",           # Queue: "skx-dev", "skx", "normal", etc.
    
    # Job metadata
    job_name="my_mpm_simulation",                    # Custom job name
    description="Large deformation analysis",       # Job description
    tags=["research", "mpm", "geomechanics"],       # Searchable tags
    
    # Archive configuration
    archive_system="designsafe",                     # Where to store results
    archive_path="mpm-results",                     # Custom archive subdirectory
)
```

### Step 6: Customize Resources

```python
# Customize job settings (optional)
job_dict["nodeCount"] = 1  # Use single node
job_dict["coresPerNode"] = 1  # Use single core for small problems
print(json.dumps(job_dict, indent=2, default=str))
```

**What this does:**

- Overrides default resource allocation from the app
- `nodeCount`: Number of compute nodes (1 for small jobs, multiple for large simulations)
- `coresPerNode`: CPU cores per node (MPM can utilize parallel processing)
- More cores = faster solution but higher cost

**Resource guidelines:**
```python
# Resource selection guidelines for MPM
resources = {
    "small_case": {"nodes": 1, "cores": 1, "time": 30},      # < 10K particles
    "medium_case": {"nodes": 1, "cores": 16, "time": 120},   # 10K - 100K particles
    "large_case": {"nodes": 2, "cores": 48, "time": 480},    # > 100K particles
}
```

### Step 7: Submit Job

```python
# Submit the job to TACC
submitted_job = ds.jobs.submit_request(job_dict)
print(f"Job UUID: {submitted_job.uuid}")
```

**What this does:**

- Sends the job request to TACC's job scheduler
- Returns a `SubmittedJob` object for monitoring
- Job UUID is a unique identifier for tracking

### Step 8: Monitor Job

```python
# Monitor job execution until completion
final_status = submitted_job.monitor(interval=15)  # Check every 15 seconds
print(f"Job {submitted_job.uuid} finished with status: {final_status}")
```

**What this does:**

- Polls job status at specified intervals (15 seconds)
- Shows progress bars for different job phases
- Returns final status when job completes
- `interval=15` means check every 15 seconds (can be adjusted)

**Job status meanings:**
```python
job_statuses = {
    "PENDING": "Job submitted but not yet processed",
    "PROCESSING_INPUTS": "Input files being staged",
    "QUEUED": "Job waiting in scheduler queue",
    "RUNNING": "Job actively executing",
    "ARCHIVING": "Output files being archived",
    "FINISHED": "Job completed successfully",
    "FAILED": "Job failed during execution"
}
```

### Step 9: Check Results

```python
# Interpret and display job outcome
ds.jobs.interpret_status(final_status, submitted_job.uuid)

# Display job runtime summary
submitted_job.print_runtime_summary(verbose=False)

# Get current job status
current_status = ds.jobs.get_status(submitted_job.uuid)
print(f"Current status: {current_status}")

# Display last status message from TACC
print(f"Last message: {submitted_job.last_message}")
```

**What each command does:**

- **`interpret_status`**: Provides human-readable explanation of job outcome
- **`print_runtime_summary`**: Shows time spent in each job phase (queued, running, etc.)
- **`get_status`**: Gets current job status (useful for checking later)
- **`last_message`**: Shows last status message from the job scheduler

### Step 10: View Job Output

```python
# Display job output from stdout
stdout_content = submitted_job.get_output_content("tapisjob.out", max_lines=50)
if stdout_content:
    print("Job output:")
    print(stdout_content)
```

**What this does:**
- `tapisjob.out` contains all console output from your MPM simulation
- `max_lines=50` limits output to last 50 lines (prevents overwhelming output)
- Shows MPM solver progress, timestep information, and timing data

**Typical MPM output includes:**
```python
# Example MPM console output:
mpm_output_info = {
    "git_revision": "Version information",
    "step_progress": "Step: 1 of 1000",
    "warnings": "Material sets, boundary conditions",
    "solver_duration": "Explicit USF solver duration: 285 ms",
    "completion": "Job execution finished"
}
```

### Step 11: Access Results

```python
# List contents of job archive directory
archive_uri = submitted_job.archive_uri
print(f"Archive URI: {archive_uri}")
outputs = ds.files.list(archive_uri)
for item in outputs:
    print(f"- {item.name} ({item.type})")
```

**What this does:**
- **`archive_uri`**: Location where job results are stored
- **`ds.files.list`**: Lists all files and directories in the archive
- Shows output files like simulation results, visualization data, and logs

**Typical MPM output files:**
```python
typical_outputs = {
    "inputDirectory/": "Copy of your input directory with results",
    "tapisjob.out": "Console output from MPM simulation",
    "tapisjob.err": "Error messages (if any)",
    "tapisjob.sh": "Job script that was executed",
    "results/": "VTK files for visualization (particles, stresses, velocities)",
    "*.vtu": "Paraview-compatible visualization files"
}
```

## 📊 Post-processing Results

### Extract and Analyze Output

```python
# Convert archive URI to local path for analysis
archive_path = ds.files.translate_uri_to_path(archive_uri)
print(f"Archive path: {archive_path}")

# Import analysis libraries
import numpy as np
import matplotlib.pyplot as plt
import os

# Navigate to results directory
results_path = os.path.join(archive_path, "inputDirectory", "results")
if os.path.exists(results_path):
    print(f"Results directory: {results_path}")
    
    # List VTK output files
    vtk_files = [f for f in os.listdir(results_path) if f.endswith('.vtu')]
    print(f"Found {len(vtk_files)} VTK files for visualization")
    
    # Example: Load and analyze particle data (requires appropriate library)
    # Note: Actual VTK analysis would require packages like vtk or pyvista
    print("Use ParaView or Python VTK libraries to visualize results")
else:
    print("No results directory found - check job completion status")
```

**What this does:**

- **`translate_uri_to_path`**: Converts Tapis URI to local file system path
- **`os.listdir`**: Lists files in the results directory
- **`.vtu files`**: VTK unstructured grid files for visualization
- **ParaView**: Recommended tool for visualizing MPM particle data