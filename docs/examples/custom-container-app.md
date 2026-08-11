# Run Your Own Container

The [custom-container-app notebook](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/custom-container-app.ipynb) registers a container app in two dapi calls and runs a published container image on a Stampede3 compute node.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/custom-container-app.ipynb)

## What the notebook does

1. **Register.** `ds.apps.new("my-container", template="container")` writes the app files and `ds.apps.deploy()` registers the app under your account. The image and command are job parameters, so this one app runs every container you build.
2. **Run.** A job names `CONTAINER_IMAGE=docker://ghcr.io/kks32/python-container-s3:latest`, an image GitHub Actions builds and publishes from [its repository](https://github.com/kks32/python-container-s3), and the compute node pulls and runs it with the input directory bind-mounted at `/data`.
3. **Results.** The containerized analysis computes a soil layer's amplification spectrum, checks its resonant peak against `f0 = Vs/4H`, and the archived report comes back through `get_output_content`.

Swap in your own image by pushing a repository with a Dockerfile; [Custom Containers](../containers.md) covers building and publishing, and [Apps](../apps.md) documents the app files the template writes.
