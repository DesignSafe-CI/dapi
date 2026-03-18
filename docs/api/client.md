# DSClient

The main client interface for all DAPI functionality. DSClient provides organized access to DesignSafe resources through the Tapis V3 API.

## DSClient

### `DSClient(tapis_client=None, **auth_kwargs)`

Main client for interacting with DesignSafe resources via Tapis V3 using dapi.

The DSClient provides a high-level interface for working with DesignSafe resources
through the Tapis V3 API. It handles authentication and provides organized access
to different service areas including applications, files, jobs, systems, and databases.

**Args:**
- `tapis_client` (Tapis, optional): Pre-authenticated Tapis client instance. If provided, it will be used instead of creating a new one.
- `**auth_kwargs`: Additional authentication arguments passed to `auth.init()` when `tapis_client` is not provided. Common arguments include:
  - `username` (str): DesignSafe username
  - `password` (str): DesignSafe password
  - `base_url` (str): Tapis base URL
  - `env_file` (str): Path to `.env` file with credentials

**Attributes:**
- `tapis` (Tapis): The underlying authenticated Tapis client instance.
- `apps` (AppMethods): Interface for application discovery and details.
- `files` (FileMethods): Interface for file operations (upload, download, list).
- `jobs` (JobMethods): Interface for job submission and monitoring.
- `systems` (SystemMethods): Interface for system information and queues.
- `db` (DatabaseAccessor): Interface for database connections and queries.

**Raises:**
- `TypeError`: If `tapis_client` is provided but is not a Tapis instance.
- `AuthenticationError`: If authentication fails when creating a new Tapis client.

**Example:**

```python
# Basic usage with automatic authentication
ds = DSClient()

# Using explicit credentials
ds = DSClient(username="myuser", password="mypass")

# Using a pre-authenticated Tapis client
from tapipy.tapis import Tapis
tapis = Tapis(base_url="https://designsafe.tapis.io", ...)
tapis.get_tokens()
ds = DSClient(tapis_client=tapis)
```

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

:::{warning}
When using the raw Tapis client, you'll need to handle errors and data formatting yourself. The dapi wrapper provides error handling and user-friendly formatting.
:::

## Service Interfaces

The DSClient provides access to different DesignSafe services through specialized interface classes:

### AppMethods

Interface for Tapis application discovery and details retrieval.

#### `find(search_term, list_type="ALL", verbose=True)`

Search for Tapis apps matching a search term.

**Args:**
- `search_term` (str): Name or partial name to search for. Use empty string for all apps. Supports partial matching with wildcards.
- `list_type` (str, optional): Type of apps to list. Must be one of: `"OWNED"`, `"SHARED_PUBLIC"`, `"SHARED_DIRECT"`, `"READ_PERM"`, `"MINE"`, `"ALL"`. Defaults to `"ALL"`.
- `verbose` (bool, optional): If `True`, prints summary of found apps including ID, version, and owner information. Defaults to `True`.

**Returns:** `List[Tapis]` -- List of matching Tapis app objects with selected fields (id, version, owner).

**Raises:**
- `AppDiscoveryError`: If the Tapis API search fails.

**Example:**

```python
apps = ds.apps.find("matlab")
# Found 3 matching apps:
# - matlab-r2023a (Version: 1.0, Owner: designsafe)
# - matlab-parallel (Version: 2.1, Owner: tacc)
```

---

#### `get_details(app_id, app_version=None, verbose=True)`

Get detailed information for a specific app ID and version.

**Args:**
- `app_id` (str): Exact app ID to look up. Must match exactly.
- `app_version` (str, optional): Specific app version to retrieve. If `None`, fetches the latest available version. Defaults to `None`.
- `verbose` (bool, optional): If `True`, prints basic app information including ID, version, owner, execution system, and description. Defaults to `True`.

**Returns:** `Optional[Tapis]` -- Tapis app object with full details including jobAttributes, parameterSet, and other configuration. Returns `None` if the app is not found.

**Raises:**
- `AppDiscoveryError`: If the Tapis API call fails (except for 404 not found).

**Example:**

