# Workflow explorations: parallel DAGs and custom containers

Exploration branch notes, 2026-08-09. Everything here builds on the v0.6.0 `dapi.workflows` module. The two questions explored are (1) what a parallel fan-out/fan-in DAG looks like on `python-s3`, and (2) how a modifiable container app would let workflows run tools like gmprocess that need their own software stack.

## Do we use python-s3 now?

Yes. Both nodes of the OpenSees ML workflow are `python-s3` jobs (the 48-core PyLauncher sweep and the 1-core training run). `python-s3` is the natural node type for workflows because one app covers any Python or shell payload, its lifecycle hooks (UNZIP_INPUTS, PRE_SCRIPT, PIP_REQUIREMENTS, POST_SCRIPT) remove per-app wrapper work, and `sequence_job()` already generates drivers for it.

## Finding: strictFileInputs and the run-root fan-in pattern

`python-s3` declares `strictFileInputs: true` with exactly one file input (`Input Directory`). A job therefore cannot list several upstream archives as extra inputs, which a fan-in node (one task consuming N parent outputs) seems to need.

The deterministic archive layout already solves this. Every task of a run archives under one run root:

```
<user>/dapi-workflows/<name>/<run_id>/
    shard-a/inputDirectory/...   <- parent A's outputs
    shard-b/inputDirectory/...   <- parent B's outputs
    shard-c/inputDirectory/...   <- parent C's outputs
    aggregate_script.py          <- uploaded before the run
```

The fan-in task's single Input Directory is the run root itself. By DAG ordering it only stages after every parent has finished archiving, so it receives all parent outputs in one staged tree. The pattern needs an explicit `run_id` (so the run root is known before `run()`) and an explicit `depends_on` list (a plain string URI carries no OutputRef edge).

Proven live by the pi spike below. Candidate API sugar for a follow-up: `wf.run_root(run_id)` returning the URI, or a `fan_in=True` task flag that wires both the input and the edges.

## Live spike: parallel fan-out, fan-in aggregation

Four 1-core `python-s3` jobs on skx-dev. Three Monte-Carlo pi shards with different seeds run in parallel (no edges between them); an aggregator depending on all three sums their counts from the staged run root.

```
pi-a (seed 11) ──┐
pi-b (seed 22) ──┼──> aggregate (reads */inputDirectory/pi_shard.json)
pi-c (seed 33) ──┘
```

Observed (run `pi-demo-20260809-201357`, all four tasks completed):

- The three shards were submitted within 7 seconds of each other and ran on Stampede3 **simultaneously** (all three RUNNING at 20:15:49).
- `aggregate` was submitted 4 seconds after the last shard reached FINISHED, and its staged run root contained all three shard archives; the estimate came out `pi = 3.1409587` from 6,000,000 samples (abs error 6.3e-4, at the statistical limit).
- Overhead profile: shard wall time was ~3 minutes each (seconds of compute), while the aggregator spent ~11 minutes staging the run root and ~11 minutes archiving it back.

### Archive filters, measured

A second run (`pi-demo-20260809-205602`, same seeds, identical pi estimate) added Tapis `archiveFilter`s: shards archive only `pi_shard.json`, the aggregator only `pi_estimate.json` (both with `includeLaunchFiles: false`). `run_pi_workflow.py` carries the filters. Effect, filtered vs unfiltered:

| Phase | Unfiltered | Filtered |
|---|---|---|
| Fan-out, 3 shards submitted to all FINISHED | 3.8 min | 2.8 min (per-shard archiving 2.5 min to ~30 s) |
| Aggregate staging (run root in) | 10.8 min | 10.9 min, unchanged |
| Aggregate archiving (results out) | 11.2 min | 41 s |
| Whole workflow | ~27 min | ~16 min |

Two conclusions. Filters should be default practice for workflow nodes (archiving scales with data volume and the filter cut it 16x). Fan-in staging does NOT scale with data volume; ~11 minutes to stage four small files points at Tapis transfer-service scheduling latency for directory inputs, which is worth raising with TACC alongside the Workflows ticket, and means the run-root pattern's cost is a roughly fixed latency rather than a data-size penalty.

## Custom containers: the gmprocess path

The blocker recorded earlier for gmprocess (and MPI and Docker training material) was the absence of a public production container recipe. The `opensees-express` app shows DesignSafe already runs arbitrary registry containers inside ZIP-runtime apps; its wrapper is essentially one line:

```bash
apptainer run --cleanenv --bind "${inputDirectory}":/data docker://taccaci/opensees:latest ...
```

That pattern generalizes into a single deployable app, drafted in `container-s3/` here, where the image is a job parameter rather than an app constant:

- `CONTAINER_IMAGE`: `docker://usgs/gmprocess:latest`, or a `.sif` staged in the input directory for air-gapped compute nodes.
- `COMMAND`: run inside the container with the input directory bind-mounted at `/data`, so outputs archive normally.

One app then serves gmprocess, custom research codes, and any registry image, and every such job is automatically a valid workflow node. A gmprocess record-processing study becomes:

```
fetch-events (python-s3, pulls waveforms) ──> gmprocess shards (container-s3, parallel) ──> aggregate report (python-s3)
```

**Deployed and verified.** `container-s3` v0.1.0 is registered under `kks32` via `ds.apps.deploy()` (the app.json and wrapper here are also dapi's shipped `container` template for `ds.apps.scaffold()`). Test job `e445d885` FINISHED on Stampede3: `docker://python:3.11-slim` pulled on the compute node, COMMAND executed at `/data`, outputs archived. Two config lessons from the shakedown, both fixed here and in the template: pin `execSystemExecDir`/`InputDir`/`OutputDir` to `${JobWorkingDir}` (Tapis otherwise defaults them to `<workingDir>/jobs/<uuid>` and the wrapper's paths miss), and default the archive dir with `${JobOwner}/...`, never `HOST_EVAL($HOME)` (403 on designsafe.storage.default). Remaining follow-ups: test the gmprocess image and `shareApp` to collaborators.

### Working demonstration without any new app: `container-demo/`

The pattern runs today through the deployed `python-s3` app. A custom image built on `tacc/tacc-base:ubuntu22.04-impi19.0.9-common` (numpy plus a site-response payload with a resonance self-check) is `docker save`d to a tarball, uploaded to MyData with dapi, and executed on the compute node by a bash driver that converts the archive to SIF and `apptainer exec`s it. No registry account exists anywhere in the loop. Three sharp edges found on the way, all handled in the driver:

- `EXTRA_MODULES=tacc-apptainer` kills the job before user code runs. The module's bash-completion script references `BASH_COMPLETION_DEBUG` unbound, and the `python-s3` wrapper runs `set -u`. Load the module inside the driver with nounset relaxed. A `python-s3` wrapper fix (module loads under relaxed `set -u`, since Lmod completion files are not nounset-clean) is patched in the WMA-Tapis-Templates draft for the next app revision.
- Recent Docker (containerd image store) saves **OCI layout**, so the tarball is `oci-archive:`, not `docker-archive:`. The driver tries both.
- The apptainer cache belongs on node-local `/tmp`, not `$HOME` (quota).

Verified on Stampede3 (job `container-site-response-v2`, FINISHED). The 2.8 GB OCI archive converted to SIF on the node and the containerized payload recovered the resonant peak at 2.00 Hz, matching `f0 = Vs/4H` exactly, self-check passed.

**Measured answer to the registry question: compute nodes CAN pull.** The probe `apptainer exec docker://alpine:3.20` succeeded on the compute node, `REGISTRY-PULL-OK`. Consequences ripple through the design. Archive staging is the no-registry-account option, not a necessity; a published image (`docker://usgs/gmprocess`, a group's ghcr image) can be referenced directly by a job or workflow node with zero image transfer through DesignSafe storage; and the `container-s3` draft app's `docker://` path is viable as the primary mode, with `.sif`/archive staging as the offline fallback.

## Ranked next steps

1. **Send the TACC ticket** authorizing the Workflows service in the designsafe tenant; flip the private `_BACKEND` switch when it lands. Everything else works today without it.
2. **Merge `workflows` into main and release v0.6.0** (DAG workflows + project permissions).
3. **Promote the fan-out/fan-in pattern**: turn the pi spike into a documented example notebook and add the run-root sugar to the API.
4. **Deploy and validate `container-s3`**, then build the gmprocess DAG on it. This also unblocks the parked gmprocess/MPI/Docker training material with a working notebook.
5. **rAPIdtools improvement pass** (deferred earlier): its heavy analyzers become `container-s3` or `python-s3` workflow nodes; its linear priority-sorted Pipeline stays for light in-notebook steps.
6. **Resume support** for interrupted client-driven runs (state file mapping task to job UUID, skip FINISHED tasks on rerun with the same run_id).
