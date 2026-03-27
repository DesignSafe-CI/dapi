# App Discovery and Management

For basic app search and details, see [Apps](../apps.md). This page covers advanced patterns.

## Working with App Data as DataFrames

```python
from dapi import DSClient
import pandas as pd

ds = DSClient()

all_apps = ds.apps.find("", verbose=False)

app_data = []
for app in all_apps:
 app_data.append({
 'id': app.id,
 'version': app.version,
 'owner': app.owner,
 'execution_system': getattr(app.jobAttributes, 'execSystemId', 'N/A'),
 'max_minutes': getattr(app.jobAttributes, 'maxMinutes', 'N/A'),
 'cores_per_node': getattr(app.jobAttributes, 'coresPerNode', 'N/A'),
 })

apps_df = pd.DataFrame(app_data)
print(apps_df.head())
```

## Accessing the Raw Tapis Client

If you need Tapis APIs not wrapped by dapi, use the underlying client:

```python
tapis_client = ds.tapis

# Get raw app details
raw_app = tapis_client.apps.getApp(appId="opensees-express")

# List apps with custom parameters
raw_apps = tapis_client.apps.getApps(search="*mpm*", listType="ALL")

# Access other Tapis services
systems = tapis_client.systems.getSystems()
```

Use `ds.tapis` when you need advanced search parameters, experimental Tapis features, or APIs not yet exposed by dapi.
