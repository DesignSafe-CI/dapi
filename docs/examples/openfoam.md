# OpenFOAM Job Submission Example

This example demonstrates how to submit and monitor an OpenFOAM CFD simulation using dapi. OpenFOAM is a free, open-source computational fluid dynamics (CFD) software package.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/openfoam/openfoam-minimal.ipynb)

## 🎯 Overview

This example covers the essential workflow for running OpenFOAM simulations:

- Installing and importing dapi
- Setting up OpenFOAM job parameters
- Configuring solvers, mesh generation, and decomposition
- Submitting and monitoring CFD jobs
- Post-processing results with force coefficient analysis

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

### Step 3: Configure Job Parameters

```python
# Job configuration parameters
ds_path: str = "/MyData/template-notebooks/tapis3/OpenFOAM/DH1_run"  # Path to OpenFOAM case directory
max_job_minutes: int = 10  # Maximum runtime in minutes
tacc_allocation: str = "ASC25049"  # TACC allocation to charge
app_id_to_use = "openfoam-stampede3"  # OpenFOAM application ID

# OpenFOAM-specific environment variables
openfoam_env_vars = [
    {"key": "mesh", "value": "On"},      # Enable mesh generation with blockMesh
    {"key": "solver", "value": "pisoFoam"},  # CFD solver to use
    {"key": "decomp", "value": "On"}      # Enable domain decomposition for parallel runs
]
```

**What each parameter does:**

- **`ds_path`**: DesignSafe path to your OpenFOAM case directory containing 0/, constant/, and system/ folders
- **`max_job_minutes`**: Maximum wall-clock time for the job (prevents runaway simulations)
- **`tacc_allocation`**: Your TACC allocation account (required for compute time billing)
- **`app_id_to_use`**: Specific OpenFOAM application version on DesignSafe
- **`openfoam_env_vars`**: OpenFOAM-specific configuration:
  - `mesh: "On"` - Runs blockMesh to generate computational mesh
  - `solver: "pisoFoam"` - Transient, incompressible Navier-Stokes solver
  - `decomp: "On"` - Enables parallel domain decomposition for multi-core runs

**Alternative solver options:**
```python
# Different OpenFOAM solvers you can use
solvers = {
    "pisoFoam": "Transient, incompressible (general purpose)",
    "simpleFoam": "Steady-state, incompressible (RANS)",
    "pimpleFoam": "Transient, incompressible (large time steps)",
    "rhoSimpleFoam": "Steady-state, compressible",
    "sonicFoam": "Transient, compressible (high speed flows)"
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
    max_minutes=max_job_minutes,
    allocation=tacc_allocation,
    archive_system="designsafe",
    extra_env_vars=openfoam_env_vars,
    input_dir_param_name="Case Directory"  # OpenFOAM apps use "Case Directory" instead of "Input Directory"
)
print(json.dumps(job_dict, indent=2, default=str))
```

**What each parameter does:**

- **`app_id`**: Specifies which application to run
- **`input_dir_uri`**: Location of your OpenFOAM case files
- **`max_minutes`**: Job timeout (prevents infinite runs)
- **`allocation`**: TACC account to charge for compute time
- **`archive_system`**: Where to store results ("designsafe" = your MyData folder)
- **`extra_env_vars`**: OpenFOAM-specific settings passed to the application
- **`input_dir_param_name`**: OpenFOAM apps expect "Case Directory" not "Input Directory"

