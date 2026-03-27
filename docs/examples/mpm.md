# MPM Job Submission Example

This example demonstrates how to submit and monitor a Material Point Method (MPM) simulation using dapi. MPM is a particle-based numerical method for simulating large deformation problems in geomechanics and fluid mechanics.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/mpm/mpm-minimal.ipynb)

For general job submission concepts, see [Jobs](../jobs.md). For resource sizing, see [DesignSafe Workflows](https://kks32.github.io/ds-workflows/guide/job-resources.html).

## Complete Example

### Step 1: Install and Import dapi

```python
# Install dapi package
%pip install dapi --quiet

# Import required modules
from dapi import DSClient
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
ds_path: str = "/CommunityData/dapi/mpm/uniaxial_stress/" # Path to MPM input files
input_filename: str = "mpm.json" # Main MPM configuration file
max_job_minutes: int = 10 # Maximum runtime in minutes
tacc_allocation: str = "ASC25049" # TACC allocation to charge
app_id_to_use = "mpm-s3" # MPM application ID
```

The MPM input file is a JSON configuration that defines the mesh, particle locations, material constitutive models (e.g., LinearElastic2D, MohrCoulomb, NeoHookean), and analysis parameters (type, number of steps, time step size).

### Step 4: Convert Path to URI

```python
# Convert DesignSafe path to Tapis URI format
input_uri = ds.files.to_uri(ds_path)
print(f"Input Directory Tapis URI: {input_uri}")
```

### Step 5: Generate Job Request

```python
# Generate job request dictionary using app defaults
job_dict = ds.jobs.generate(
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

### Step 6: Customize Resources

```python
# Customize job settings (optional)
job_dict["nodeCount"] = 1 # Use single node
job_dict["coresPerNode"] = 1 # Use single core for small problems
print(json.dumps(job_dict, indent=2, default=str))
```

### Step 7: Submit Job

```python
# Submit the job to TACC
submitted_job = ds.jobs.submit(job_dict)
print(f"Job UUID: {submitted_job.uuid}")
```

### Step 8: Monitor Job

```python
# Monitor job execution until completion
final_status = submitted_job.monitor(interval=15) # Check every 15 seconds
print(f"Job {submitted_job.uuid} finished with status: {final_status}")
```

### Step 9: Check Results

```python
# Interpret and display job outcome
ds.jobs.interpret_status(final_status, submitted_job.uuid)

# Display job runtime summary
submitted_job.print_runtime_summary(verbose=False)

# Get current job status
current_status = ds.jobs.status(submitted_job.uuid)
print(f"Current status: {current_status}")

# Display last status message from TACC
print(f"Last message: {submitted_job.last_message}")
```

### Step 10: View Job Output

```python
# Display job output from stdout
stdout_content = submitted_job.get_output_content("tapisjob.out", max_lines=50)
if stdout_content:
 print("Job output:")
 print(stdout_content)
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

## Post-processing Results

### Extract and Analyze Output

```python
# Convert archive URI to local path for analysis
archive_path = ds.files.to_path(archive_uri)
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
