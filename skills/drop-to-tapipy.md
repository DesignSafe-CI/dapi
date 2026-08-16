---
name: drop-to-tapipy
description: When and how to use the raw Tapis client underneath dapi
---

# Drop to tapipy

dapi is the orchestration surface; every submission goes through
`ds.jobs.generate` -> `submit` -> `monitor`. But `DSClient` carries the
authenticated tapipy client as `ds.tapis`, and a few real needs sit
below the wrappers. Use `ds.tapis` for those; never construct a second
`Tapis()` client, and never submit work through it.

## Sanctioned drop-downs

Binary output download by job UUID (no dapi wrapper returns bytes):

```python
data = ds.tapis.jobs.getJobOutputDownload(jobUuid=uuid, outputPath=rel_path)
open(local_path, "wb").write(data)
```

Job event history, to see where time went (long QUEUED means the
request is oversized; long ARCHIVING means too much output):

```python
events = ds.tapis.jobs.getJobHistory(jobUuid=uuid)
```

App schema introspection beyond `ds.apps.get_details`, e.g. resolving
"latest" to a pinned version or reading fixed appArgs:

```python
app = ds.tapis.apps.getAppLatestVersion(appId="opensees-mp-s3")
```

Tapis search grammar that `ds.apps.find`'s substring match cannot say:

```python
ds.tapis.apps.getApps(
    search="(id.like.*opensees*)~(version.eq.latest)",
    listType="ALL",
    select="id,version,description",
)
```

Full system definitions when `ds.systems.list`/`queues` omit a field
(auth method, root dir, complete queue objects):

```python
sysdef = ds.tapis.systems.getSystem(systemId="stampede3")
```

Auditing exactly how a past job was configured (resolved
archiveSystemDir, appArgs, queue):

```python
job = ds.tapis.jobs.getJob(jobUuid=uuid)
```

## Not sanctioned

- Submitting jobs (`t.jobs.submitJob`): submission stays behind dapi
  and its approval gating; raw-submission notebooks in community data
  are stale by definition and get modernized, not copied.
- Hand-building job JSON: `ds.jobs.generate` reads the app schema and
  fills defaults; a hand-built dict skips that validation.
- Re-authenticating: `DSClient()` already holds tokens; a second
  client only adds a second failure mode.

If a drop-down becomes routine, that is a missing dapi feature:
propose the wrapper upstream rather than letting raw calls spread.
