# OpenFOAM Job Submission Example

This example demonstrates how to submit and monitor an OpenFOAM CFD simulation using dapi. OpenFOAM is a free, open-source computational fluid dynamics (CFD) software package.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/openfoam/openfoam-minimal.ipynb)

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
ds_path: str = "/MyData/template-notebooks/tapis3/OpenFOAM/DH1_run" # Path to OpenFOAM case directory
max_job_minutes: int = 10 # Maximum runtime in minutes
tacc_allocation: str = "ASC25049" # TACC allocation to charge
app_id_to_use = "openfoam-stampede3" # OpenFOAM application ID

# OpenFOAM-specific environment variables
openfoam_env_vars = [
 {"key": "mesh", "value": "On"}, # Enable mesh generation with blockMesh
 {"key": "solver", "value": "pisoFoam"}, # CFD solver to use
 {"key": "decomp", "value": "On"} # Enable domain decomposition for parallel runs
]
```

OpenFOAM environment variables control the simulation workflow. The `mesh` key runs blockMesh to generate the computational mesh, `solver` selects the CFD solver (e.g., `pisoFoam` for transient incompressible flows, `simpleFoam` for steady-state RANS), and `decomp` enables parallel domain decomposition.

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
 max_minutes=max_job_minutes,
 allocation=tacc_allocation,
 archive_system="designsafe",
 extra_env_vars=openfoam_env_vars,
 input_dir_param_name="Case Directory" # OpenFOAM apps use "Case Directory" instead of "Input Directory"
)
print(json.dumps(job_dict, indent=2, default=str))
```

Note: OpenFOAM apps on DesignSafe expect `input_dir_param_name="Case Directory"` rather than the default `"Input Directory"`.

### Step 6: Customize Resources

```python
# Customize job settings (optional)
job_dict["nodeCount"] = 1 # Use single node
job_dict["coresPerNode"] = 2 # Use 2 cores for parallel simulation
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

### Extract Force Coefficients

```python
# Convert archive URI to local path for analysis
archive_path = ds.files.to_path(archive_uri)
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

Force coefficient columns: 0=Time, 1=Cm (moment), 2=Cd (drag), 3=Cl (lift), 4=Cl(f) (front lift), 5=Cl(r) (rear lift).

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
