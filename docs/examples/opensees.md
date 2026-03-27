# OpenSees Job Submission Example

This example demonstrates how to submit and monitor an OpenSees simulation using dapi. OpenSees is a software framework for developing applications to simulate earthquake engineering applications, featuring finite element analysis capabilities for structural and geotechnical systems.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/opensees/opensees-mp/OpenSeesMP-dapi.ipynb)

For general job submission concepts, see [Jobs](../jobs.md). For resource sizing, see [DesignSafe Workflows](https://kks32.github.io/ds-workflows/guide/job-resources.html).

## Complete Example

### Step 1: Install and Import dapi

```python
# Install dapi package
%pip install dapi --quiet

# Import required modules
from dapi import DSClient
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import date
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
ds_path = os.getcwd() + "/input" # Path to OpenSees input files
input_filename: str = "Main_multiMotion.tcl" # Main OpenSees script
tacc_allocation: str = "your-allocation" # TACC allocation to charge
app_id: str = "opensees-mp-s3" # OpenSees-MP application ID
max_job_minutes: int = 60 # Maximum runtime in minutes

# Resource configuration
control_nodeCount: int = 1 # Number of compute nodes
control_corespernode: int = 16 # Cores per node for parallel analysis
```

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
 app_id=app_id,
 input_dir_uri=input_uri,
 script_filename=input_filename,
 max_minutes=max_job_minutes,
 allocation=tacc_allocation,
 # Archive configuration for organized result storage
 archive_system="designsafe",
 archive_path="opensees-results", # Results go to MyData/opensees-results/
 # OpenSees-specific job metadata
 job_name="opensees_multi_motion_analysis",
 description="Multi-free field analysis using OpenSees-MP",
 tags=["research", "opensees", "earthquake", "site-response"]
)
print(json.dumps(job_dict, indent=2, default=str))
```

### Step 6: Customize Resources

```python
# Customize job settings
job_dict["name"] = "opensees-MP-multiMotion-dapi"
job_dict["nodeCount"] = control_nodeCount
job_dict["coresPerNode"] = control_corespernode

print("Generated job request:")
print(json.dumps(job_dict, indent=2, default=str))
```

**Resource guidelines:**
Visit [OpenSees userguide on DesignSafe](https://www.designsafe-ci.org/user-guide/tools/simulation/opensees/opensees/#decision-matrix-for-opensees-applications)

### Step 7: Submit Job

```python
# Submit job using dapi
submitted_job = ds.jobs.submit(job_dict)
print(f"Job launched with UUID: {submitted_job.uuid}")
print("Can also check in DesignSafe portal under - Workspace > Tools & Application > Job Status")
```

### Step 8: Monitor Job

```python
# Monitor job status using dapi
final_status = submitted_job.monitor(interval=15) # Check every 15 seconds
print(f"Job finished with status: {final_status}")
```

### Step 9: Check Results

```python
# Interpret job status
ds.jobs.interpret_status(final_status, submitted_job.uuid)

# Display runtime summary
submitted_job.print_runtime_summary(verbose=False)

# Get current job status
current_status = ds.jobs.status(submitted_job.uuid)
print(f"Current status: {current_status}")

# Display last status message from TACC
print(f"Last message: {submitted_job.last_message}")
```

### Step 10: Access Job Archive and Results

```python
# Get archive information using dapi
archive_uri = submitted_job.archive_uri
print(f"Archive URI: {archive_uri}")

# Translate archive URI to local DesignSafe path
local_archive_path = ds.files.to_path(archive_uri)
print(f"Local archive path: {local_archive_path}")

# List archive contents
archive_files = ds.files.list(archive_uri)
print("\nArchive contents:")
for item in archive_files:
 print(f"- {item.name} ({item.type})")
```

### Step 11: Access Results from Input Directory

```python
# Download the inputDirectory folder which contains results
input_dir_archive_uri = f"{archive_uri}/inputDirectory"
try:
 # List contents of inputDirectory in archive
 input_dir_files = ds.files.list(input_dir_archive_uri)
 print("\nFiles in inputDirectory:")
 for item in input_dir_files:
 print(f"- {item.name} ({item.type})")

 # Change to the archive directory for post-processing
 archive_path = ds.files.to_path(input_dir_archive_uri)
 os.chdir(archive_path)
 print(f"\nChanged to directory: {archive_path}")

except Exception as e:
 print(f"Error accessing archive: {e}")
