# OpenSees ML Example

A simple end-to-end ML workflow on DesignSafe using `dapi` and the
`designsafe-agnostic-app`. Sweeps a 2D cantilever pushover in OpenSeesPy
across `NodalMass × LCol × E`, then fits a linear regression that recovers
`T = 2π·√(M·L³ / (3·E·I))` from the data.

Conceptually mirrors the ML layer in Silvia Mazzoni's
`nga_mpi_ml_example.py` (feature matrix → train/test split → sklearn
`LinearRegression` with `lstsq` fallback → JSON model artifact) but uses
synthetic OpenSees data so it needs no external dataset.

## Files

| File                          | Role                                                                |
| ----------------------------- | ------------------------------------------------------------------- |
| `cantilever.py`               | One PyLauncher task: runs an OpenSeesPy pushover, writes `metrics.json`. |
| `aggregate_and_train.py`      | Aggregates `out_*/metrics.json` and fits the regression.            |
| `postprocess.py`              | Renders diagnostic PDF/PNG (histograms, predicted-vs-truth, residuals, coefficients). |
| `POST_JOB_SCRIPT.sh`          | Invokes `aggregate_and_train.py` and `postprocess.py` after PyLauncher finishes. |
| `PIP_INSTALLS_FILE.txt`       | Extra packages (`scikit-learn`, `matplotlib`) installed inside the job. |
| `DS_OpenSees_ML_Example.ipynb`| Notebook: defines the sweep, submits via `dapi`, inspects outputs.  |

## How it runs

```
sweep grid ──► parametric_sweep.generate ──► runsList.txt + call_pylauncher.py
                                                       │
                                                       ▼
                                       designsafe-agnostic-app (Stampede3)
                                       ├─ Main: python3 call_pylauncher.py
                                       │   └─ N × cantilever.py tasks
                                       │       └─ out_*/metrics.json
                                       └─ POST_JOB_SCRIPT.sh
                                           ├─ aggregate_and_train.py
                                           │   └─ ml_results/*.{json,csv,txt}
                                           └─ postprocess.py
                                               └─ ml_results/*_diagnostics.{pdf,png}
```

Because the physics is exact, the regression should report
`coef ≈ [const, 0.5, 1.5, -0.5]` with `R² = 1.0` — a clean confirmation
that the workflow plumbing is correct.

## Run locally (no Tapis)

```bash
mkdir -p tmp_runs/out_4.19_100_3600 tmp_runs/out_4.99_500_5000
python3 cantilever.py --NodalMass 4.19 --LCol 100 --E 3600 \
    --outDir tmp_runs/out_4.19_100_3600
python3 cantilever.py --NodalMass 4.99 --LCol 500 --E 5000 \
    --outDir tmp_runs/out_4.99_500_5000
python3 aggregate_and_train.py --indir tmp_runs --outdir tmp_runs/ml_results
python3 postprocess.py --indir tmp_runs/ml_results
cat tmp_runs/ml_results/opensees_ml_report.txt
open tmp_runs/ml_results/opensees_ml_diagnostics.pdf  # or .png
```

## Run on DesignSafe

See `DS_OpenSees_ML_Example.ipynb`.