```python
app = ds.apps.get_details("matlab-r2023a", "1.0")
# App Details:
#   ID: matlab-r2023a
#   Version: 1.0
#   Execution System: frontera
```

---

### FileMethods

Interface for file operations on Tapis storage systems.

#### `to_uri(path, verify_exists=False)`

Translate DesignSafe-style paths to Tapis URIs.

**Args:**
- `path` (str): The DesignSafe-style path string to translate. Supported formats:
  - MyData paths: `"/MyData/folder"`, `"jupyter/MyData/folder"`
  - Community paths: `"/CommunityData/folder"`
  - Project paths: `"/projects/PRJ-XXXX/folder"`
  - Direct Tapis URIs: `"tapis://system-id/path"`
- `verify_exists` (bool, optional): If `True`, verifies the translated path exists on the target Tapis system. Defaults to `False`.

**Returns:** `str` -- The corresponding Tapis URI (e.g., `"tapis://system-id/path"`).

**Raises:**
- `FileOperationError`: If path translation fails or verification fails.
- `AuthenticationError`: If username is required for MyData paths but not available.
- `ValueError`: If the input path format is unrecognized.

**Example:**

```python
uri = ds.files.to_uri("/MyData/analysis/results")
# "tapis://designsafe.storage.default/username/analysis/results"

uri = ds.files.to_uri("/projects/PRJ-1234/data", verify_exists=True)
```

---

#### `to_path(tapis_uri)`

Translate Tapis URIs to DesignSafe local paths.

**Args:**
- `tapis_uri` (str): The Tapis URI to convert. Supported formats:
  - `"tapis://designsafe.storage.default/username/path"` -> `"/home/jupyter/MyData/path"`
  - `"tapis://designsafe.storage.community/path"` -> `"/home/jupyter/CommunityData/path"`
  - `"tapis://project-*/path"` -> `"/home/jupyter/MyProjects/path"`

**Returns:** `str` -- The corresponding DesignSafe local path, or the original URI if it is not a recognized format.

**Example:**

```python
local_path = ds.files.to_path("tapis://designsafe.storage.default/user/data/file.txt")
# "/home/jupyter/MyData/data/file.txt"
```

---

#### `upload(local_path, remote_uri)`

Upload a local file to a Tapis storage system.

**Args:**
- `local_path` (str): Path to the local file to upload.
- `remote_uri` (str): Tapis URI destination (e.g., `"tapis://system/path/file.txt"`).

**Raises:**
- `FileNotFoundError`: If the local file does not exist.
- `ValueError`: If `local_path` is not a file or `remote_uri` is invalid.
- `FileOperationError`: If the Tapis upload operation fails.

**Example:**

```python
ds.files.upload("/local/data.txt", "tapis://mysystem/uploads/data.txt")
```

---

#### `download(remote_uri, local_path)`

Download a file from a Tapis storage system to the local filesystem.

**Args:**
- `remote_uri` (str): Tapis URI of the file to download (e.g., `"tapis://system/path/file.txt"`).
- `local_path` (str): Local filesystem path where the file should be saved.

**Raises:**
- `ValueError`: If `local_path` is a directory or `remote_uri` is invalid.
- `FileOperationError`: If the download operation fails.

**Example:**

```python
ds.files.download("tapis://mysystem/data/results.txt", "/local/results.txt")
```

---

#### `list(remote_uri, limit=100, offset=0)`

List files and directories in a Tapis storage system path.

**Args:**
- `remote_uri` (str): Tapis URI of the directory to list (e.g., `"tapis://system/path/"`).
- `limit` (int, optional): Maximum number of items to return. Defaults to `100`.
- `offset` (int, optional): Number of items to skip (for pagination). Defaults to `0`.

**Returns:** `List[Tapis]` -- List of file and directory objects from the specified path. Each object contains metadata like name, size, type, and permissions.

**Raises:**
- `ValueError`: If `remote_uri` is invalid.
- `FileOperationError`: If the listing operation fails or path not found.

**Example:**

```python
files = ds.files.list("tapis://mysystem/data/")
for f in files:
    print(f"{f.name} ({f.type})")
```

---

### JobMethods

Interface for Tapis job submission, monitoring, and management.

