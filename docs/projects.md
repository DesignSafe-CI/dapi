# Projects

A DesignSafe project is the workspace a team shares files in, curates datasets in, and publishes from. `ds.projects` lists yours (MyProjects) and published ones (NHERI-Published), reads their metadata, and lists their files, all addressed by a PRJ number such as PRJ-6270.

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

The DataFrame has columns `projectId`, `title`, `pi`, `type`, `created`, `lastUpdated`, and `uuid`.

## Get project details

Returns a dictionary with full project metadata.

```python
info = ds.projects.get("PRJ-6270")

info["title"]
info["description"]
info["pi"]  # PI display name (e.g., "Cheng-Hsi Hsiao")
info["dois"]  # Associated DOIs
info["keywords"]
info["awardNumbers"]
info["projectType"]  # experimental, simulation, field_recon, other, etc.
info["systemId"]  # Tapis system ID for file access
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

The DataFrame has columns `name`, `type`, `size`, `lastModified`, and `path`.

## Projects and file path translation

`ds.files.to_uri()` also accepts project paths. dapi resolves the PRJ number to the Tapis system UUID automatically:

```python
uri = ds.files.to_uri("/MyProjects/PRJ-6270/data/")
# tapis://project-8ef68b96-dad5-4029-aba3-614ff3fa8f97/data/

files = ds.files.list(uri)
```

Both `/MyProjects/PRJ-XXXX/` and `/projects/PRJ-XXXX/` are accepted.

## Check who can see a file

Project sharing rides on POSIX access control lists. Every member has a named ACL entry on each file, and an ACL *mask* caps what those entries grant. `permissions()` reads all of it and computes each member's real access:

```python
ds.projects.permissions("PRJ-1234", "/results/run1.out")
```

| username | role | tapis | posix_acl | mask | other | effective |
|---|---|---|---|---|---|---|
| user1 | pi | MODIFY | rwx | --- | --- | none |
| user2 | team_member | MODIFY | rwx | --- | --- | none |

In the table, `tapis` is the Tapis-layer grant from project membership. `posix_acl` is the member's named ACL entry on the file (`missing` means it was wiped). `mask` caps every entry; `other` is the file's world bits, which act as a floor. `effective` combines them into the truth. In the table above, membership looks fine, yet nobody can read the file, because its mask vetoes everything.

## Fix broken file sharing

Files transferred into a project from the command line break sharing in two ways: `scp` and `cp` cap the mask with the source file's mode, while `mv`, `cp -p`, and `rsync -a` wipe the member entries entirely. `fix_permissions()` repairs each broken file with the strongest strategy it allows:

```python
ds.projects.fix_permissions("PRJ-1234")  # whole project
ds.projects.fix_permissions("PRJ-1234", "/results")  # one directory
ds.projects.fix_permissions("PRJ-1234", dry_run=True)  # preview only
```

The report maps each repaired path to its strategy:

- **direct**: the file belongs to the Tapis service account; one `setFacl` fixes it. This also covers files that predate a newly added member.
- **owner (via cloud.data)**: the file is yours. dapi reaches the storage host through the `cloud.data` system, which acts as the calling user, and an owner may always repair their own ACLs, from any machine, no shell required.
- **copy**: the service account can read the file, so it is recreated with healthy ACLs and swapped over the original (the owner becomes the service account).
- **unfixable**: the file belongs to another member; the report includes the exact `fix_permissions` call for that person to run.

Healthy files are skipped, directory default ACLs are refreshed so future files inherit access for all current members, and every repair is verified against the storage before being reported.

Prevention beats repair. Transfer into projects through Tapis (portal, dapi, or job archiving into the project system), or finish command-line copies with `chmod -R g+rwX` on the destination. Never `mv`, `cp -p`, or `rsync -a` into a project.

The [project permissions example](examples/project-permissions.md) breaks a file the way scp does and repairs it.

## The APIs behind project access

1. **Project listing and metadata**: dapi queries the DesignSafe portal API (`https://designsafe-ci.org/api/projects/v2/`) using your Tapis authentication token. This API returns project metadata including the project UUID.

2. **PRJ-to-UUID resolution**: Each project's Tapis storage system ID is `project-<uuid>`. When you use a PRJ number (e.g., `PRJ-6270`), dapi looks up the UUID via the portal API.

3. **File operations**: File listings use the standard Tapis Files API (`t.files.listFiles`) against the resolved `project-<uuid>` system.

## Error handling

- **Project not found**: raised if the PRJ number doesn't match any project you have access to.
- **File listing errors**: raised if the Tapis system for the project is unavailable or the path doesn't exist.
