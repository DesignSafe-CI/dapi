# Apps

## Find apps

Search by name. Use an empty string to list everything.

```python
from dapi import DSClient
ds = DSClient()

ds.apps.find("matlab")
# Found 3 matching apps:
# - matlab-r2023a (Version: 1.0, Owner: designsafe)
# - matlab-parallel (Version: 2.1, Owner: tacc)
# - matlab-desktop (Version: 1.5, Owner: designsafe)

ds.apps.find("opensees")
ds.apps.find("mpm")

# All apps (quiet mode)
all_apps = ds.apps.find("", verbose=False)
len(all_apps)
```

The search uses partial matching — `"matlab"` matches any app with "matlab" in the ID.

You can filter by ownership:

```python
# Only apps you own
ds.apps.find("", list_type="OWNED")

# Only shared/public apps
ds.apps.find("", list_type="SHARED_PUBLIC")
```

Valid `list_type` values: `"ALL"` (default), `"OWNED"`, `"SHARED_PUBLIC"`, `"SHARED_DIRECT"`, `"READ_PERM"`, `"MINE"`.

## App details

```python
app = ds.apps.get_details("mpm-s3")
# App Details:
#   ID: mpm-s3
#   Version: 0.1.0
#   Owner: designsafe
#   Execution System: frontera
#   Description: ...
```

Access job configuration:

```python
attrs = app.jobAttributes
print(attrs.execSystemId)          # frontera
print(attrs.maxMinutes)            # 2880
print(attrs.coresPerNode)          # 56
print(attrs.execSystemLogicalQueue)  # normal
```

Request a specific version:

```python
app = ds.apps.get_details("mpm-s3", app_version="0.1.0")
```

Returns `None` if the app doesn't exist (instead of raising).

## Common apps

| App ID | Description |
|---|---|
| `designsafe-agnostic-app` | General-purpose Python, OpenSees, PyLauncher |
| `matlab-r2023a` | MATLAB |
| `opensees-express` | OpenSees (serial) |
| `opensees-mp-s3` | OpenSees (MPI parallel) |
| `mpm-s3` | Material Point Method |
| `adcirc-v55` | ADCIRC coastal modeling |
| `ls-dyna` | LS-DYNA finite element |