**Additional options you can add:**
```python
# Extended job configuration options
job_dict = ds.jobs.generate_request(
    app_id=app_id_to_use,
    input_dir_uri=input_uri,
    max_minutes=max_job_minutes,
    allocation=tacc_allocation,
    
    # Resource configuration
    node_count=2,              # Number of compute nodes
    cores_per_node=48,         # Cores per node (max depends on system)
    memory_mb=96000,           # Memory in MB per node
    queue="normal",            # Queue: "development", "normal", "large", etc.
    
    # Job metadata
    job_name="my_cfd_simulation",                    # Custom job name
    description="Wind flow around building",        # Job description
    tags=["research", "cfd", "wind-engineering"],   # Searchable tags
    
    # Archive configuration
    archive_system="designsafe",                     # Where to store results
    archive_path="openfoam-results",                # Custom archive subdirectory
    
    # Additional environment variables
    extra_env_vars=[
        {"key": "mesh", "value": "On"},
        {"key": "solver", "value": "pisoFoam"},
        {"key": "decomp", "value": "On"},
        {"key": "OMP_NUM_THREADS", "value": "4"}     # OpenMP threads per MPI process
    ]
)
```

### Step 6: Customize Resources

```python
# Customize job settings (optional)
job_dict["nodeCount"] = 1  # Use single node
job_dict["coresPerNode"] = 2  # Use 2 cores for parallel simulation
print(json.dumps(job_dict, indent=2, default=str))
```

**What this does:**
- Overrides default resource allocation from the app
- `nodeCount`: Number of compute nodes (1 for small jobs, multiple for large simulations)
- `coresPerNode`: CPU cores per node (enables parallel processing)
- More cores = faster solution but higher cost

**Resource guidelines:**
```python
# Resource selection guidelines
resources = {
    "small_case": {"nodes": 1, "cores": 2, "time": 30},      # < 100K cells
    "medium_case": {"nodes": 1, "cores": 16, "time": 120},   # 100K - 1M cells
    "large_case": {"nodes": 2, "cores": 48, "time": 480},    # > 1M cells
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
- `tapisjob.out` contains all console output from your OpenFOAM simulation
- `max_lines=50` limits output to last 50 lines (prevents overwhelming output)
- Shows OpenFOAM solver progress, residuals, and timing information

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
- Shows output files like mesh, solution fields, and post-processing data

**Typical OpenFOAM output files:**
```python
typical_outputs = {
    "inputDirectory/": "Copy of your case directory with results",
    "tapisjob.out": "Console output from OpenFOAM",
    "tapisjob.err": "Error messages (if any)",
    "tapisjob.sh": "Job script that was executed",
    "postProcessing/": "Force coefficients, residuals, monitoring data",
    "processor*/": "Parallel decomposed solution (if using multiple cores)"
}
```

## 📊 Post-processing Results

### Extract Force Coefficients

```python
# Convert archive URI to local path for analysis
archive_path = ds.files.translate_uri_to_path(archive_uri)
print(f"Archive path: {archive_path}")

# Import plotting libraries
import numpy as np
import matplotlib.pyplot as plt
import os

# Load force coefficient data using pandas
import pandas as pd

force_data_path = archive_path + "/inputDirectory/postProcessing/forceCoeffs1/0/forceCoeffs.dat"

# Read the file, skipping header lines and using tab separator
data = pd.read_csv(force_data_path, sep='\t', skiprows=9, header=None)
print(f"Loaded force coefficients data with shape: {data.shape}")
```

**What this does:**
- **`translate_uri_to_path`**: Converts Tapis URI to local file system path
- **`pandas.read_csv`**: Reads force coefficient data (much cleaner than manual parsing)
- **`skiprows=9`**: Skips OpenFOAM header lines
- **`sep='\t'`**: Uses tab separator (OpenFOAM default)

**Force coefficient file format:**
```python
# Column meanings in forceCoeffs.dat
columns = {
    0: "Time",
    1: "Cm (moment coefficient)",
    2: "Cd (drag coefficient)",
    3: "Cl (lift coefficient)", 
    4: "Cl(f) (front lift)",
    5: "Cl(r) (rear lift)"
}
```

### Plot Results

```python
# Plot drag coefficient (Cd) vs time
plt.plot(data.iloc[100:, 0], data.iloc[100:, 2])
plt.xlabel('Time')
plt.ylabel('$C_d$')
plt.title('Drag Coefficient vs Time')
plt.grid(True)
plt.show()

