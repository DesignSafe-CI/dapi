# Workflows

`dapi.workflows` runs a multi-stage study as a directed acyclic graph of Tapis jobs, with each job a node and each dependency an edge. A sweep that feeds a training job is the typical shape; the training job consumes the sweep's archived output.

![A two-node workflow. An output reference connects the sweep job to the train job, and the referenced archive path is known before either job is submitted.](images/workflow-dag.png)

The concepts behind the design, and an interactive view of the scheduler, live in the [DesignSafe Workflows book](https://designsafe-ci.github.io/ds-workflows/dag-workflows).

Every task runs as a real Tapis job on HPC, on the same queues and against the same allocation as a job submitted by hand. `run()` coordinates the graph from your notebook or script, submitting each job with your credentials the moment its dependencies finish and running independent branches in parallel.

## Step 1. Generate the job requests

Every workflow node is an ordinary job request from `ds.jobs.generate()`. Define each stage exactly as if it were a standalone job, sized to its own resources; the 48-core sweep and the 1-core trainer below are the [OpenSees ML example](examples/opensees_ml.md)'s two stages.

```python
from dapi import DSClient

ds = DSClient()

sweep_job = ds.jobs.generate(
    app_id="python-s3",
    input_dir_uri=staged_uri,
    script_filename="call_pylauncher.py",
    node_count=1,
    cores_per_node=48,
    max_minutes=30,
    queue="skx-dev",
    allocation=allocation,
)
train_job = ds.jobs.generate(
    app_id="python-s3",
    input_dir_uri="tapis://designsafe.storage.default/placeholder",  # replaced in Step 3
    script_filename="ml_post.sh",
    node_count=1,
    cores_per_node=1,
    max_minutes=15,
    queue="skx-dev",
    allocation=allocation,
    extra_env_vars=[{"key": "BINARY", "value": "bash"}],
)
```

## Step 2. Add the tasks to a workflow

Dependencies are always declared, never inferred from the order you add tasks.

```python
from dapi.workflows import Workflow, JobTask

wf = Workflow("opensees-ml")
sweep = wf.add(JobTask("sweep", job_dict=sweep_job))
train = wf.add(JobTask("train", job_dict=train_job), depends_on=["sweep"])
```

## Step 3. Wire outputs between tasks

A task references an upstream task's archive with `task.output()`. The reference does two things at once. It wires the data flow, and it declares the dependency edge, so the explicit `depends_on` above becomes optional.

```python
train_job["fileInputs"][0]["sourceUrl"] = sweep.output(
    "archive_uri", suffix="/inputDirectory"
)
train = wf.add(JobTask("train", job_dict=train_job))
```

References resolve before anything is submitted. Each run assigns every task a deterministic archive directory under `MyData/dapi-workflows/<workflow>/<run_id>/<task>`, so at compile time the reference becomes a concrete `tapis://` path. The `suffix` selects a subfolder of the upstream archive, for example the `inputDirectory` a `python-s3` job archives its results into.

Only `archive_uri` can be referenced. A job's UUID or status does not exist before the run, so referencing them raises a validation error.

## Step 4. Validate, visualize, preview

`validate()` rejects cycles, duplicate task ids, and references to unknown tasks. `visualize()` draws the graph with every edge labeled by the output flowing across it, so a wiring mistake is visible before it costs a queue wait.

```python
wf.validate()
wf.visualize()
```

![The visualize() output for the two-node workflow: sweep and train boxes connected by an edge labeled archive_uri.](images/workflow-visualize.png)

`compile()` shows exactly what a run will submit, one job definition per task with archives assigned and references resolved.

```python
tasks, archives = wf.compile(ds.tapis.username, run_id="preview")
print(tasks[1]["tapis_job_def"]["fileInputs"][0]["sourceUrl"])
# tapis://designsafe.storage.default/<you>/dapi-workflows/opensees-ml/preview/sweep/inputDirectory
```

## Step 5. Run and watch

```python
results = wf.run(ds)
```

While the run is active, `run()` streams timestamped status transitions for every task, so a notebook shows each node advance from submission through completion.

```
[10:32:01] workflow 'opensees-ml-20260809-103201': 2 tasks
[10:32:04]   task sweep: submitted (job 8f2c...-007)
[10:32:35]   task sweep: SUBMITTED -> QUEUED
[10:41:12]   task sweep: QUEUED -> RUNNING
[10:58:44]   task sweep: RUNNING -> FINISHED
[10:58:45]   task train: submitted (job a41d...-007)
```

| Parameter | Default | Meaning |
|---|---|---|
| `run_id` | timestamp | Names this run's archive tree; pass one explicitly when a task needs the run root before `run()` |
| `poll_interval` | 30 | Seconds between status polls |
| `timeout_minutes` | 240 | Stop waiting after this long |
| `progress` | `True` | Stream per-task transitions |

## Step 6. Collect results

`run()` returns a mapping from task id to `status`, `message`, `archive_uri`, and `uuid`. Every task's outputs sit at its deterministic archive path.

```python
ds.files.download(
    results["train"]["archive_uri"] + "/inputDirectory/ml_results/report.txt",
    "report.txt",
)
```

## Failure semantics

Tasks whose upstream failed are never submitted. They are reported as `blocked`, and the raised `WorkflowExecutionError` carries the per-task detail. A failed branch never cancels its siblings; independent branches run to completion, and their archives survive for a fixed rerun. A kernel that dies mid-run does not stop already-submitted jobs, and `ds.jobs.job(uuid)` re-attaches to them. Tasks not yet submitted when the coordinator dies stay unsubmitted; rerunning the workflow starts a fresh `run_id`.

## Parallel branches and fan-in

Tasks with no edges between them are submitted together and polled together, each as its own job with its own resources. A downstream task that depends on all of them becomes the fan-in.

```python
wf = Workflow("regional-study")
a = wf.add(JobTask("shard-a", job_a))  # no edges between these three:
b = wf.add(JobTask("shard-b", job_b))  # all submitted at once
c = wf.add(JobTask("shard-c", job_c))
wf.add(JobTask("aggregate", agg_job), depends_on=["shard-a", "shard-b", "shard-c"])
```

![Three shards fan in to one aggregate task whose single input directory is the run root holding every shard's archive.](images/workflow-fanin.png)

Most DesignSafe apps, `python-s3` included, accept exactly one input directory (`strictFileInputs`), yet a fan-in needs every parent's output. All tasks of a run archive under one run root, so the aggregator's single input directory is the run root itself, and DAG ordering guarantees it stages only after every parent has archived. The app never changes. This is the **run-root pattern**. Choose the `run_id` yourself so the run root is known up front, and upload the aggregator's script into it before running.

```python
run_id = time.strftime("%Y%m%d-%H%M%S")
run_root = f"tapis://designsafe.storage.default/{ds.tapis.username}/dapi-workflows/regional-study/{run_id}"
ds.files.upload("aggregate.py", f"{run_root}/aggregate.py")
agg_job = ds.jobs.generate(app_id="python-s3", input_dir_uri=run_root,
                           script_filename="aggregate.py", ...)
...
results = wf.run(ds, run_id=run_id)
```

Inside the aggregator, each parent's outputs sit at `<task_id>/inputDirectory/`. The [pi fan-out example](https://github.com/DesignSafe-CI/dapi/tree/main/examples/workflows/pi_fanout) runs this exact shape on Stampede3. Three Monte-Carlo shards run in parallel, and the aggregator submits the moment the last shard finishes.

## Archive filters

By default a `python-s3` task archives its whole working copy, including the staged inputs, and fan-ins re-stage everything their parents archived. Add a Tapis `archiveFilter` to every workflow node so it archives only its result files.

```python
job["parameterSet"]["archiveFilter"] = {
    "includes": ["metrics.json", "**/metrics.json"],
    "includeLaunchFiles": False,
}
```

On the pi workflow, the filter cut the aggregator's archiving from 11.2 minutes to 41 seconds and the whole workflow from 27 to 16 minutes. Staging time did not shrink with volume, so directory staging carries a roughly fixed Tapis transfer latency regardless of size; budget for it when sizing many-node graphs.

## Fuse sequential steps into one job

Separate tasks each pay a queue wait. When a linear sequence of steps can share one node, `sequence_job()` packs the steps into a single `python-s3` job that runs them in order and fails at the first failing step. The result is an ordinary job request, so it can also serve as one node inside a larger graph.

```python
from dapi.workflows import sequence_job

fused = sequence_job(
    ds,
    steps=["python3 call_pylauncher.py", "bash ml_post.sh"],
    input_dir_uri=staged_uri,
    node_count=1,
    cores_per_node=48,
    max_minutes=45,
    queue="skx-dev",
    allocation="MyAllocation",
)
job = ds.jobs.submit(fused)
```

Choose the graph when stages need different resources or fan out; choose the fused job when they share a machine and always run together.

## Containers as workflow nodes

Tools that need their own software stack run as containers inside ordinary `python-s3` jobs, so they drop into a graph unchanged. Compute nodes pull registry images directly (`apptainer exec docker://usgs/gmprocess ...`), and unpublished images travel as `docker save` tarballs staged like any input file, converted to SIF on the node. The [container-demo example](https://github.com/DesignSafe-CI/dapi/tree/main/examples/workflows/container-demo) is the working reference, including the driver script and its two sharp edges (load `tacc-apptainer` with `set -u` relaxed; recent Docker saves OCI layout, so convert with `oci-archive:`).

## Full example

The [OpenSees ML DAG notebook](examples/opensees_ml.md) runs a 75-simulation OpenSees sweep and a training job as a two-node workflow on Stampede3.
