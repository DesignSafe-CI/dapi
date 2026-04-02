# Projects

## List your projects

```python
from dapi import DSClient
ds = DSClient()

projects = ds.projects.list()
for p in projects[:5]:
    pi = p['pi']
    pi_name = f"{pi['fname']} {pi['lname']}" if pi else "N/A"
    print(f"{p['projectId']:12s} | {pi_name:25s} | {p['title'][:50]}")
```

Pagination:

```python
# Get projects 100-199
projects = ds.projects.list(limit=100, offset=100)
```

## Get project details

```python
info = ds.projects.get("PRJ-6270")

print(info['title'])
print(info['description'])
print(info['projectType'])
print(info['pi'])
print(info['dois'])
print(info['keywords'])
print(info['awardNumbers'])
print(info['systemId'])  # Tapis system ID for file access
```

The returned dictionary contains:

| Field | Description |
|---|---|
| `uuid` | Project UUID |
| `projectId` | Project ID (e.g., "PRJ-6270") |
| `title` | Project title |
| `description` | Project description |
| `pi` | Principal investigator (dict with username, fname, lname, email) |
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

```python
# Root of a project
files = ds.projects.files("PRJ-6270")
for f in files:
    print(f"{f.name:50s} {f.type}")

# Subfolder
files = ds.projects.files("PRJ-1305", path="/Training/")
for f in files[:10]:
    print(f"{f.name:50s} {f.type}")
```

## Projects and file path translation

`ds.files.to_uri()` also accepts project paths. dapi resolves the PRJ number to the Tapis system UUID automatically:

```python
uri = ds.files.to_uri("/MyProjects/PRJ-6270/data/")
# tapis://project-8ef68b96-dad5-4029-aba3-614ff3fa8f97/data/

files = ds.files.list(uri)
```

Both `/MyProjects/PRJ-XXXX/` and `/projects/PRJ-XXXX/` are accepted.

## Error handling

- **Project not found**: raised if the PRJ number doesn't match any project you have access to.
- **File listing errors**: raised if the Tapis system for the project is unavailable or the path doesn't exist.