**Attributes:**
- `parametric_sweep` (ParametricSweepMethods): Interface for PyLauncher parameter sweep generation and submission.

#### `generate(app_id, input_dir_uri, *, script_filename=None, app_version=None, job_name=None, description=None, tags=None, max_minutes=None, node_count=None, cores_per_node=None, memory_mb=None, queue=None, allocation=None, archive_system=None, archive_path=None, extra_file_inputs=None, extra_app_args=None, extra_env_vars=None, extra_scheduler_options=None, script_param_names=["Input Script", "Main Script", "tclScript"], input_dir_param_name="Input Directory", allocation_param_name="TACC Allocation")`

Generate a Tapis job request dictionary based on app definition and inputs. Automatically retrieves app details and applies user-specified overrides and extra parameters.

**Args:**
- `app_id` (str): The ID of the Tapis application to use for the job.
- `input_dir_uri` (str): Tapis URI to the input directory containing job files.
- `script_filename` (str, optional): Name of the main script file to execute. If `None`, no script parameter is added (suitable for apps like OpenFOAM).
- `app_version` (str, optional): Specific app version. If `None`, uses latest.
- `job_name` (str, optional): Custom job name. If `None`, auto-generates one.
- `description` (str, optional): Job description. If `None`, uses app description.
- `tags` (List[str], optional): List of tags to associate with the job.
- `max_minutes` (int, optional): Maximum runtime in minutes. Overrides app default.
- `node_count` (int, optional): Number of compute nodes. Overrides app default.
- `cores_per_node` (int, optional): Cores per node. Overrides app default.
- `memory_mb` (int, optional): Memory in MB. Overrides app default.
- `queue` (str, optional): Execution queue name. Overrides app default.
- `allocation` (str, optional): TACC allocation to charge for compute time.
- `archive_system` (str, optional): Archive system for job outputs. Use `"designsafe"` for `designsafe.storage.default`. If `None`, uses app default.
- `archive_path` (str, optional): Archive directory path. Can be a full path or just a directory name in MyData. If `None` and `archive_system` is `"designsafe"`, defaults to `"tapis-jobs-archive/${JobCreateDate}/${JobUUID}"`.
- `extra_file_inputs` (List[Dict], optional): Additional file inputs beyond the main input directory.
- `extra_app_args` (List[Dict], optional): Additional application arguments.
- `extra_env_vars` (List[Dict], optional): Additional environment variables. Each item should be `{"key": "VAR_NAME", "value": "var_value"}`.
- `extra_scheduler_options` (List[Dict], optional): Additional scheduler options.
- `script_param_names` (List[str], optional): Parameter names to check for script placement. Defaults to `["Input Script", "Main Script", "tclScript"]`.
- `input_dir_param_name` (str, optional): Parameter name for input directory. Defaults to `"Input Directory"`.
- `allocation_param_name` (str, optional): Parameter name for allocation. Defaults to `"TACC Allocation"`.

**Returns:** `Dict[str, Any]` -- Complete job request dictionary ready for submission.

**Raises:**
- `AppDiscoveryError`: If the specified app cannot be found.
- `ValueError`: If required parameters are missing or invalid.
- `JobSubmissionError`: If job request generation fails.

**Example:**

```python
job_request = ds.jobs.generate(
    app_id="matlab-r2023a",
    input_dir_uri="tapis://designsafe.storage.default/username/input/",
    script_filename="run_analysis.m",
    max_minutes=120,
    allocation="MyProject-123",
)
```

---

#### `submit(job_request)`

Submit a job request dictionary to Tapis.

**Args:**
- `job_request` (Dict[str, Any]): Complete job request dictionary (typically from `generate()`).

**Returns:** `SubmittedJob` -- A SubmittedJob object for monitoring and managing the job.

**Raises:**
- `ValueError`: If `job_request` is not a dictionary.
- `JobSubmissionError`: If the Tapis submission fails.

**Example:**

```python
job_request = ds.jobs.generate(...)
job = ds.jobs.submit(job_request)
print(f"Job submitted with UUID: {job.uuid}")
```

---

#### `job(job_uuid)`

Get a SubmittedJob object for an existing job by UUID.

