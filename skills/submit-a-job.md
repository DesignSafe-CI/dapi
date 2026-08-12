---
name: submit-a-job
description: The canonical dapi job lifecycle, from input folder to archived results
---

# Submit a job

Every dapi run follows one lifecycle. Deviating from it is the main
source of broken workflows.

```python
from dapi import DSClient

ds = DSClient()  # auth from env or .env

input_uri = ds.files.to_uri(str(input_dir))  # DesignSafe path -> tapis://
job = ds.jobs.generate(
    app_id="python-s3",
    input_dir_uri=input_uri,
    script_filename="run.py",
    max_minutes=30,
    allocation="YOUR-ALLOCATION",
)
submitted = ds.jobs.submit(job)
final = submitted.monitor(interval=15)  # blocking poll
ds.jobs.interpret_status(final, submitted.uuid)

archive_uri = submitted.archive_uri
for item in ds.files.list(archive_uri):
    print(item.name, item.type)
```

Work from a writable folder. On the DesignSafe JupyterHub only MyData
is writable; CommunityData is read-only:

```python
mydata = Path.home() / "MyData"
work_root = mydata if mydata.is_dir() else Path.cwd()
```

Inspect `job` before submitting; `generate` fills app defaults and you
override fields like `job["nodeCount"]` afterwards. Monitoring stops at
a terminal state (FINISHED, FAILED, CANCELLED, STOPPED); BLOCKED is a
waiting state and resolves on its own.
