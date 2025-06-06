# Quick Start

Get up and running with dapi in just a few minutes! This guide will walk you through your first job submission and database query.

## 🚀 Prerequisites

1. **Install dapi**: `pip install dapi` (see [Installation Guide](installation.md))
2. **DesignSafe Account**: [Sign up here](https://www.designsafe-ci.org/account/register/) if needed
3. **Authentication**: Set up credentials (see [Authentication Guide](authentication.md))

## ⚡ 5-Minute Example

Here's a complete example that demonstrates the core dapi functionality:

```python
from dapi import DSClient

# 1. Initialize client (handles authentication)
client = DSClient()

# 2. Find available applications
matlab_apps = client.apps.find("matlab", verbose=True)

# 3. Submit a simple job
job_request = client.jobs.generate_request(
    app_id="matlab-r2023a",
    input_dir_uri="/MyData/analysis/input/",
    script_filename="run_analysis.m",
    max_minutes=30,
    allocation="your_allocation"
)

# 4. Submit and monitor
job = client.jobs.submit_request(job_request)
final_status = job.monitor()

# 5. Check results
if final_status == "FINISHED":
    print("✅ Job completed successfully!")
    job.print_runtime_summary()
    
    # Get job outputs
    outputs = job.list_outputs()
    for output in outputs:
        print(f"- {output.name} ({output.type})")

# 6. Query research database
df = client.db.ngl.read_sql("SELECT * FROM SITE LIMIT 5")
print(df)
```

## 📝 Step-by-Step Walkthrough

### Step 1: Initialize the Client

```python
from dapi import DSClient

# This will prompt for credentials if not found in environment
client = DSClient()
# Output: Authentication successful.
```

### Step 2: Explore Available Applications

```python
# Find all applications
all_apps = client.apps.find("", verbose=False)
print(f"Found {len(all_apps)} total applications")

# Find specific applications
mpm_apps = client.apps.find("mpm", verbose=True)
matlab_apps = client.apps.find("matlab", verbose=True)
opensees_apps = client.apps.find("opensees", verbose=True)

# Get detailed information about an app
app_details = client.apps.get_details("mpm-s3", verbose=True)
```

### Step 3: Prepare Your Input Files

```python
# Translate DesignSafe paths to TAPIS URIs
input_path = "/MyData/mpm-benchmarks/2d/uniaxial_stress/"
input_uri = client.files.translate_path_to_uri(input_path, verify_exists=True)
print(f"Input URI: {input_uri}")

# List files in the directory
files = client.files.list(input_uri)
for file in files:
    print(f"- {file.name} ({file.type}, {file.size} bytes)")
```

### Step 4: Generate Job Request

```python
# Generate a job request with automatic parameter mapping
job_request = client.jobs.generate_request(
    app_id="mpm-s3",
    input_dir_uri=input_uri,
    script_filename="mpm.json",
    max_minutes=10,
    node_count=1,
    cores_per_node=1,
    allocation="your_tacc_allocation"
)

# Optionally modify the request
job_request["description"] = "My MPM analysis"
job_request["tags"] = ["research", "mpm"]
```

### Step 5: Submit and Monitor Job

```python
# Submit the job
job = client.jobs.submit_request(job_request)
print(f"Job submitted: {job.uuid}")

# Monitor with real-time progress
final_status = job.monitor(interval=15)

# Interpret the result
client.jobs.interpret_status(final_status, job.uuid)
```

### Step 6: Access Job Results

```python
# Print runtime summary
if final_status in job.TERMINAL_STATES:
    job.print_runtime_summary(verbose=False)
    
    # Get archive URI
    archive_uri = job.archive_uri
    print(f"Results at: {archive_uri}")
    
    # List output files
    outputs = job.list_outputs()
    for output in outputs:
        print(f"- {output.name}")
    
    # Read job output
    stdout = job.get_output_content("tapisjob.out", max_lines=50)
    if stdout:
        print("Job Output:")
        print(stdout)
```

### Step 7: Query Research Databases

```python
# Query NGL database
ngl_data = client.db.ngl.read_sql("""
    SELECT SITE_NAME, SITE_LAT, SITE_LON 
    FROM SITE 
    WHERE SITE_LAT > 35 
    LIMIT 10
""")
print("NGL Sites:")
print(ngl_data)

# Query with parameters
site_name = "Amagasaki"
site_data = client.db.ngl.read_sql(
    "SELECT * FROM SITE WHERE SITE_NAME = %s",
    params=[site_name]
)
print(f"Data for {site_name}:")
print(site_data)
```

## 🎯 Common Workflows

### Workflow 1: MATLAB Analysis

```python
# Submit MATLAB job
job_request = client.jobs.generate_request(
    app_id="matlab-r2023a",
    input_dir_uri="/MyData/matlab/analysis/",
    script_filename="main.m",
    max_minutes=60,
    allocation="your_allocation"
)

job = client.jobs.submit_request(job_request)
final_status = job.monitor()

if final_status == "FINISHED":
    # Download specific result file
    job.download_output("results.mat", "/local/path/results.mat")
```

### Workflow 2: OpenSees Simulation

```python
# Submit OpenSees job
job_request = client.jobs.generate_request(
    app_id="opensees-express",
    input_dir_uri="/MyData/opensees/earthquake/",
    script_filename="earthquake_analysis.tcl",
    max_minutes=120,
    allocation="your_allocation"
)

job = client.jobs.submit_request(job_request)
final_status = job.monitor()
```

### Workflow 3: Database Analysis

```python
# Complex database query with joins
query = """
SELECT s.SITE_NAME, s.SITE_LAT, s.SITE_LON, COUNT(r.RECORD_ID) as num_records
FROM SITE s
LEFT JOIN RECORD r ON s.SITE_ID = r.SITE_ID
WHERE s.SITE_LAT BETWEEN 32 AND 38
GROUP BY s.SITE_ID
HAVING num_records > 5
ORDER BY num_records DESC
LIMIT 20
"""

df = client.db.ngl.read_sql(query)
print("Sites with most records in California:")
print(df)

# Export to CSV
df.to_csv("california_sites.csv", index=False)
```

## 🔧 Configuration Tips

### Set Default Allocation

```python
import os
os.environ['DEFAULT_ALLOCATION'] = 'your_tacc_allocation'

# Now you can omit allocation in job requests
job_request = client.jobs.generate_request(
    app_id="mpm-s3",
    input_dir_uri=input_uri,
    script_filename="mpm.json"
    # allocation will use DEFAULT_ALLOCATION
)
```

### Customize Job Monitoring

```python
# Monitor with custom interval and timeout
final_status = job.monitor(
    interval=30,           # Check every 30 seconds
    timeout_minutes=240    # Timeout after 4 hours
)

# Handle different outcomes
if final_status == "FINISHED":
    print("✅ Success!")
elif final_status == "FAILED":
    print("❌ Job failed")
    # Get error details
    stderr = job.get_output_content("tapisjob.err")
    if stderr:
        print("Error details:", stderr)
elif final_status == "TIMEOUT":
    print("⏰ Monitoring timed out")
```

## 🚨 Error Handling

```python
from dapi import (
    AuthenticationError,
    JobSubmissionError, 
    FileOperationError,
    JobMonitorError
)

try:
    client = DSClient()
    
    # Try to submit job
    job_request = client.jobs.generate_request(...)
    job = client.jobs.submit_request(job_request)
    final_status = job.monitor()
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except JobSubmissionError as e:
    print(f"Job submission failed: {e}")
except FileOperationError as e:
    print(f"File operation failed: {e}")
except JobMonitorError as e:
    print(f"Job monitoring failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 📊 Best Practices

### 1. Always Verify Paths
```python
# ✅ Good - verify path exists
input_uri = client.files.translate_path_to_uri(
    "/MyData/analysis/", 
    verify_exists=True
)

# ❌ Risk - path might not exist
input_uri = client.files.translate_path_to_uri("/MyData/analysis/")
```

### 2. Use Descriptive Job Names
```python
# ✅ Good - descriptive name
job_request["name"] = "earthquake_analysis_2024_site_A"
job_request["description"] = "Nonlinear seismic analysis for Site A"
job_request["tags"] = ["earthquake", "site-A", "research"]
```

### 3. Handle Long-Running Jobs
```python
# For long jobs, save job UUID for later monitoring
job = client.jobs.submit_request(job_request)
job_uuid = job.uuid

# Save UUID to file or environment
with open("current_job.txt", "w") as f:
    f.write(job_uuid)

# Later, resume monitoring
from dapi import SubmittedJob
saved_job = SubmittedJob(client._tapis, job_uuid)
final_status = saved_job.monitor()
```

## ➡️ Next Steps

Now that you've completed the quick start:

1. **[Explore detailed job management](jobs.md)** for advanced job operations
2. **[Learn database querying](database.md)** for research data analysis  
3. **[Study complete examples](examples/mpm.md)** for real-world workflows
4. **Check the API reference** for all available methods