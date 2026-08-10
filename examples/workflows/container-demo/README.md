# Custom container in an ordinary job (no registry, no new app)

This demo runs a custom container on Stampede3 through the deployed `python-s3` app. The image is built locally on a TACC base, saved as a tarball, and executed on the compute node with apptainer's `docker-archive` support. No registry account, no image publishing, no new Tapis app deployment.

```
laptop:  docker build (FROM tacc/tacc-base:ubuntu22.04-impi19.0.9-common)
         docker save -> site-response-container.tar
         dapi upload -> MyData
job:     python-s3 with BINARY=bash, EXTRA_MODULES=tacc-apptainer
         run_container.sh -> apptainer exec docker-archive:site-response-container.tar
```

| File | Role |
|---|---|
| `Dockerfile` | Custom image on the TACC Ubuntu 22.04 + Intel MPI base |
| `site_response.py` | The containerized payload, a soil-layer amplification spectrum with a built-in resonance self-check |
| `run_container.sh` | Job driver, probes registry access then runs the staged image |
| `submit_container_job.py` | Uploads image + driver, submits, monitors, fetches results |

The driver also probes whether the compute node can pull `docker://` images directly, which decides whether the tarball staging is a necessity or a convenience. See `../EXPLORATION.md` for the measured answer and the `container-s3/` draft app that turns this pattern into a first-class Tapis app.
