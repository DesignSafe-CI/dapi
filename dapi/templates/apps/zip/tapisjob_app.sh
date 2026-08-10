#!/bin/bash
# __APP_ID__: EDIT THIS WRAPPER. It runs on the compute node after Tapis
# stages the job's Input Directory. The two job parameters are
#
#   COMMAND        shell command, run inside the staged input directory
#   EXTRA_MODULES  comma-separated TACC modules to load first (optional)
#
# Outputs written to the input directory are archived when the job ends.
# Replace the COMMAND line at the bottom with your own launch logic when
# a single command is not enough (MPI launchers, staging, post steps).
set -euo pipefail
set -x

INPUTSCRIPT="${1:-}"  # unused; kept for parity with python-s3 calling convention

: "${COMMAND:?COMMAND is required}"

# Lmod modulefiles and their completion hooks are not nounset-clean,
# so module loads run with set -u relaxed.
if [[ -n "${EXTRA_MODULES:-}" ]]; then
    IFS=',' read -ra MODS <<< "${EXTRA_MODULES}"
    for mod in "${MODS[@]}"; do
        mod="$(echo "${mod}" | xargs)"
        if [[ -n "${mod}" ]]; then
            set +u
            module load "${mod}"
            set -u
        fi
    done
fi

cd "${_tapisExecSystemInputDir}/inputDirectory"

/bin/bash -c "${COMMAND}"

echo "Job execution finished at: $(date)"