**Args:**
- `job_uuid` (str): The UUID of an existing Tapis job.

**Returns:** `SubmittedJob` -- A job object for monitoring via `.monitor()`.

**Example:**

```python
job = ds.jobs.job("12345678-1234-1234-1234-123456789abc")
job.monitor()
```

---

#### `status(job_uuid)`

Get the current status of a job by UUID.

**Args:**
- `job_uuid` (str): The UUID of the job to check.

**Returns:** `str` -- The current job status (e.g., `"QUEUED"`, `"RUNNING"`, `"FINISHED"`).

**Raises:**
- `JobMonitorError`: If status retrieval fails.

**Example:**

```python
ds.jobs.status("12345678-1234-1234-1234-123456789abc")
# 'FINISHED'
```

---

#### `runtime_summary(job_uuid, verbose=False)`

Print the runtime summary for a job by UUID.

**Args:**
- `job_uuid` (str): The UUID of the job to analyze.
- `verbose` (bool, optional): If `True`, prints detailed job history events. Defaults to `False`.

**Example:**

```python
ds.jobs.runtime_summary("12345678-1234-1234-1234-123456789abc")
# Runtime Summary
# ---------------
# QUEUED  time: 00:05:30
# RUNNING time: 01:23:45
# TOTAL   time: 01:29:15
```

---

#### `interpret_status(final_status, job_uuid=None)`

Print a user-friendly interpretation of a job status.

**Args:**
- `final_status` (str): The job status to interpret.
- `job_uuid` (str, optional): The job UUID for context in the message.

**Example:**

```python
ds.jobs.interpret_status("FINISHED", "12345678-1234-1234-1234-123456789abc")
# Job 12345678-1234-1234-1234-123456789abc completed successfully.
```

---

#### `list(app_id=None, status=None, limit=100, output="df", verbose=False)`

List jobs with optional filtering. Fetches jobs from Tapis ordered by creation date (newest first). Filters are applied client-side.

**Args:**
- `app_id` (str, optional): Filter by application ID.
- `status` (str, optional): Filter by job status (e.g., `"FINISHED"`). Case-insensitive.
- `limit` (int, optional): Maximum jobs to fetch. Defaults to `100`.
- `output` (str, optional): Output format. `"df"` for pandas DataFrame (default), `"list"` for list of dicts, `"raw"` for TapisResult objects.
- `verbose` (bool, optional): Print job count. Defaults to `False`.

**Returns:** Depends on `output`: DataFrame, list of dicts, or list of TapisResult objects.

**Raises:**
- `JobMonitorError`: If the Tapis API call fails.
- `ValueError`: If output format is not recognized.

**Example:**

```python
df = ds.jobs.list(app_id="matlab-r2023a", status="FINISHED")
jobs = ds.jobs.list(output="list")
raw = ds.jobs.list(limit=10, output="raw")
```

---

### SystemMethods

Interface for Tapis system information and queue management.

#### `queues(system_id, verbose=True)`

List logical queues available on a Tapis execution system.

**Args:**
- `system_id` (str): The ID of the execution system (e.g., `"frontera"`).
- `verbose` (bool, optional): If `True`, prints detailed queue information. Defaults to `True`.

**Returns:** `List[Any]` -- List of queue objects with queue configuration details.

**Raises:**
- `SystemInfoError`: If the system is not found or queue retrieval fails.
- `ValueError`: If `system_id` is empty.

**Example:**

```python
queues = ds.systems.queues("frontera")
```

---

#### `check_credentials(system_id, username=None)`

Check whether TMS credentials exist for a user on a system.

**Args:**
- `system_id` (str): The ID of the Tapis system (e.g., `"frontera"`).
- `username` (str, optional): Username to check. Defaults to the authenticated user.

**Returns:** `bool` -- `True` if credentials exist, `False` otherwise.

**Raises:**
- `CredentialError`: If the credential check fails unexpectedly.
- `ValueError`: If `system_id` is empty.

**Example:**

```python
has_creds = ds.systems.check_credentials("frontera")
```

---

#### `establish_credentials(system_id, username=None, force=False, verbose=True)`

