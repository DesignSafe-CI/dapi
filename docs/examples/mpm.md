# MPM Job Submission Example

This comprehensive example demonstrates how to submit and monitor a Material Point Method (MPM) job using dapi. MPM is a particle-based method for simulating large deformation problems in geomechanics and fluid mechanics.

## 🎯 Overview

This example covers:
- Setting up authentication and environment
- Discovering available MPM applications
- Preparing input files and directories
- Generating and customizing job requests
- Submitting and monitoring jobs
- Accessing and analyzing results

## 🚀 Complete Example

### Step 1: Setup and Authentication

```python
import os
from dapi import (
    DSClient,
    SubmittedJob,
    interpret_job_status,
    AppDiscoveryError,
    FileOperationError,
    JobSubmissionError,
    JobMonitorError,
    STATUS_TIMEOUT,
    STATUS_UNKNOWN,
    TAPIS_TERMINAL_STATES,
)
import json
from datetime import datetime
import pandas as pd

# Initialize DSClient with authentication
try:
    print("Initializing DSClient...")
    ds = DSClient()
    print("DSClient initialized successfully.")
except Exception as e:
    print(f"Initialization failed: {e}")
    raise SystemExit("Stopping due to client initialization failure.")
```

### Step 2: Configure Job Parameters

```python
# Job configuration
ds_path: str = "/MyData/mpm-benchmarks/2d/uniaxial_stress/"
input_filename: str = "mpm.json"
max_job_minutes: int = 10
tacc_allocation: str = "ASC25049"  # Replace with your allocation
app_id_to_use = "mpm-s3"

# Optional queue override (use default if not specified)
# queue: str = "skx"  # Uncomment to override default queue
```

### Step 3: Verify Input Path and Files

```python
# Translate and verify DesignSafe path
try:
    input_uri = ds.files.translate_path_to_uri(ds_path, verify_exists=True)
    print(f"✅ Input Directory URI: {input_uri}")
    
    # List files in the input directory
    print("\n📁 Files in input directory:")
    files = ds.files.list(input_uri)
    for file in files:
        print(f"  - {file.name} ({file.type}, {file.size} bytes)")
    
    # Verify required input file exists
    input_files = [f.name for f in files]
    if input_filename not in input_files:
        raise FileOperationError(f"Required file '{input_filename}' not found in {ds_path}")
    print(f"✅ Required input file '{input_filename}' found")
    
except FileOperationError as e:
    print(f"❌ Path verification failed: {e}")
    raise SystemExit("Stopping due to path verification error.")
```

### Step 4: Discover and Inspect MPM Applications

```python
# Find available MPM applications
print("\n🔍 Discovering available applications...")
try:
    mpm_apps = ds.apps.find("mpm", verbose=True)
    print(f"Found {len(mpm_apps)} MPM applications")
    
    # Get detailed information about the specific app
    app_details = ds.apps.get_details(app_id_to_use, verbose=True)
    if not app_details:
        raise AppDiscoveryError(f"App '{app_id_to_use}' not found")
    
    print(f"\n📋 Using Application: {app_details.id}")
    print(f"   Version: {app_details.version}")
    print(f"   Description: {app_details.description}")
    print(f"   Execution System: {app_details.jobAttributes.execSystemId}")
    print(f"   Default Queue: {app_details.jobAttributes.execSystemLogicalQueue}")
    print(f"   Max Runtime: {app_details.jobAttributes.maxMinutes} minutes")
    print(f"   Default Cores: {app_details.jobAttributes.coresPerNode}")
    
except (AppDiscoveryError, Exception) as e:
    print(f"❌ App discovery failed: {e}")
    raise SystemExit("Stopping due to app discovery error.")
```

### Step 5: Generate Job Request

