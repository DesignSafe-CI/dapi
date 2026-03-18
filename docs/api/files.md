# Files

File operations and path translation utilities for DesignSafe storage systems.

All functions below accept an authenticated Tapis client as the first argument.
When using the `DSClient`, the Tapis client is supplied automatically and the
methods are available under `ds.files`.

| Module function | Client shorthand |
|---|---|
| `get_ds_path_uri(t, ...)` | `ds.files.to_uri(...)` |
| `tapis_uri_to_local_path(...)` | `ds.files.to_path(...)` |
| `upload_file(t, ...)` | `ds.files.upload(...)` |
| `download_file(t, ...)` | `ds.files.download(...)` |
| `list_files(t, ...)` | `ds.files.list(...)` |

---

## Path Translation

### `get_ds_path_uri(t, path, verify_exists=False)`

Translate DesignSafe-style paths to Tapis URIs.

Converts commonly used DesignSafe path formats (e.g., `/MyData/folder`,
`/projects/PRJ-XXXX/folder`) to their corresponding Tapis system URIs.
Supports MyData, CommunityData, and project-specific paths with automatic
system discovery for projects.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `path` (`str`): The DesignSafe-style path string to translate. Supported formats:
  - MyData paths: `"/MyData/folder"`, `"jupyter/MyData/folder"`, `"/home/jupyter/MyData/folder"`
  - Community paths: `"/CommunityData/folder"`
  - Project paths: `"/projects/PRJ-XXXX/folder"`
  - Direct Tapis URIs: `"tapis://system-id/path"` (passed through)
- `verify_exists` (`bool`, optional): If `True`, verifies the translated path exists on the target Tapis system. Defaults to `False`.

**Returns:** `str` -- The corresponding Tapis URI (e.g., `"tapis://system-id/path"`).

**Raises:**

- `FileOperationError`: If path translation fails, project system lookup fails, or path verification fails (when `verify_exists=True`).
- `AuthenticationError`: If username is required for MyData paths but `t.username` is not available.
- `ValueError`: If the input path format is unrecognized, empty, or incomplete.

**Example:**

```python
from dapi.files import get_ds_path_uri

uri = get_ds_path_uri(client, "/MyData/analysis/results")
# Translated '/MyData/analysis/results' to
# 'tapis://designsafe.storage.default/username/analysis/results'

uri = get_ds_path_uri(client, "/projects/PRJ-1234/data", verify_exists=True)

# Using DSClient:
uri = ds.files.to_uri("/MyData/analysis/results")
```

---

### `tapis_uri_to_local_path(tapis_uri)`

Convert a Tapis URI to the corresponding DesignSafe local path.

This is the reverse operation of `get_ds_path_uri()`. Converts Tapis system
URIs back to their equivalent DesignSafe local paths accessible in a Jupyter
environment.

**Args:**

- `tapis_uri` (`str`): The Tapis URI to convert. Supported formats:
  - `"tapis://designsafe.storage.default/username/path"` -> `"/home/jupyter/MyData/path"`
  - `"tapis://designsafe.storage.community/path"` -> `"/home/jupyter/CommunityData/path"`
  - `"tapis://project-*/path"` -> `"/home/jupyter/MyProjects/path"`

**Returns:** `str` -- The corresponding DesignSafe local path, or the original URI if it is not a recognized Tapis URI format.

**Raises:**

- `ValueError`: If the Tapis URI format is invalid.

**Example:**

```python
from dapi.files import tapis_uri_to_local_path

local_path = tapis_uri_to_local_path(
    "tapis://designsafe.storage.default/user/data/file.txt"
)
# "/home/jupyter/MyData/data/file.txt"

local_path = tapis_uri_to_local_path(
    "tapis://designsafe.storage.community/datasets/earthquake.csv"
)
# "/home/jupyter/CommunityData/datasets/earthquake.csv"

# Using DSClient:
local_path = ds.files.to_path("tapis://designsafe.storage.default/user/data/file.txt")
```

---

## File Operations

### `upload_file(t, local_path, remote_uri)`

Upload a local file to a Tapis storage system.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `local_path` (`str`): Path to the local file to upload.
- `remote_uri` (`str`): Tapis URI destination (e.g., `"tapis://system/path/file.txt"`).

**Raises:**

- `FileNotFoundError`: If the local file does not exist.
- `ValueError`: If `local_path` is not a file or `remote_uri` is invalid.
- `FileOperationError`: If the Tapis upload operation fails.

**Example:**

```python
from dapi.files import upload_file

upload_file(client, "/local/data.txt", "tapis://mysystem/uploads/data.txt")
# Uploading '/local/data.txt' to system 'mysystem' at path 'uploads/data.txt'...
# Upload complete.

# Using DSClient:
ds.files.upload("/local/data.txt", "tapis://mysystem/uploads/data.txt")
```

---

### `download_file(t, remote_uri, local_path)`

Download a file from a Tapis storage system to the local filesystem.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `remote_uri` (`str`): Tapis URI of the file to download (e.g., `"tapis://system/path/file.txt"`).
- `local_path` (`str`): Local filesystem path where the file should be saved.

**Raises:**

- `ValueError`: If `local_path` is a directory or `remote_uri` is invalid.
- `FileOperationError`: If the download operation fails or the remote file is not found.

**Example:**

```python
from dapi.files import download_file

download_file(client, "tapis://mysystem/data/results.txt", "/local/results.txt")
# Downloading from system 'mysystem' path 'data/results.txt' to '/local/results.txt'...
# Download complete.

# Using DSClient:
ds.files.download("tapis://mysystem/data/results.txt", "/local/results.txt")
```

---

### `list_files(t, remote_uri, limit=100, offset=0)`

List files and directories in a Tapis storage system path.

**Args:**

- `t` (`Tapis`): Authenticated Tapis client instance.
- `remote_uri` (`str`): Tapis URI of the directory to list (e.g., `"tapis://system/path/"`).
- `limit` (`int`, optional): Maximum number of items to return. Defaults to `100`.
- `offset` (`int`, optional): Number of items to skip (for pagination). Defaults to `0`.

**Returns:** `List[Tapis]` -- List of file and directory objects from the specified path. Each object contains metadata like name, size, type, and permissions.

**Raises:**

- `ValueError`: If `remote_uri` is invalid.
- `FileOperationError`: If the listing operation fails or the path is not found.

**Example:**

```python
from dapi.files import list_files

files = list_files(client, "tapis://mysystem/data/")
for f in files:
    print(f"{f.name} ({f.type})")

# Using DSClient:
files = ds.files.list("tapis://mysystem/data/")
```
