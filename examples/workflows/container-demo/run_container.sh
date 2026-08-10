#!/bin/bash
# Runs a custom container inside an ordinary python-s3 job.
# The image arrives as an image-archive tarball in the input directory,
# so no registry account or login is needed anywhere. Recent docker
# saves OCI layout (blobs/ at the tar root); older ones save the legacy
# docker-archive format, so conversion tries both.
set -uo pipefail
set -x

# Load apptainer here rather than via EXTRA_MODULES: the module's
# bash-completion script is not `set -u` clean, so it must be loaded
# with nounset relaxed.
set +u
module load tacc-apptainer
set -u

export APPTAINER_CACHEDIR="/tmp/apptainer-cache-$$"
mkdir -p "${APPTAINER_CACHEDIR}"

echo "=== probe: can this compute node pull from a registry? ==="
if apptainer exec docker://alpine:3.20 echo "REGISTRY-PULL-OK"; then
    echo "probe result: REGISTRY-PULL-OK"
else
    echo "probe result: REGISTRY-PULL-BLOCKED (archive staging is the way)"
fi

echo "=== convert the staged image archive to SIF ==="
set -e
SIF="/tmp/site-response-$$.sif"
if ! apptainer build "${SIF}" oci-archive:site-response-container.tar; then
    echo "oci-archive transport failed; trying legacy docker-archive"
    apptainer build "${SIF}" docker-archive:site-response-container.tar
fi

echo "=== run the custom TACC-based container ==="
apptainer exec \
    --cleanenv \
    --pwd /data \
    --bind "$PWD":/data \
    "${SIF}" \
    python3 /opt/app/site_response.py

echo "=== container run finished ==="