```python
# Generate job request with automatic parameter mapping
try:
    print("\n⚙️ Generating job request...")
    job_dict = ds.jobs.generate_request(
        app_id=app_id_to_use,
        input_dir_uri=input_uri,
        script_filename=input_filename,
        max_minutes=max_job_minutes,
        allocation=tacc_allocation,
        # Optional parameters
        job_name=f"mpm_uniaxial_stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        description="MPM simulation of uniaxial stress test using dapi",
        tags=["research", "mpm", "geomechanics", "uniaxial-stress"],
        node_count=1,
        cores_per_node=1,  # Start with single core for testing
    )
    
    print("✅ Job request generated successfully")
    
    # Display the generated job request
    print("\n📄 Generated Job Request:")
    print(json.dumps(job_dict, indent=2, default=str))
    
except (AppDiscoveryError, ValueError, JobSubmissionError) as e:
    print(f"❌ Job request generation failed: {e}")
    raise SystemExit("Stopping due to job request generation error.")
```

### Step 6: Customize Job Request (Optional)

```python
# Optional: Modify job request before submission
print("\n🔧 Customizing job request...")

# Ensure we're using minimal resources for this example
job_dict["nodeCount"] = 1
job_dict["coresPerNode"] = 1
job_dict["maxMinutes"] = max_job_minutes

# Add environment variables if needed
if "parameterSet" not in job_dict:
    job_dict["parameterSet"] = {}
if "envVariables" not in job_dict["parameterSet"]:
    job_dict["parameterSet"]["envVariables"] = []

# Example: Add OpenMP thread control
job_dict["parameterSet"]["envVariables"].append({
    "key": "OMP_NUM_THREADS",
    "value": "1"
})

print("✅ Job request customized")
print(f"   Nodes: {job_dict['nodeCount']}")
print(f"   Cores per node: {job_dict['coresPerNode']}")
print(f"   Max runtime: {job_dict['maxMinutes']} minutes")
```

### Step 7: Submit Job

```python
# Submit the job
try:
    print("\n🚀 Submitting job...")
    submitted_job = ds.jobs.submit_request(job_dict)
    print(f"✅ Job submitted successfully!")
    print(f"   Job UUID: {submitted_job.uuid}")
    print(f"   Job Name: {job_dict['name']}")
    
    # Save job UUID for later reference
    job_uuid = submitted_job.uuid
    with open("current_mpm_job.txt", "w") as f:
        f.write(f"{job_uuid}\n{datetime.now().isoformat()}\n")
    print(f"   Job UUID saved to: current_mpm_job.txt")
    
except JobSubmissionError as e:
    print(f"❌ Job submission failed: {e}")
    print("\n🔍 Failed Job Request Details:")
    print(json.dumps(job_dict, indent=2, default=str))
    raise SystemExit("Stopping due to job submission error.")
```

### Step 8: Monitor Job Progress

```python
# Monitor job with real-time progress
try:
    print(f"\n👀 Monitoring job {submitted_job.uuid}...")
    print("   Use Ctrl+C to interrupt monitoring (job will continue running)")
    
    # Monitor with custom interval
    final_status = submitted_job.monitor(interval=15)  # Check every 15 seconds
    
    print(f"\n🏁 Job monitoring completed!")
    print(f"   Final Status: {final_status}")
    
except KeyboardInterrupt:
    print(f"\n⏸️ Monitoring interrupted by user")
    print(f"   Job is still running. UUID: {submitted_job.uuid}")
    print(f"   Check status later with: ds.jobs.get_status('{submitted_job.uuid}')")
    final_status = "INTERRUPTED"
except Exception as e:
    print(f"\n❌ Monitoring error: {e}")
    final_status = "MONITOR_ERROR"
```

### Step 9: Interpret Results

```python
# Interpret the final job status
print("\n📊 Job Results Analysis")
print("=" * 50)

# Use the built-in status interpretation
ds.jobs.interpret_status(final_status, submitted_job.uuid)

# Additional analysis based on status
if final_status == "FINISHED":
    print("\n✅ SUCCESS: Job completed successfully!")
    
    # Get runtime summary
    try:
        print("\n⏱️ Runtime Summary:")
        submitted_job.print_runtime_summary(verbose=False)
    except Exception as e:
        print(f"Could not display runtime summary: {e}")
        
elif final_status == "FAILED":
    print("\n❌ FAILURE: Job failed during execution")
    print("💡 Check the troubleshooting section below for common issues")
    
elif final_status in ["TIMEOUT", "INTERRUPTED"]:
    print(f"\n⚠️ WARNING: Job monitoring {final_status.lower()}")
    print("   Job may still be running on the compute system")
    
    # Check current status
    try:
        current_status = submitted_job.get_status()
        print(f"   Current job status: {current_status}")
    except Exception as e:
        print(f"   Could not check current status: {e}")
```

