# OpenSees Job Submission Example

This comprehensive example demonstrates how to submit and monitor an OpenSees job using dapi. OpenSees is a software framework for developing applications to simulate earthquake engineering applications, featuring finite element analysis capabilities for structural and geotechnical systems.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/opensees/opensees-mp/OpenSeesMP-dapi.ipynb)

## 🎯 Overview

This example covers:

- Setting up authentication and environment
- Configuring OpenSees Multi-Free Field Analysis
- Managing input files and DesignSafe paths
- Generating job requests with custom archive settings
- Submitting and monitoring OpenSees jobs
- Downloading and postprocessing results with plotting

## 🚀 Complete Example

### Step 1: Setup and Authentication

```python
# Install required packages
!pip install dapi

# Import DAPI and other required libraries
from dapi import DSClient
import os
import json
import tempfile
import shutil
import numpy as np
import matplotlib.pyplot as plt
from datetime import date

# Initialize DesignSafe client
ds = DSClient()
print("Authentication successful.")
```

### Step 2: Configure Job Parameters

```python
# Define DesignSafe paths and job configuration
ds_path = "/home/jupyter/MyData/template-notebooks/tapis3/opensees/OpenSeesMP_multiMotion/DS_input"
print(f"DesignSafe path: {ds_path}")

# Translate DesignSafe path to Tapis URI
input_uri = ds.files.translate_path_to_uri(ds_path)
print(f"Input URI: {input_uri}")

# Job configuration parameters
jobname: str = "opensees-MP-multiMotion-dapi"
app_id: str = "opensees-mp-s3"
input_filename: str = "Main_multiMotion.tcl"
control_exec_Dir: str = "DS_input"  # Folder with files including input_filename
tacc_allocation: str = "ASC25049"  # MUST USE YOUR OWN ALLOCATION !!
control_nodeCount: int = 1
control_corespernode: int = 16
max_job_minutes: int = 60
```

### Step 3: Generate Job Request with Custom Archive Settings

```python
# Generate job request dictionary using app defaults
job_dict = ds.jobs.generate_request(
    app_id=app_id,
    input_dir_uri=input_uri,
    script_filename=input_filename,
    max_minutes=max_job_minutes,
    allocation=tacc_allocation,
    # Archive configuration for organized result storage
    archive_system="designsafe",
    archive_path="opensees-results",  # Results go to MyData/opensees-results/
)

# Customize job settings
job_dict["name"] = jobname
job_dict["nodeCount"] = control_nodeCount
job_dict["coresPerNode"] = control_corespernode

print("Generated job request:")
print(json.dumps(job_dict, indent=2, default=str))
```

### Step 4: Submit and Monitor Job

```python
# Submit job using dapi
submitted_job = ds.jobs.submit_request(job_dict)
print(f"Job launched with UUID: {submitted_job.uuid}")
print("Can also check in DesignSafe portal under - Workspace > Tools & Application > Job Status")

# Monitor job status using dapi
final_status = submitted_job.monitor(interval=15)
print(f"Job finished with status: {final_status}")

# Interpret job status
ds.jobs.interpret_status(final_status, submitted_job.uuid)

# Display runtime summary
submitted_job.print_runtime_summary(verbose=False)
```

### Step 5: Access Job Archive and Results

```python
# Get archive information using dapi
archive_uri = submitted_job.archive_uri
print(f"Archive URI: {archive_uri}")

# Translate archive URI to local DesignSafe path
local_archive_path = ds.files.translate_uri_to_path(archive_uri)
print(f"Local archive path: {local_archive_path}")

# List archive contents
archive_files = ds.files.list(archive_uri)
print("\\nArchive contents:")
for item in archive_files:
    print(f"- {item.name} ({item.type})")
```

### Step 6: Download Results for Postprocessing

