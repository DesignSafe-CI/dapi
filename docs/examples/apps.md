# App Discovery and Management

This guide demonstrates how to discover and examine Tapis applications available on DesignSafe using the dapi library.

## Basic Setup

```python
from dapi import DSClient

# Initialize the client (will prompt for credentials if needed)
ds = DSClient()
```

## Finding Applications

### Find All Available Apps

```python
# Get a list of all available applications
all_apps = ds.apps.find("", verbose=False)
print(f"Found {len(all_apps)} total apps.")
```

### Search for Specific Apps

```python
# Search for applications containing "mpm" in the name
mpm_apps = ds.apps.find("mpm", verbose=True)
```

The `verbose=True` option will display a formatted list of matching applications with their versions and owners.

### Search for Other Common Applications

```python
# Find MATLAB apps
matlab_apps = ds.apps.find("matlab", verbose=True)

# Find OpenSees apps
opensees_apps = ds.apps.find("opensees", verbose=True)

# Find ADCIRC apps
adcirc_apps = ds.apps.find("adcirc", verbose=True)

# Find OpenFOAM apps
openfoam_apps = ds.apps.find("openfoam", verbose=True)
```

## Getting Application Details

### Basic App Information

```python
# Get detailed information for a specific application
app_id = "opensees-express"
app_details = ds.apps.get_details(app_id, verbose=True)

if app_details:
    print(f"App ID: {app_details.id}")
    print(f"Version: {app_details.version}")
    print(f"Description: {app_details.description}")
    print(f"Owner: {app_details.owner}")
    print(f"Execution System: {app_details.jobAttributes.execSystemId}")
else:
    print(f"App '{app_id}' not found")
```

### Understanding App Parameters

Applications define their input requirements through parameters. Here's how to examine them:

```python
app_details = ds.apps.get_details("opensees-express")
job_attrs = app_details.jobAttributes
param_set = job_attrs.parameterSet

# Check file inputs
print("File Inputs:")
for file_input in job_attrs.fileInputs:
    print(f"  - {file_input.name}: {file_input.description}")

# Check app arguments
print("\nApp Arguments:")
for arg in param_set.appArgs:
    print(f"  - {arg.name}: {arg.description}")

# Check environment variables
print("\nEnvironment Variables:")
for env_var in param_set.envVariables:
    print(f"  - {env_var.key}: {env_var.description}")
    if hasattr(env_var, 'enum_values') and env_var.enum_values:
        print(f"    Options: {list(env_var.enum_values.keys())}")
```

### Resource Requirements

```python
# Check default resource requirements
job_attrs = app_details.jobAttributes
print(f"Default node count: {job_attrs.nodeCount}")
print(f"Default cores per node: {job_attrs.coresPerNode}")
print(f"Default memory (MB): {job_attrs.memoryMB}")
print(f"Default max minutes: {job_attrs.maxMinutes}")
print(f"Default queue: {job_attrs.execSystemLogicalQueue}")
```

## Working with App Data as DataFrames

For analysis and comparison, you can convert app data to pandas DataFrames:

```python
import pandas as pd

# Get all apps and convert to DataFrame
all_apps = ds.apps.find("", verbose=False)

# Extract basic app information
app_data = []
for app in all_apps:
    app_data.append({
        'id': app.id,
        'version': app.version,
        'owner': app.owner,
        'description': app.description,
        'enabled': app.enabled,
        'execution_system': getattr(app.jobAttributes, 'execSystemId', 'N/A'),
        'max_minutes': getattr(app.jobAttributes, 'maxMinutes', 'N/A'),
        'node_count': getattr(app.jobAttributes, 'nodeCount', 'N/A'),
        'cores_per_node': getattr(app.jobAttributes, 'coresPerNode', 'N/A'),
    })

apps_df = pd.DataFrame(app_data)
print(apps_df.head())

# Filter for specific types of applications
simulation_apps = apps_df[apps_df['description'].str.contains('simulation', case=False, na=False)]
print(f"\nFound {len(simulation_apps)} simulation apps")
```

## Advanced: Accessing the Raw Tapis Client

If you need to access Tapis APIs that aren't wrapped by dapi, you can get the underlying Tapis client:

```python
# Get the raw Tapis client for advanced operations
tapis_client = ds.tapis

# Example: Get raw app details using Tapis client directly
raw_app_details = tapis_client.apps.getApp(appId="opensees-express")
print(f"Raw app data: {raw_app_details}")

# Example: List apps with custom parameters
raw_apps = tapis_client.apps.getApps(search="*mpm*", listType="ALL")
print(f"Found {len(raw_apps)} raw apps")

# Example: Access other Tapis services
systems = tapis_client.systems.getSystems()
print(f"Available systems: {len(systems)}")
```

### When to Use the Raw Tapis Client

Use `ds.tapis` when you need to:

- Access Tapis APIs not yet wrapped by dapi
- Use advanced search parameters not exposed by dapi
- Implement custom functionality
- Debug or troubleshoot API calls
- Access experimental or new Tapis features

!!! warning "Using Raw Tapis Client"
    When using the raw Tapis client, you'll need to handle errors and data formatting yourself. The dapi wrapper provides error handling and user-friendly formatting that you'll lose with direct Tapis calls.

## Common App Categories

Here are some common application categories available on DesignSafe:

```python
# Structural analysis applications
structural_keywords = ["opensees", "abaqus", "ansys", "ls-dyna"]

# Fluid dynamics applications  
fluid_keywords = ["openfoam", "adcirc", "swan"]

# Geotechnical applications
geo_keywords = ["mpm", "plaxis", "flac"]

# Materials applications
materials_keywords = ["lammps", "matlab"]

# Search for each category
for category, keywords in [
    ("Structural", structural_keywords),
    ("Fluid Dynamics", fluid_keywords), 
    ("Geotechnical", geo_keywords),
    ("Materials", materials_keywords)
]:
    print(f"\n{category} Applications:")
    for keyword in keywords:
        apps = ds.apps.find(keyword, verbose=False)
        if apps:
            print(f"  {keyword}: {len(apps)} apps found")
```

## Next Steps

After discovering applications, you can:

1. **[Submit jobs](../jobs.md)** using the discovered applications
2. **[Explore job examples](mpm.md)** for specific workflows
3. **[Check system resources](../api/systems.md)** for execution requirements
4. **[Manage files](../api/files.md)** for job inputs and outputs

## Troubleshooting

### App Not Found
If an application isn't found, it might be:
- Disabled temporarily
- Only available to specific users
- Spelled differently than expected

Try broader searches or contact DesignSafe support.

### Access Issues
Some applications might require special permissions or allocations. Check with your project team or DesignSafe support if you can't access expected applications.