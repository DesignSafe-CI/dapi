# Apps

Application discovery and management for DesignSafe computational applications.

All functions below accept an authenticated Tapis client as the first argument.
When using the `DSClient`, the Tapis client is supplied automatically and the
methods are available under `ds.apps`.

| Module function | Client shorthand |
|---|---|
| `find_apps(t, ...)` | `ds.apps.find(...)` |
| `get_app_details(t, ...)` | `ds.apps.get_details(...)` |

---

## Application Discovery

### `find_apps(t, search_term, list_type="ALL", verbose=True)`

Search for Tapis apps matching a search term.

Searches through available Tapis applications using partial name matching.
This function helps discover applications available for job submission.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `search_term` (`str`): Name or partial name to search for. Use an empty string for all apps. Supports partial matching with wildcards.
- `list_type` (`str`, optional): Type of apps to list. Must be one of: `"OWNED"`, `"SHARED_PUBLIC"`, `"SHARED_DIRECT"`, `"READ_PERM"`, `"MINE"`, `"ALL"`. Defaults to `"ALL"`.
- `verbose` (`bool`, optional): If `True`, prints a summary of found apps including ID, version, and owner information. Defaults to `True`.

**Returns:** `List[Tapis]` -- List of matching Tapis app objects with selected fields (`id`, `version`, `owner`).

**Raises:**

- `AppDiscoveryError`: If the Tapis API search fails or an unexpected error occurs during the search operation.

**Example:**

```python
from dapi.apps import find_apps

apps = find_apps(client, "matlab", verbose=True)
# Found 3 matching apps:
# - matlab-r2023a (Version: 1.0, Owner: designsafe)
# - matlab-parallel (Version: 2.1, Owner: tacc)
# - matlab-desktop (Version: 1.5, Owner: designsafe)

# Using DSClient:
apps = ds.apps.find("matlab")
```

---

## Application Details

### `get_app_details(t, app_id, app_version=None, verbose=True)`

Get detailed information for a specific app ID and version.

Retrieves comprehensive details about a specific Tapis application,
including job attributes, execution system, and parameter definitions.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `app_id` (`str`): Exact app ID to look up. Must match exactly.
- `app_version` (`Optional[str]`, optional): Specific app version to retrieve. If `None`, fetches the latest available version. Defaults to `None`.
- `verbose` (`bool`, optional): If `True`, prints basic app information including ID, version, owner, execution system, and description. Defaults to `True`.

**Returns:** `Optional[Tapis]` -- Tapis app object with full details including `jobAttributes`, `parameterSet`, and other configuration. Returns `None` if the app is not found.

**Raises:**

- `AppDiscoveryError`: If the Tapis API call fails (except for 404 not found) or an unexpected error occurs during retrieval.

**Example:**

```python
from dapi.apps import get_app_details

app = get_app_details(client, "matlab-r2023a", "1.0")
# App Details:
#   ID: matlab-r2023a
#   Version: 1.0
#   Owner: designsafe
#   Execution System: frontera
#   Description: MATLAB R2023a runtime environment

# Using DSClient:
app = ds.apps.get_details("matlab-r2023a", "1.0")
```