```python
# Download archive files to local directory for postprocessing
import tempfile
import shutil

# Create temporary directory for downloaded files
temp_dir = tempfile.mkdtemp(prefix="opensees_results_")
print(f"Downloading results to: {temp_dir}")

# Download the inputDirectory folder which contains results
input_dir_archive_uri = f"{archive_uri}/inputDirectory"
try:
    # List contents of inputDirectory in archive
    input_dir_files = ds.files.list(input_dir_archive_uri)
    print("\\nFiles in inputDirectory:")
    for item in input_dir_files:
        print(f"- {item.name} ({item.type})")
    
    # Download all files from inputDirectory (excluding subdirectories)
    files_to_download = [item.name for item in input_dir_files if item.type == "file"]
    
    print(f"\\nDownloading {len(files_to_download)} files...")
    successful_downloads = []
    
    for filename in files_to_download:
        try:
            file_uri = f"{input_dir_archive_uri}/{filename}"
            local_path = os.path.join(temp_dir, filename)
            
            # Try downloading with the ds.files.download method
            try:
                ds.files.download(file_uri, local_path)
                print(f"Downloaded: {filename}")
                successful_downloads.append(filename)
            except Exception as download_error:
                print(f"Standard download failed for {filename}: {download_error}")
                
                # Try alternative download approach using get_file_content
                try:
                    content = ds.files.get_file_content(file_uri)
                    with open(local_path, 'wb') as f:
                        if hasattr(content, 'read'):
                            shutil.copyfileobj(content, f)
                        else:
                            f.write(content)
                    print(f"Downloaded (alternative method): {filename}")
                    successful_downloads.append(filename)
                except Exception as alt_error:
                    print(f"Alternative download also failed for {filename}: {alt_error}")
                    
        except Exception as e:
            print(f"Could not download {filename}: {e}")
    
    print(f"\\nSuccessfully downloaded {len(successful_downloads)} out of {len(files_to_download)} files")
            
except Exception as e:
    print(f"Error accessing archive: {e}")

# Change to the temporary directory for postprocessing
os.chdir(temp_dir)
print(f"\\nChanged to directory: {os.getcwd()}")
print("Local files:")
for f in sorted(os.listdir(".")):
    print(f"- {f}")
```

### Step 7: Install Plotting Dependencies and Setup

```python
# Install matplotlib for plotting
!pip3 install matplotlib

# Setup matplotlib for inline plotting
%matplotlib inline
import numpy as np
import matplotlib.pyplot as plt
```

### Step 8: Create Postprocessing Functions

```python
# Define response spectra function inline
def resp_spectra(a, time, nstep):
    """
    This function builds response spectra from acceleration time history,
    a should be a numpy array, T and nStep should be integers.
    """
    # add initial zero value to acceleration and change units
    a = np.insert(a, 0, 0)
    # number of periods at which spectral values are to be computed
    nperiod = 100
    # define range of considered periods by power of 10
    minpower = -3.0
    maxpower = 1.0
    # create vector of considered periods
    p = np.logspace(minpower, maxpower, nperiod)
    # incremental circular frequency
    dw = 2.0 * np.pi / time
    # vector of circular freq
    w = np.arange(0, (nstep + 1) * dw, dw)
    # fast fourier transform of acceleration
    afft = np.fft.fft(a)
    # arbitrary stiffness value
    k = 1000.0
    # damping ratio
    damp = 0.05
    umax = np.zeros(nperiod)
    vmax = np.zeros(nperiod)
    amax = np.zeros(nperiod)
    # loop to compute spectral values at each period
    for j in range(0, nperiod):
        # compute mass and dashpot coeff to produce desired periods
        m = ((p[j] / (2 * np.pi)) ** 2) * k
        c = 2 * damp * (k * m) ** 0.5
        h = np.zeros(nstep + 2, dtype=complex)
        # compute transfer function
        for l in range(0, int(nstep / 2 + 1)):
            h[l] = 1.0 / (-m * w[l] * w[l] + 1j * c * w[l] + k)
            # mirror image of transfer function
            h[nstep + 1 - l] = np.conj(h[l])

        # compute displacement in frequency domain using transfer function
        qfft = -m * afft
        u = np.zeros(nstep + 1, dtype=complex)
        for l in range(0, nstep + 1):
            u[l] = h[l] * qfft[l]

        # compute displacement in time domain (ignore imaginary part)
        utime = np.real(np.fft.ifft(u))

        # spectral displacement, velocity, and acceleration
        umax[j] = np.max(np.abs(utime))
        vmax[j] = (2 * np.pi / p[j]) * umax[j]
        amax[j] = (2 * np.pi / p[j]) * vmax[j]

    return p, umax, vmax, amax

# Define plot_acc function inline
def plot_acc():
    """
    Plot acceleration time history and response spectra
    """
    plt.figure()

    for motion in ["motion1"]:
        for profile in ["A", "B", "C", "D"]:
            acc = np.loadtxt("Profile" + profile + "_acc" + motion + ".out")
            [p, umax, vmax, amax] = resp_spectra(acc[:, -1], acc[-1, 0], acc.shape[0])
            plt.semilogx(p, amax)

    # response spectra on log-linear plot

    plt.ylabel("$S_a (g)$")
    plt.xlabel("$Period (s)$")

# Execute the plotting function
plot_acc()
```

This comprehensive OpenSees example demonstrates the complete workflow for submitting, monitoring, and analyzing OpenSees simulations using dapi, including advanced features like custom archive management, parametric studies, and detailed result postprocessing with response spectra analysis.