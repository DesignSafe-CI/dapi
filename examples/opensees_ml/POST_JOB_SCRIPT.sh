#!/bin/bash
# Runs after PyLauncher completes all sweep tasks.
# Aggregates per-task metrics.json files, trains a linear regression,
# writes ML artifacts into ml_results/.
set -e
python3 aggregate_and_train.py \
    --indir . \
    --outdir ml_results \
    --out-prefix opensees_ml \
    --target period \
    --test-frac 0.20 \
    --seed 12345

python3 postprocess.py \
    --indir ml_results \
    --out-prefix opensees_ml