### Step 10: Access Job Outputs

```python
# Access job outputs and results
if final_status in TAPIS_TERMINAL_STATES:
    print("\n📁 Accessing Job Outputs")
    print("-" * 30)
    
    try:
        # Get archive URI
        archive_uri = submitted_job.archive_uri
        if archive_uri:
            print(f"📍 Job Archive URI: {archive_uri}")
            
            # List all files in the archive
            print("\n📋 Files in job archive:")
            outputs = submitted_job.list_outputs()
            for output in outputs:
                size_mb = output.size / (1024 * 1024) if output.size else 0
                print(f"   - {output.name} ({output.type}, {size_mb:.2f} MB)")
                
            # Read job output log
            print("\n📜 Job Output (last 50 lines):")
            stdout_content = submitted_job.get_output_content(
                "tapisjob.out", 
                max_lines=50,
                missing_ok=True
            )
            if stdout_content:
                print("```")
                print(stdout_content)
                print("```")
            else:
                print("   No output log available")
                
            # Check for errors if job failed
            if final_status == "FAILED":
                print("\n🚨 Error Analysis:")
                stderr_content = submitted_job.get_output_content(
                    "tapisjob.err",
                    max_lines=50, 
                    missing_ok=True
                )
                if stderr_content:
                    print("Error log:")
                    print("```")
                    print(stderr_content)
                    print("```")
                else:
                    print("   No error log found (errors may be in main output)")
                    
        else:
            print("❌ Archive URI not available")
            
    except FileOperationError as e:
        print(f"❌ Could not access job outputs: {e}")
    except Exception as e:
        print(f"❌ Unexpected error accessing outputs: {e}")
```

### Step 11: Download Results (Optional)

```python
# Download specific result files
if final_status == "FINISHED":
    print("\n💾 Downloading Results")
    print("-" * 25)
    
    try:
        # Create local results directory
        local_results_dir = f"mpm_results_{job_uuid[:8]}"
        os.makedirs(local_results_dir, exist_ok=True)
        
        # Download key files
        files_to_download = ["tapisjob.out", "tapisjob.err"]
        
        for filename in files_to_download:
            try:
                local_path = os.path.join(local_results_dir, filename)
                submitted_job.download_output(filename, local_path)
                print(f"✅ Downloaded: {filename} -> {local_path}")
            except Exception as e:
                print(f"⚠️ Could not download {filename}: {e}")
                
        # List any MPM-specific output files and download them
        try:
            outputs = submitted_job.list_outputs()
            mpm_files = [f for f in outputs if f.name.endswith(('.vtu', '.vtk', '.csv', '.txt')) 
                        and f.type == 'file']
            
            for mpm_file in mpm_files:
                try:
                    local_path = os.path.join(local_results_dir, mpm_file.name)
                    submitted_job.download_output(mpm_file.name, local_path)
                    print(f"✅ Downloaded MPM result: {mpm_file.name} -> {local_path}")
                except Exception as e:
                    print(f"⚠️ Could not download {mpm_file.name}: {e}")
                    
        except Exception as e:
            print(f"⚠️ Could not list/download MPM output files: {e}")
            
        print(f"\n📁 Results saved in: {local_results_dir}/")
        
    except Exception as e:
        print(f"❌ Error during download: {e}")
```

### Step 12: Status Summary and Next Steps

```python
# Final summary
print("\n" + "=" * 60)
print("🎯 MPM Job Submission Summary")
print("=" * 60)
print(f"Job UUID: {submitted_job.uuid}")
print(f"Job Name: {job_dict['name']}")
print(f"Final Status: {final_status}")
print(f"Application: {app_id_to_use}")
print(f"Input Directory: {ds_path}")
print(f"Input File: {input_filename}")

if final_status == "FINISHED":
    print("✅ Status: SUCCESS - Job completed successfully")
    print("💡 Next steps:")
    print("   - Analyze results in the downloaded files")
    print("   - Visualize outputs using ParaView (for .vtu files)")
    print("   - Compare with expected results")
    
