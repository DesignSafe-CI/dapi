---
name: build-a-dag-workflow
description: Multi-stage studies as server-side DAGs with dapi.workflows
---

# Build a DAG workflow

When one stage's outputs feed the next and the whole thing must run
hands-off, declare the graph and let Tapis Workflows run it
server-side.

```python
from dapi.workflows import JobTask, Workflow

wf = Workflow("sweep-then-train")
sweep = wf.add(JobTask("sweep", sweep_job))
train_job["fileInputs"][0]["sourceUrl"] = sweep.output("archive_uri")
wf.add(JobTask("train", train_job), depends_on=["sweep"])

run = wf.run(ds)  # deploys pipeline, returns handle
run.wait()  # or poll run.status()
```

Archives are deterministic
(`<user>/dapi-workflows/<name>/<run_id>/<task>`), so downstream tasks
reference upstream outputs before anything runs. Fan-out is tasks with
no dependencies between them; fan-in is one task depending on several.
Independent tasks dispatch in parallel. Use `wf.compile(username,
run_id)` to preview tasks, edges, and archive paths without deploying.
