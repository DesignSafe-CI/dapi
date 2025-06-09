# DSClient

The main client interface for all DAPI functionality. DSClient provides organized access to DesignSafe resources through the Tapis V3 API.

::: dapi.client.DSClient

## Accessing the Raw Tapis Client

For advanced use cases or accessing Tapis APIs not wrapped by dapi, you can get the underlying Tapis client:

```python
from dapi import DSClient

# Initialize DSClient
ds = DSClient()

# Access the raw Tapis client
tapis_client = ds.tapis

# Use raw Tapis APIs directly
raw_apps = tapis_client.apps.getApps(search="*opensees*")
systems = tapis_client.systems.getSystems()
jobs = tapis_client.jobs.getJobList()
```

### When to Use the Raw Tapis Client

- Access Tapis APIs not yet wrapped by dapi
- Use advanced search parameters not exposed by dapi  
- Implement custom functionality
- Debug or troubleshoot API calls
- Access experimental or new Tapis features

!!! warning
    When using the raw Tapis client, you'll need to handle errors and data formatting yourself. The dapi wrapper provides error handling and user-friendly formatting.

## Service Interfaces

The DSClient provides access to different DesignSafe services through specialized interface classes:

### AppMethods

::: dapi.client.AppMethods

### FileMethods

::: dapi.client.FileMethods

### JobMethods

::: dapi.client.JobMethods

### SystemMethods

::: dapi.client.SystemMethods