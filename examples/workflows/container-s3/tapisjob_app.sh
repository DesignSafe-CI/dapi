#!/bin/bash
set -euo pipefail
set -x

# container-s3 (DRAFT): run ANY container image as a Tapis job on Stampede3.
#
# The image is a job parameter, not baked into the app, so one deployed app
# covers gmprocess, custom research codes, and anything on a registry:
#
#   CONTAINER_IMAGE  docker://usgs/gmprocess:latest      (pulled at job start)
#                    or a .sif filename inside inputDirectory (pre-staged)
#   COMMAND          shell command run inside the container, cwd /data
#
# inputDirectory is bind-mounted at /data, so the command reads staged
# inputs and writes outputs to the same folder Tapis archives.

INPUTSCRIPT="${1:-}"  # unused; kept for parity with python-s3 calling convention

: "${CONTAINER_IMAGE:?CONTAINER_IMAGE is required (docker://... or a staged .sif)}"
: "${COMMAND:?COMMAND is required}"

# Lmod completion hooks are not nounset-clean; relax set -u to load
set +u
module load tacc-apptainer
set -u

# Inputs land in the exec-system input dir regardless of app dir layout
INPUT_DIR="${_tapisExecSystemInputDir}/inputDirectory"

IMAGE="${CONTAINER_IMAGE}"
if [[ "${IMAGE}" != docker://* && "${IMAGE}" != *.sif && "${IMAGE}" != *.tar ]]; then
    echo "CONTAINER_IMAGE must be docker://<image>, a .sif file, or a .tar archive" >&2
    exit 64
fi
# Bare filenames mean the image was staged into the input directory
if [[ "${IMAGE}" != docker://* && "${IMAGE}" != /* ]]; then
    IMAGE="${INPUT_DIR}/${IMAGE}"
fi

# docker:// pulls convert to SIF in the apptainer cache; keep it on the
# fast local disk of the node instead of a small $HOME quota.
export APPTAINER_CACHEDIR="${APPTAINER_CACHEDIR:-/tmp/apptainer-cache-$$}"

# A docker-save tarball converts to SIF on the node. Recent Docker saves
# OCI layout; older ones save the legacy docker-archive format.
if [[ "${IMAGE}" == *.tar ]]; then
    SIF="/tmp/container-image-$$.sif"
    if ! apptainer build "${SIF}" "oci-archive:${IMAGE}"; then
        apptainer build "${SIF}" "docker-archive:${IMAGE}"
    fi
    IMAGE="${SIF}"
fi

apptainer exec \
    --cleanenv \
    --bind "${INPUT_DIR}":/data \
    "${IMAGE}" \
    /bin/sh -c "cd /data && ${COMMAND}"

EXITCODE=$?
if [ ${EXITCODE} -ne 0 ]; then
    echo "Container exited with status ${EXITCODE}" >&2
    echo ${EXITCODE} > "${_tapisExecSystemOutputDir}/tapisjob.exitcode"
fi
echo "Job execution finished at: $(date)"
