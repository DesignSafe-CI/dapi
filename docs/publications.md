# Publications

DesignSafe hosts over 1,500 published datasets with DOIs, spanning experimental, simulation, field reconnaissance, and other research types. Published datasets are read-only and accessible to all users.

Publication metadata is fetched from the [DesignSafe portal API](https://designsafe-ci.org) (`/api/publications/v2/`). Files are accessed via the Tapis Files API on `designsafe.storage.published`.

## List publications

Returns a DataFrame by default. Use `output="list"` for a list of dicts.

```python
from dapi import DSClient
ds = DSClient()

# Recent publications
ds.publications.list()

# Pagination
ds.publications.list(limit=50, offset=100)
```

DataFrame columns: `projectId`, `title`, `pi`, `type`, `keywords`, `created`.

## Search publications

Search with specific filters or general text. All filters are case-insensitive and combined with AND logic.

```python
# General text search (across title, description, keywords, PI)
ds.publications.search("liquefaction")

# Filter by PI name
ds.publications.search(pi="Rathje")

# Filter by keyword
ds.publications.search(keyword="storm surge")

# Filter by publication type: simulation, experimental, field_recon, other, hybrid_simulation
ds.publications.search(publication_type="simulation")

# Combine filters (AND logic)
ds.publications.search(keyword="storm surge", publication_type="simulation")

# Combine filters
ds.publications.search(keyword="earthquake", publication_type="experimental")
```

## Get publication details

Returns a dictionary with full metadata.

```python
info = ds.publications.get("PRJ-6270")

info['title']
info['description']
info['pi']
info['dois']          # DOIs for citation
info['keywords']
info['dataTypes']
info['projectType']   # simulation, experimental, field_recon, other
info['awardNumbers']
```

## List files in a publication

```python
# Root of a published project
ds.publications.files("PRJ-1271")

# Subfolder
ds.publications.files("PRJ-1271", path="/Experiment-9/")

# Raw Tapis file objects
files = ds.publications.files("PRJ-1271", output="raw")
```

DataFrame columns: `name`, `type`, `size`, `lastModified`, `path`.

## How it works

1. **Publication listing and search**: dapi queries the DesignSafe portal API (`/api/publications/v2/`). For search, all ~1,500 publications are fetched via pagination (~3 seconds) and filtered client-side.

2. **Publication detail**: dapi queries `/api/publications/v2/PRJ-XXXX/` which returns metadata in the `tree.children[0].value` structure, including DOIs, authors, and data types.

3. **File access**: published files live on the `designsafe.storage.published` Tapis system under `/PRJ-XXXX/` paths. File listings use the standard Tapis Files API.

## Error handling

- **Publication not found**: raised if the PRJ number doesn't match any published dataset.
- **File listing errors**: raised if the path doesn't exist on `designsafe.storage.published`.