elif final_status == "FAILED":
    print("❌ Status: FAILED - Job execution failed")
    print("💡 Troubleshooting steps:")
    print("   - Review error logs above")
    print("   - Check input file format and parameters")
    print("   - Verify resource requirements are reasonable")
    print("   - Contact support if issues persist")
    
elif final_status in ["TIMEOUT", "INTERRUPTED"]:
    print(f"⚠️ Status: {final_status} - Monitoring stopped")
    print("💡 Check job status later:")
    print(f"   current_status = ds.jobs.get_status('{submitted_job.uuid}')")
    
else:
    print(f"❓ Status: {final_status} - Unexpected final status")

print("\n📚 For more examples and documentation:")
print("   - https://designsafe-ci.github.io/dapi")
print("   - https://github.com/DesignSafe-CI/dapi")
```

## 🔧 Advanced Customization

### Custom Resource Requirements

```python
# For larger simulations, customize resources
advanced_job_request = ds.jobs.generate_request(
    app_id="mpm-s3",
    input_dir_uri=input_uri,
    script_filename="large_simulation.json",
    
    # High-performance configuration
    max_minutes=240,       # 4 hours
    node_count=4,          # Multiple nodes
    cores_per_node=48,     # Full node utilization
    memory_mb=192000,      # 192 GB RAM
    queue="normal",        # Production queue
    allocation=tacc_allocation,
    
    # Job metadata
    job_name="mpm_large_scale_analysis",
    description="Large-scale MPM simulation with multiple materials",
    tags=["research", "mpm", "large-scale", "multi-material"],
    
    # Additional environment variables
    extra_env_vars=[
        {"key": "OMP_NUM_THREADS", "value": "48"},
        {"key": "MPM_VERBOSE", "value": "1"},
        {"key": "MPM_OUTPUT_FREQ", "value": "100"}
    ]
)
```

### Parametric Study Example

```python
# Submit multiple jobs with different parameters
parameters = [
    {"friction": 0.1, "cohesion": 1000, "density": 2000},
    {"friction": 0.2, "cohesion": 1500, "density": 2200},
    {"friction": 0.3, "cohesion": 2000, "density": 2400},
]

submitted_jobs = []

for i, params in enumerate(parameters):
    # Create parameter-specific job request
    param_job_request = ds.jobs.generate_request(
        app_id="mpm-s3",
        input_dir_uri=input_uri,
        script_filename="parametric_template.json",
        max_minutes=60,
        allocation=tacc_allocation,
        job_name=f"mpm_parametric_{i:03d}",
        description=f"Parametric study: friction={params['friction']}, cohesion={params['cohesion']}"
    )
    
    # Add parameters as environment variables
    if "parameterSet" not in param_job_request:
        param_job_request["parameterSet"] = {}
    if "envVariables" not in param_job_request["parameterSet"]:
        param_job_request["parameterSet"]["envVariables"] = []
    
    param_job_request["parameterSet"]["envVariables"].extend([
        {"key": "MPM_FRICTION", "value": str(params["friction"])},
        {"key": "MPM_COHESION", "value": str(params["cohesion"])},
        {"key": "MPM_DENSITY", "value": str(params["density"])}
    ])
    
    # Submit job
    job = ds.jobs.submit_request(param_job_request)
    submitted_jobs.append((job, params))
    print(f"Submitted parametric job {i+1}/{len(parameters)}: {job.uuid}")

# Monitor all jobs
print("Monitoring all parametric jobs...")
results = []
for job, params in submitted_jobs:
    final_status = job.monitor()
    results.append({
        "job_uuid": job.uuid,
        "parameters": params,
        "final_status": final_status
    })

# Summarize results
print("\nParametric Study Results:")
for result in results:
    print(f"  {result['parameters']} -> {result['final_status']}")