Establish TMS credentials for a user on a Tapis system. Idempotent: skips creation if credentials already exist (unless `force=True`). Only supported for systems using TMS_KEYS authentication.

**Args:**
- `system_id` (str): The ID of the Tapis system (e.g., `"frontera"`).
- `username` (str, optional): Username. Defaults to the authenticated user.
- `force` (bool, optional): Re-create even if credentials exist. Defaults to `False`.
- `verbose` (bool, optional): Print status messages. Defaults to `True`.

**Raises:**
- `CredentialError`: If the system is not TMS_KEYS or creation fails.
- `ValueError`: If `system_id` is empty.

**Example:**

```python
ds.systems.establish_credentials("frontera")
```

---

#### `revoke_credentials(system_id, username=None, verbose=True)`

Remove TMS credentials for a user on a Tapis system. Idempotent: succeeds silently if credentials do not exist.

**Args:**
- `system_id` (str): The ID of the Tapis system (e.g., `"frontera"`).
- `username` (str, optional): Username. Defaults to the authenticated user.
- `verbose` (bool, optional): Print status messages. Defaults to `True`.

**Raises:**
- `CredentialError`: If credential removal fails unexpectedly.
- `ValueError`: If `system_id` is empty.

**Example:**

```python
ds.systems.revoke_credentials("frontera")
```

---

### ParametricSweepMethods

Interface for PyLauncher parameter sweeps. Accessible via `ds.jobs.parametric_sweep`.

#### `generate(command, sweep, directory=None, *, placeholder_style="token", debug=None, preview=False)`

Generate PyLauncher sweep files or preview the parameter grid.

With `preview=True`, returns a DataFrame of all parameter combinations -- no files are written. Otherwise, expands `command` into one command per combination and writes `runsList.txt` and `call_pylauncher.py` into `directory`.

**Args:**
- `command` (str): Command template with placeholders matching sweep keys.
- `sweep` (Dict[str, Any]): Mapping of placeholder name to sequence of values.
- `directory` (str, optional): Directory to write files into (created if needed). Required when `preview` is `False`.
- `placeholder_style` (str, optional): `"token"` (default) for bare `ALPHA`, or `"braces"` for `{ALPHA}`.
- `debug` (str, optional): Optional debug string (e.g., `"host+job"`).
- `preview` (bool, optional): If `True`, return a DataFrame (dry run).

**Returns:** `List[str]` of commands, or `pandas.DataFrame` when `preview` is `True`.

**Example:**

```python
# Preview the parameter grid
df = ds.jobs.parametric_sweep.generate(
    command="python run.py --alpha ALPHA --beta BETA",
    sweep={"ALPHA": [0.1, 0.5], "BETA": [1, 2]},
    preview=True,
)

# Generate sweep files
commands = ds.jobs.parametric_sweep.generate(
    command="python run.py --alpha ALPHA --beta BETA",
    sweep={"ALPHA": [0.1, 0.5], "BETA": [1, 2]},
    directory="/MyData/sweep/",
)
```

---

#### `submit(directory, app_id, allocation, *, node_count=None, cores_per_node=None, max_minutes=None, queue=None, **kwargs)`

Submit a PyLauncher sweep job. Translates `directory` to a Tapis URI, builds a job request with `call_pylauncher.py` as the script, and submits it.

**Args:**
- `directory` (str): Path to the input directory containing `runsList.txt` and `call_pylauncher.py` (e.g., `"/MyData/sweep/"`).
- `app_id` (str): Tapis application ID (e.g., `"openseespy-s3"`).
- `allocation` (str): TACC allocation to charge.
- `node_count` (int, optional): Number of compute nodes.
- `cores_per_node` (int, optional): Cores per node.
- `max_minutes` (int, optional): Maximum runtime in minutes.
- `queue` (str, optional): Execution queue name.
- `**kwargs`: Additional arguments passed to `ds.jobs.generate()`.

**Returns:** `SubmittedJob` -- A job object for monitoring via `.monitor()`.

**Example:**

```python
job = ds.jobs.parametric_sweep.submit(
    directory="/MyData/sweep/",
    app_id="openseespy-s3",
    allocation="MyProject-123",
    node_count=2,
    max_minutes=60,
)
job.monitor()
```
