# Files

## Path translation

DesignSafe uses Tapis URIs internally (`tapis://system-id/path`). Most users work with familiar paths like `/MyData/folder/` — dapi translates between the two.

```python
from dapi import DSClient
ds = DSClient()

# MyData → includes your username automatically
ds.files.to_uri("/MyData/analysis/input/")
# tapis://designsafe.storage.default/<username>/analysis/input/

# Community data
ds.files.to_uri("/CommunityData/some-dataset/")
# tapis://designsafe.storage.community/some-dataset/

# Projects — looks up the Tapis system ID from the project number
ds.files.to_uri("/projects/PRJ-1234/data/")
# tapis://project-xxxx-xxxx-xxxx/data/

# Already a Tapis URI — passed through unchanged
ds.files.to_uri("tapis://designsafe.storage.default/<username>/folder/")
```

Verify a path exists before using it:

```python
ds.files.to_uri("/MyData/analysis/input/", verify_exists=True)
```

Reverse translation (URI back to Jupyter path, where `~` is `/home/jupyter` on DesignSafe JupyterHub):

```python
ds.files.to_path("tapis://designsafe.storage.default/<username>/data/file.txt")
# ~/MyData/data/file.txt

ds.files.to_path("tapis://designsafe.storage.community/datasets/eq.csv")
# ~/CommunityData/datasets/eq.csv
```

### Supported path formats

| Input path | Tapis system |
|---|---|
| `/MyData/...` | `designsafe.storage.default/<username>/...` |
| `~/MyData/...` | `designsafe.storage.default/<username>/...` |
| `jupyter/MyData/...` | `designsafe.storage.default/<username>/...` |
| `/CommunityData/...` | `designsafe.storage.community/...` |
| `/projects/PRJ-XXXX/...` | `project-<uuid>/...` (auto-discovered) |
| `tapis://...` | passed through unchanged |

## List files

```python
files = ds.files.list("tapis://designsafe.storage.default/<username>/analysis/")
for f in files:
    print(f"{f.name} ({f.type}, {f.size} bytes)")
```

Pagination:

```python
# Get items 100-199
files = ds.files.list(uri, limit=100, offset=100)
```

## Upload

```python
ds.files.upload(
    "/local/path/input.json",
    "tapis://designsafe.storage.default/<username>/analysis/input.json",
)
```

The local file must exist and be a regular file (not a directory). Parent directories are created on the remote system.

## Download

```python
ds.files.download(
    "tapis://designsafe.storage.default/<username>/results/output.csv",
    "/local/path/output.csv",
)
```

Local parent directories are created automatically. The local path must be a file path, not a directory.

## Error handling

File operations raise exceptions on failure:

- **File not found**: raised if the remote path does not exist (for `download`, `list`) or local file does not exist (for `upload`).
- **Permission denied**: raised if the user does not have access to the storage system or directory.
- **`verify_exists=True`**: when used with `to_uri()`, raises an error immediately if the path does not exist on DesignSafe, instead of failing later during job submission.