# Plot lift coefficient (Cl) vs time  
plt.plot(data.iloc[100:, 0], data.iloc[100:, 3])
plt.xlabel('Time')
plt.ylabel('$C_l$')
plt.title('Lift Coefficient vs Time')
plt.grid(True)
plt.show()
```

**What this does:**
- **`data.iloc[100:, 0]`**: Time values (column 0) starting from row 100
- **`data.iloc[100:, 2]`**: Drag coefficient values (column 2)
- **`[100:]`**: Skips initial transient period for cleaner plots
- Creates separate plots for drag and lift coefficients

**Advanced plotting options:**
```python
# Create subplots for better comparison
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(data.iloc[100:, 0], data.iloc[100:, 2], 'b-', linewidth=2)
plt.xlabel('Time (s)')
plt.ylabel('$C_d$ (Drag Coefficient)')
plt.title('Drag Coefficient vs Time')
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.plot(data.iloc[100:, 0], data.iloc[100:, 3], 'r-', linewidth=2)
plt.xlabel('Time (s)')
plt.ylabel('$C_l$ (Lift Coefficient)')
plt.title('Lift Coefficient vs Time')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Calculate final values
final_cd = float(data.iloc[-1, 2])
final_cl = float(data.iloc[-1, 3])
print(f"Final drag coefficient: {final_cd:.6f}")
print(f"Final lift coefficient: {final_cl:.6f}")
```

## 🔧 Configuration Options

### Environment Variable Options

```python
# Complete list of OpenFOAM environment variables
openfoam_options = [
    {"key": "mesh", "value": "On"},        # Generate mesh with blockMesh
    {"key": "solver", "value": "pisoFoam"}, # Solver selection
    {"key": "decomp", "value": "On"},       # Enable parallel decomposition
    {"key": "reconstruct", "value": "On"},  # Reconstruct parallel results
    {"key": "postProcess", "value": "On"},  # Run post-processing functions
]
```

### Queue and System Options

```python
# Available queues on different systems
queue_options = {
    "stampede3": {
        "development": {"max_nodes": 2, "max_time": 120},    # 2 hours, testing
        "normal": {"max_nodes": 256, "max_time": 2880},      # 48 hours, production
        "large": {"max_nodes": 512, "max_time": 1440},       # 24 hours, large jobs
    }
}

# System-specific configurations
systems = {
    "stampede3": {"cores_per_node": 48, "memory_per_node": 192000},
    "frontera": {"cores_per_node": 56, "memory_per_node": 192000},
}
```

### Complete Job Request Example

```python
# Full-featured job request showing all options
complete_job = ds.jobs.generate_request(
    # Required parameters
    app_id="openfoam-stampede3",
    input_dir_uri=input_uri,
    allocation="YOUR_ALLOCATION",
    
    # Resource configuration
    max_minutes=120,           # 2 hours
    node_count=2,              # Multiple nodes
    cores_per_node=48,         # Full node utilization
    memory_mb=192000,          # 192 GB RAM
    queue="normal",            # Production queue
    
    # Job metadata
    job_name="wind_flow_cfd_simulation",
    description="RANS simulation of wind flow around building using OpenFOAM",
    tags=["research", "cfd", "wind-engineering", "rans", "openfoam"],
    
    # Archive configuration
    archive_system="designsafe",
    archive_path="cfd-results/wind-study",  # Results go to MyData/cfd-results/wind-study/
    
    # OpenFOAM configuration
    extra_env_vars=[
        {"key": "mesh", "value": "On"},
        {"key": "solver", "value": "simpleFoam"},    # Steady-state RANS
        {"key": "decomp", "value": "On"},
        {"key": "reconstruct", "value": "On"},
        {"key": "postProcess", "value": "On"},
    ],
    
    # Advanced options
    input_dir_param_name="Case Directory",
)
```

This streamlined approach focuses on the essential workflow while explaining what each step accomplishes, making it easy to understand and modify for different OpenFOAM simulations.