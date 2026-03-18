# Systems

System information, queue management, and TMS credential management for DesignSafe execution systems.

All functions below accept an authenticated Tapis client as the first argument.
When using the `DSClient`, the Tapis client is supplied automatically and the
methods are available under `ds.systems`.

| Module function | Client shorthand |
|---|---|
| `list_system_queues(t, ...)` | `ds.systems.queues(...)` |
| `check_credentials(t, ...)` | `ds.systems.check_credentials(...)` |
| `establish_credentials(t, ...)` | `ds.systems.establish_credentials(...)` |
| `revoke_credentials(t, ...)` | `ds.systems.revoke_credentials(...)` |
| `setup_tms_credentials(t, ...)` | *(called automatically during `DSClient` init)* |

---

## System Queues

### `list_system_queues(t, system_id, verbose=True)`

Retrieve the list of batch logical queues available on a specific Tapis execution system.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `system_id` (`str`): The ID of the execution system (e.g., `"frontera"`, `"stampede3"`).
- `verbose` (`bool`, optional): If `True`, prints the found queues with details. Defaults to `True`.

**Returns:** `List[Any]` -- A list of queue objects (typically `TapisResult` instances) defined for the system. Returns an empty list if the system exists but has no queues defined.

**Raises:**

- `SystemInfoError`: If the system is not found or an API error occurs.
- `ValueError`: If `system_id` is empty.

**Example:**

```python
from dapi.systems import list_system_queues

queues = list_system_queues(client, "frontera")
# Fetching queue information for system 'frontera'...
# Found 3 batch logical queues for system 'frontera':
#   - Name: normal (HPC Queue: normal, Max Jobs: 50, ...)
#   - Name: development (HPC Queue: development, Max Jobs: 1, ...)

# Using DSClient:
queues = ds.systems.queues("frontera")
```

---

## TMS Credential Management

Manage Tapis Managed Secrets (TMS) credentials on execution systems. TMS credentials are SSH key pairs that allow Tapis to access TACC systems (Frontera, Stampede3, Lonestar6) on behalf of a user. They must be established once per system before submitting jobs.

### `check_credentials(t, system_id, username=None)`

Check whether TMS credentials exist for a user on a Tapis system.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `system_id` (`str`): The ID of the Tapis system (e.g., `"frontera"`, `"stampede3"`).
- `username` (`Optional[str]`, optional): The username to check. If `None`, auto-detected from `t.username`. Defaults to `None`.

**Returns:** `bool` -- `True` if credentials exist, `False` if they do not.

**Raises:**

- `ValueError`: If `system_id` is empty or username cannot be determined.
- `CredentialError`: If an unexpected API error occurs during the check.

**Example:**

```python
from dapi.systems import check_credentials

has_creds = check_credentials(client, "frontera")
print(has_creds)  # True or False

# Using DSClient:
has_creds = ds.systems.check_credentials("frontera")
```

---

### `establish_credentials(t, system_id, username=None, force=False, verbose=True)`

Establish TMS credentials for a user on a Tapis system.

Idempotent: if credentials already exist and `force` is `False`, no action is taken.
Only systems with `defaultAuthnMethod` set to `"TMS_KEYS"` are supported.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `system_id` (`str`): The ID of the Tapis system (e.g., `"frontera"`, `"stampede3"`).
- `username` (`Optional[str]`, optional): The username. If `None`, auto-detected from `t.username`. Defaults to `None`.
- `force` (`bool`, optional): If `True`, create credentials even if they already exist. Defaults to `False`.
- `verbose` (`bool`, optional): If `True`, prints status messages. Defaults to `True`.

**Raises:**

- `ValueError`: If `system_id` is empty or username cannot be determined.
- `CredentialError`: If the system does not use `TMS_KEYS`, if the system is not found, or if credential creation fails.

**Example:**

```python
from dapi.systems import establish_credentials

establish_credentials(client, "frontera")
# TMS credentials established for user 'myuser' on system 'frontera'.

# Force re-creation:
establish_credentials(client, "frontera", force=True)

# Using DSClient:
ds.systems.establish_credentials("frontera")
```

---

### `revoke_credentials(t, system_id, username=None, verbose=True)`

Remove TMS credentials for a user on a Tapis system.

Idempotent: if credentials do not exist, no error is raised.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `system_id` (`str`): The ID of the Tapis system (e.g., `"frontera"`, `"stampede3"`).
- `username` (`Optional[str]`, optional): The username. If `None`, auto-detected from `t.username`. Defaults to `None`.
- `verbose` (`bool`, optional): If `True`, prints status messages. Defaults to `True`.

**Raises:**

- `ValueError`: If `system_id` is empty or username cannot be determined.
- `CredentialError`: If credential removal fails unexpectedly.

**Example:**

```python
from dapi.systems import revoke_credentials

revoke_credentials(client, "frontera")
# Credentials revoked for user 'myuser' on system 'frontera'.

# Using DSClient:
ds.systems.revoke_credentials("frontera")
```

---

### `setup_tms_credentials(t, systems=None)`

Check and establish TMS credentials on execution systems.

For each system, checks if credentials exist and creates them if missing.
Failures are handled gracefully -- a system that cannot be reached or where
the user lacks an allocation is skipped with a warning.

This function is called automatically during `DSClient` initialization for the
default TACC systems.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `systems` (`Optional[List[str]]`, optional): List of system IDs to set up. Defaults to `TACC_SYSTEMS` (`["frontera", "stampede3", "ls6"]`).

**Returns:** `Dict[str, str]` -- A dictionary mapping each `system_id` to its status: `"ready"` (credentials already existed), `"created"` (newly established), or `"skipped"` (system unreachable or not TMS_KEYS).

**Example:**

```python
from dapi.systems import setup_tms_credentials

results = setup_tms_credentials(client)
# TMS credentials ready: frontera, stampede3 (newly created: stampede3)
# TMS credentials skipped: ls6
print(results)
# {'frontera': 'ready', 'stampede3': 'created', 'ls6': 'skipped'}

# With custom system list:
results = setup_tms_credentials(client, systems=["frontera"])
```
