"""Resubmit the container job; inputs (fixed driver + tarball) already in MyData."""

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

job = ds.jobs.generate(
    app_id="python-s3",
    input_dir_uri=inputs,
    script_filename="run_container.sh",
    node_count=1,
    cores_per_node=1,
    max_minutes=25,
    queue="skx-dev",
    allocation=ALLOCATION,
    extra_env_vars=[
        {"key": "BINARY", "value": "bash"},
        # tacc-apptainer is loaded inside run_container.sh with nounset
        # relaxed; its completion script trips the wrapper's set -u.
    ],
)
job["name"] = "container-site-response-v2"

submitted = ds.jobs.submit(job)
print(f"submitted: {submitted.uuid}", flush=True)
final = submitted.monitor(interval=15)
print("final status:", final, flush=True)

print("\n--- tapisjob.out (probe + conversion + container run) ---")
out = submitted.get_output_content("tapisjob.out", max_lines=500)
print(out[-7000:] if out else "(no output)")

submitted.download_output(
    "inputDirectory/site_response.json", f"{HERE}/site_response.json"
)
print("\nRESULT:", json.dumps(json.load(open(f"{HERE}/site_response.json")), indent=2))