```

## Post-processing Results

### Response Spectra Analysis

```python
# Define response spectra function
def resp_spectra(a, time, nstep):
 """
 This function builds response spectra from acceleration time history,
 a should be a numpy array, T and nStep should be integers.
 """
 # Add initial zero value to acceleration
 a = np.insert(a, 0, 0)
 # Number of periods at which spectral values are computed
 nperiod = 100
 # Define range of considered periods by power of 10
 minpower = -3.0
 maxpower = 1.0
 # Create vector of considered periods
 p = np.logspace(minpower, maxpower, nperiod)
 # Incremental circular frequency
 dw = 2.0 * np.pi / time
 # Vector of circular frequency
 w = np.arange(0, (nstep + 1) * dw, dw)
 # Fast fourier transform of acceleration
 afft = np.fft.fft(a)
 # Arbitrary stiffness value
 k = 1000.0
 # Damping ratio
 damp = 0.05
 umax = np.zeros(nperiod)
 vmax = np.zeros(nperiod)
 amax = np.zeros(nperiod)

 # Loop to compute spectral values at each period
 for j in range(0, nperiod):
 # Compute mass and dashpot coefficient for desired periods
 m = ((p[j] / (2 * np.pi)) ** 2) * k
 c = 2 * damp * (k * m) ** 0.5
 h = np.zeros(nstep + 2, dtype=complex)

 # Compute transfer function
 for l in range(0, int(nstep / 2 + 1)):
 h[l] = 1.0 / (-m * w[l] * w[l] + 1j * c * w[l] + k)
 # Mirror image of transfer function
 h[nstep + 1 - l] = np.conj(h[l])

 # Compute displacement in frequency domain using transfer function
 qfft = -m * afft
 u = np.zeros(nstep + 1, dtype=complex)
 for l in range(0, nstep + 1):
 u[l] = h[l] * qfft[l]

 # Compute displacement in time domain (ignore imaginary part)
 utime = np.real(np.fft.ifft(u))

 # Spectral displacement, velocity, and acceleration
 umax[j] = np.max(np.abs(utime))
 vmax[j] = (2 * np.pi / p[j]) * umax[j]
 amax[j] = (2 * np.pi / p[j]) * vmax[j]

 return p, umax, vmax, amax
```

### Plot Response Spectra

```python
# Define plotting function
def plot_acc():
 """
 Plot acceleration response spectra on log-linear scale
 """
 plt.figure(figsize=(10, 6))

 # Plot response spectra for each profile
 for motion in ["motion1"]:
 for profile in ["A", "B", "C", "D"]:
 try:
 # Load acceleration data
 acc = np.loadtxt(f"Profile{profile}_acc{motion}.out")

 # Compute response spectra
 [p, umax, vmax, amax] = resp_spectra(acc[:, -1], acc[-1, 0], acc.shape[0])

 # Plot spectral acceleration
 plt.semilogx(p, amax, label=f"Profile {profile}", linewidth=2)

 except FileNotFoundError:
 print(f"File Profile{profile}_acc{motion}.out not found")

 # Format plot
 plt.ylabel("$S_a$ (g)")
 plt.xlabel("Period (s)")
 plt.title("Acceleration Response Spectra (5% Damping)")
 plt.grid(True, alpha=0.3)
 plt.legend()
 plt.xlim([0.01, 10])
 plt.show()

# Execute the plotting function
plot_acc()
```

### Advanced Post-processing

```python
# Analyze stress time histories
def analyze_stress_results():
 """
 Analyze stress time histories from OpenSees output
 """
 stress_files = [f for f in os.listdir('.') if 'Gstress' in f and f.endswith('.out')]

 print(f"Found {len(stress_files)} stress output files:")
 for file in stress_files:
 print(f"- {file}")

 # Load stress data
 try:
 stress_data = np.loadtxt(file)

 # Basic statistics
 max_stress = np.max(np.abs(stress_data[:, 1:])) # Skip time column
 print(f"Maximum stress magnitude: {max_stress:.2f}")

 # Plot time history
 plt.figure(figsize=(10, 4))
 plt.plot(stress_data[:, 0], stress_data[:, 1], label='Shear Stress')
 plt.xlabel('Time (s)')
 plt.ylabel('Stress (kPa)')
 plt.title(f'Stress Time History - {file}')
 plt.grid(True, alpha=0.3)
 plt.legend()
 plt.show()

 except Exception as e:
 print(f"Error loading {file}: {e}")

# Run stress analysis
analyze_stress_results()
```
