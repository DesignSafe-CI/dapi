# Projects

DesignSafe projects (MyProjects) are collaborative workspaces where team members share files, curate datasets, and publish research. Each project has a PRJ number (e.g., PRJ-6270), a UUID, and a corresponding Tapis storage system.

Project metadata is fetched from the [DesignSafe portal API](https://designsafe-ci.org) (`/api/projects/v2/`), which provides project details, team information, and DOIs. File listings use the Tapis Files API against the project's storage system (`project-<uuid>`).

## List your projects

Returns a DataFrame by default. Use `output="list"` for a list of dicts.

```python
from dapi import DSClient
ds = DSClient()

# DataFrame (renders as a table in Jupyter)
ds.projects.list()

# List of dicts
projects = ds.projects.list(output="list")
```

Pagination:

```python
ds.projects.list(limit=100, offset=100)
```

DataFrame columns: `projectId`, `title`, `pi`, `type`, `created`, `lastUpdated`, `uuid`.

## Get project details

Returns a dictionary with full project metadata.

```python
info = ds.projects.get("PRJ-6270")

info['title']
info['description']
info['pi']           # PI display name (e.g., "Cheng-Hsi Hsiao")
info['dois']         # Associated DOIs
info['keywords']
info['awardNumbers']
info['projectType']  # experimental, simulation, field_recon, other, etc.
info['systemId']     # Tapis system ID for file access
```

Full field reference:

| Field | Description |
|---|---|
| `uuid` | Project UUID |
| `projectId` | Project ID (e.g., "PRJ-6270") |
| `title` | Project title |
| `description` | Project description |
| `pi` | Principal investigator display name |
| `coPis` | Co-PIs |
| `teamMembers` | Team members |
| `awardNumbers` | Grant/award numbers |
| `keywords` | Keywords |
| `dois` | Associated DOIs |
| `projectType` | Type (experimental, simulation, field_recon, etc.) |
| `systemId` | Tapis system ID for file access |
| `created` | Creation timestamp |
| `lastUpdated` | Last update timestamp |

## List files in a project

Returns a DataFrame by default. Use `output="raw"` for Tapis file objects.

```python
# Root of a project
ds.projects.files("PRJ-6270")

# Subfolder
ds.projects.files("PRJ-1305", path="/Training/")

# Raw Tapis file objects
files = ds.projects.files("PRJ-6270", output="raw")
```

DataFrame columns: `name`, `type`, `size`, `lastModified`, `path`.

## Projects and file path translation

`ds.files.to_uri()` also accepts project paths. dapi resolves the PRJ number to the Tapis system UUID automatically:

```python
uri = ds.files.to_uri("/MyProjects/PRJ-6270/data/")
# tapis://project-8ef68b96-dad5-4029-aba3-614ff3fa8f97/data/

files = ds.files.list(uri)
```

Both `/MyProjects/PRJ-XXXX/` and `/projects/PRJ-XXXX/` are accepted.

## How it works

1. **Project listing and metadata** — dapi queries the DesignSafe portal API (`https://designsafe-ci.org/api/projects/v2/`) using your Tapis authentication token. This API returns project metadata including the project UUID.

2. **PRJ-to-UUID resolution** — Each project's Tapis storage system ID is `project-<uuid>`. When you use a PRJ number (e.g., `PRJ-6270`), dapi looks up the UUID via the portal API.

3. **File operations** — File listings use the standard Tapis Files API (`t.files.listFiles`) against the resolved `project-<uuid>` system.

## Error handling

- **Project not found**: raised if the PRJ number doesn't match any project you have access to.
- **File listing errors**: raised if the Tapis system for the project is unavailable or the path doesn't exist.