```

## 🚨 Troubleshooting

### Common Issues and Solutions

```python
# Check system and queue availability
def check_system_status():
    try:
        # Check if target system is available
        stampede_queues = ds.systems.list_queues("stampede3")
        print("✅ Stampede3 system is accessible")
        
        # Check specific queue
        available_queues = [q.name for q in stampede_queues]
        if "skx-dev" in available_queues:
            print("✅ Development queue is available")
        else:
            print("⚠️ Development queue not found. Available queues:")
            for queue in available_queues:
                print(f"   - {queue}")
                
    except Exception as e:
        print(f"❌ System check failed: {e}")

# Validate input files
def validate_input_files():
    try:
        # Check if input file is valid JSON
        with open("local_copy_of_mpm.json", "r") as f:
            import json
            config = json.load(f)
            print("✅ Input file is valid JSON")
            
        # Check required fields (example)
        required_fields = ["mesh", "particles", "materials"]
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            print(f"⚠️ Missing required fields: {missing_fields}")
        else:
            print("✅ All required fields present")
            
    except FileNotFoundError:
        print("❌ Input file not found locally for validation")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
    except Exception as e:
        print(f"❌ Validation error: {e}")

# Run diagnostics
print("🔍 Running diagnostics...")
check_system_status()
validate_input_files()
```

### Resume Monitoring

```python
# If monitoring was interrupted, resume with saved job UUID
def resume_monitoring():
    try:
        with open("current_mpm_job.txt", "r") as f:
            lines = f.readlines()
            saved_uuid = lines[0].strip()
            submission_time = lines[1].strip() if len(lines) > 1 else "Unknown"
            
        print(f"Resuming monitoring for job: {saved_uuid}")
        print(f"Originally submitted: {submission_time}")
        
        # Create SubmittedJob object
        resumed_job = SubmittedJob(ds._tapis, saved_uuid)
        
        # Check current status
        current_status = resumed_job.get_status()
        print(f"Current status: {current_status}")
        
        if current_status not in resumed_job.TERMINAL_STATES:
            print("Job is still running, resuming monitoring...")
            final_status = resumed_job.monitor()
            print(f"Final status: {final_status}")
        else:
            print("Job has already completed")
            final_status = current_status
            
        return resumed_job, final_status
        
    except FileNotFoundError:
        print("❌ No saved job UUID found")
        return None, None
    except Exception as e:
        print(f"❌ Error resuming monitoring: {e}")
        return None, None

# Example usage:
# resumed_job, final_status = resume_monitoring()
```

## 📊 Performance Analysis

### Analyzing Job Performance

```python
def analyze_job_performance(job):
    """Analyze job performance and resource utilization"""
    try:
        # Get runtime summary
        print("📈 Performance Analysis")
        print("-" * 30)
        
        job.print_runtime_summary(verbose=True)
        
        # Get job details
        details = job.details
        
        # Calculate efficiency metrics
        total_cores = details.nodeCount * details.coresPerNode
        max_runtime_hours = details.maxMinutes / 60
        
        print(f"\n📊 Resource Allocation:")
        print(f"   Nodes: {details.nodeCount}")
        print(f"   Cores per node: {details.coresPerNode}")
        print(f"   Total cores: {total_cores}")
        print(f"   Memory per node: {details.memoryMB} MB")
        print(f"   Max runtime: {max_runtime_hours:.2f} hours")
        
        # Analyze output for performance metrics
        output = job.get_output_content("tapisjob.out", missing_ok=True)
        if output:
            # Look for timing information in MPM output
            lines = output.split('\n')
            duration_lines = [line for line in lines if 'duration' in line.lower()]
            
            if duration_lines:
                print(f"\n⏱️ Execution Timing:")
                for line in duration_lines:
                    print(f"   {line.strip()}")
                    
        print(f"\n💡 Optimization suggestions:")
        if total_cores == 1:
            print("   - Consider using multiple cores for larger simulations")
        if max_runtime_hours > 2:
            print("   - Consider breaking large simulations into smaller parts")
        print("   - Monitor memory usage to optimize allocation")
        
    except Exception as e:
        print(f"❌ Performance analysis failed: {e}")

# Example usage after job completion:
# if final_status == "FINISHED":
#     analyze_job_performance(submitted_job)
```

This comprehensive example demonstrates the complete workflow for submitting and monitoring MPM jobs using dapi, including error handling, result analysis, and advanced features for production use.