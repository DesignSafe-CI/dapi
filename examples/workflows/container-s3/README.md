# container-s3

container-s3 is a generic Tapis app for Stampede3 that runs **any container image** as a job. `CONTAINER_IMAGE` (a `docker://` reference, a staged `.sif`, or a `docker save` tarball) and `COMMAND` are job parameters, and the input directory is bind-mounted at `/data` so outputs archive normally. The design follows `python-s3` for the lifecycle and ZIP runtime, and `opensees-express`, which already runs `docker://taccaci/opensees` via apptainer on DesignSafe.

In a workflow, any container becomes a DAG node without a new Tapis app, which unlocks gmprocess-style pipelines. See `../EXPLORATION.md` for the design, the deployment checklist, and the open questions (registry access from compute nodes, apptainer cache location).
