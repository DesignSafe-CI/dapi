"""Run a custom TACC-based container inside an ordinary python-s3 job.

The image was built locally (FROM tacc/tacc-ubuntu22), saved with
`docker save`, and is staged to the job as a tarball; the job driver
runs it via `apptainer exec docker-archive:...`. No registry, no new
Tapis app.
"""

import json
import os

from dapi import DSClient

HERE = os.path.dirname(os.path.abspath(__file__))
ALLOCATION = "DS-Portal-SPARC2026"

ds = DSClient()
username = ds.tapis.username

inputs = (
    f"tapis://designsafe.storage.default/{username}/dapi-workflows-demo/container-demo"
)
print("uploading driver + image tarball (this is the big transfer)...", flush=True)
ds.files.upload(f"{HERE}/run_container.sh", f"{inputs}/run_container.sh")
ds.files.upload(
    f"{HERE}/site-response-container.tar", f"{inputs}/site-response-container.tar"
)

job = ds.jobs.generate(
    app_id="python-s3",
    input_dir_uri=inputs,
    script_filename="run_container.sh",
    node_count=1,
    cores_per_node=1,
    max_minutes=20,
    queue="skx-dev",
    allocation=ALLOCATION,
    extra_env_vars=[
        {"key": "BINARY", "value": "bash"},
        {"key": "EXTRA_MODULES", "value": "tacc-apptainer"},
    ],
)
job["name"] = "container-site-response"

submitted = ds.jobs.submit(job)
print(f"submitted: {submitted.uuid}", flush=True)
final = submitted.monitor(interval=15)
print("final status:", final, flush=True)

print("\n--- tapisjob.out (probe + container run) ---")
out = submitted.get_output_content("tapisjob.out", max_lines=400)
print(out[-6000:] if out else "(no output)")

submitted.download_output(
    "inputDirectory/site_response.json", f"{HERE}/site_response.json"
)
print("\nRESULT:", json.dumps(json.load(open(f"{HERE}/site_response.json")), indent=2))
