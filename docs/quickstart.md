# Quick Start

```bash
pip install dapi
```

```python
from dapi import DSClient

ds = DSClient()

# Translate path and submit a job
input_uri = ds.files.to_uri("/MyData/analysis/input/")

job_request = ds.jobs.generate(
    app_id="matlab-r2023a",
    input_dir_uri=input_uri,
    script_filename="run_analysis.m",
    max_minutes=30,
    allocation="your_allocation",
)

job = ds.jobs.submit(job_request)
job.monitor()
```

That's it. `DSClient()` handles authentication and TMS credentials automatically.

## More examples

### Find apps

```python
ds.apps.find("matlab")
ds.apps.find("opensees")
```

### List files

```python
files = ds.files.list(input_uri)
for f in files:
    print(f.name)
```

### Check job results

```python
job.print_runtime_summary()

outputs = job.list_outputs()
for output in outputs:
    print(output.name)

stdout = job.get_output_content("tapisjob.out")
print(stdout)
```

### Query research databases

```python
df = ds.db.ngl.read_sql("SELECT * FROM SITE LIMIT 5")
print(df)
```

### PyLauncher parameter sweep

```python
sweep = {"ALPHA": [0.3, 0.5, 3.7], "BETA": [1.1, 2.0, 3.0]}

ds.jobs.parametric_sweep.generate(
    "python3 simulate.py --alpha ALPHA --beta BETA --output out_ALPHA_BETA",
    sweep,
    "/home/jupyter/MyData/sweep_demo/",
)

job = ds.jobs.parametric_sweep.submit(
    "/MyData/sweep_demo/",
    app_id="designsafe-agnostic-app",
    allocation="your_allocation",
    node_count=1,
    cores_per_node=48,
)
job.monitor()
```

## Next steps

- [Jobs](jobs.md) — advanced job configuration, error handling, monitoring
- [Database](database.md) — research data queries
- [Examples](examples.md) — full notebook workflows
