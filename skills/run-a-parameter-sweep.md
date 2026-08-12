---
name: run-a-parameter-sweep
description: Many related runs in one HPC job with parametric_sweep and PyLauncher
---

# Run a parameter sweep

One job, many tasks. `ds.jobs.parametric_sweep` writes a task list,
uploads inputs once, and PyLauncher fans tasks across the cores of the
job.

```python
sweep = ds.jobs.parametric_sweep(
    app_id="python-s3",
    script="oscillator.py",
    sweep_parameter="frequency",
    sweep_values=[round(0.2 + 0.075 * i, 3) for i in range(25)],
    input_dir=str(work_dir),
    allocation="YOUR-ALLOCATION",
    cores_per_node=25,
)
submitted = sweep.submit()
```

Size cores_per_node to the task count when tasks are serial; a task
list longer than the core count simply queues inside the job. Each
task writes its own output file; collect them from the archive by
pattern. Pitfalls that surface at scale: shared scratch collisions
(write per-task subdirectories), and tasks that read the same input
file are fine, tasks that write one are not.
