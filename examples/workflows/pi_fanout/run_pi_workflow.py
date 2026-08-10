"""Parallel fan-out/fan-in workflow on python-s3.

Three 1-core Monte-Carlo shards run in parallel; an aggregator fans
them in through the run-root pattern (its single Input Directory is the
parent directory of every task archive in this run).

Run: python run_pi_workflow.py  (needs dapi auth and an allocation)
"""

import json
import os
import time

from dapi import DSClient
from dapi.workflows import JobTask, Workflow

ALLOCATION = os.environ.get("TACC_ALLOCATION", "DS-Portal-SPARC2026")
HERE = os.path.dirname(os.path.abspath(__file__))

ds = DSClient()
username = ds.tapis.username

# The run root must be known before run(), so choose the run_id here.
run_id = time.strftime("%Y%m%d-%H%M%S")
run_root_uri = (
    f"tapis://designsafe.storage.default/{username}/dapi-workflows/pi-demo/{run_id}"
)

# Stage the shard script once (shared by all three shards) and the
# aggregator script into the run root, where the fan-in will find it.
shard_inputs = (
    f"tapis://designsafe.storage.default/{username}/dapi-workflows-demo/pi-inputs"
)
ds.files.upload(f"{HERE}/shard_pi.py", f"{shard_inputs}/shard_pi.py")
ds.files.upload(f"{HERE}/aggregate_pi.py", f"{run_root_uri}/aggregate_pi.py")

wf = Workflow("pi-demo")
shard_ids = []
for tag, seed in (("pi-a", 11), ("pi-b", 22), ("pi-c", 33)):
    job = ds.jobs.generate(
        app_id="python-s3",
        input_dir_uri=shard_inputs,
        script_filename="shard_pi.py",
        node_count=1,
        cores_per_node=1,
        max_minutes=10,
        queue="skx-dev",
        allocation=ALLOCATION,
        extra_env_vars=[
            {"key": "SEED", "value": str(seed)},
            {"key": "N_SAMPLES", "value": "2000000"},
        ],
    )
    job["name"] = tag
    # Archive only the shard result. Fan-in staging copies every parent
    # archive, so lean shard archives directly shrink the aggregator's
    # input transfer (measured: minutes to seconds on this workflow).
    job["parameterSet"]["archiveFilter"] = {
        "includes": ["pi_shard.json", "**/pi_shard.json"],
        "includeLaunchFiles": False,
    }
    wf.add(JobTask(tag, job))  # no edges: the three shards run in parallel
    shard_ids.append(tag)

agg = ds.jobs.generate(
    app_id="python-s3",
    input_dir_uri=run_root_uri,  # the run root: all parent archives land here
    script_filename="aggregate_pi.py",
    node_count=1,
    cores_per_node=1,
    max_minutes=10,
    queue="skx-dev",
    allocation=ALLOCATION,
)
agg["name"] = "pi-aggregate"
# The aggregator stages the whole run root as its input; without a
# filter it would archive that entire copy back. Keep only the report.
agg["parameterSet"]["archiveFilter"] = {
    "includes": ["pi_estimate.json", "**/pi_estimate.json"],
    "includeLaunchFiles": False,
}
# A plain URI carries no OutputRef edge, so declare the fan-in explicitly.
wf.add(JobTask("aggregate", agg), depends_on=shard_ids)

wf.validate()
results = wf.run(ds, run_id=run_id, poll_interval=20, timeout_minutes=90)

ds.files.download(
    results["aggregate"]["archive_uri"] + "/inputDirectory/pi_estimate.json",
    "pi_estimate.json",
)
print(json.dumps(json.load(open("pi_estimate.json")), indent=2))
