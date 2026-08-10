# OpenSees ML, Sweep to Regression

An end-to-end machine learning workflow on DesignSafe. A PyLauncher sweep runs a 2D cantilever pushover in OpenSeesPy across a 75-point parameter grid, and a post-script fits a linear regression that recovers the physics from the results, all in one `python-s3` job.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/opensees_ml/DS_OpenSees_ML_Example.ipynb)

For PyLauncher basics, see [PyLauncher Parameter Sweeps](pylauncher.md). For the app settings used here, see the [Generic Python App](python.md).

## The period equation as ground truth

The natural period of a cantilever with tip mass follows

```
T = 2π · sqrt(M · L³ / (3 · E · I))
```

so in log space the exponents are known exactly, 0.5 on mass, 1.5 on length, and -0.5 on modulus. The workflow sweeps `NODAL_MASS x LCOL x EMOD` (5 x 5 x 3 = 75 OpenSeesPy pushover runs), aggregates each task's `metrics.json`, and fits `log T` against the log features with scikit-learn. Because the physics is exact, the regression must report `coef ≈ [0.5, 1.5, -0.5]` with `R² = 1.0`, which makes the example self-checking. Wrong plumbing cannot produce the right coefficients.

## How one job does all of it

Each stage of the `python-s3` job does one piece of the work.

| Stage | Setting | What it does here |
|---|---|---|
| Staging | `UNZIP_INPUTS: inputs.zip` | All eight input files travel as one ZIP, one Tapis transfer instead of eight |
| Pre-script | `PRE_SCRIPT: setup.sh` | Copies the TACC-compiled OpenSeesPy shared library into the job (handles both the `opensees.so` and older `OpenSeesPy.so` layouts) |
| Environment | `PIP_REQUIREMENTS: requirements.txt` | Installs scikit-learn and matplotlib into the temporary per-job environment |
| Main | `call_pylauncher.py` | PyLauncher dispatches the 75 `cantilever.py` tasks across the node's cores |
| Post-script | `POST_SCRIPT: ml_post.sh` (required) | Aggregates `out_*/metrics.json`, fits the regression, renders diagnostic plots |

The sweep definition and submission are three notebook cells.

```python
sweep = {
    "NODAL_MASS": [4.19, 4.39, 4.59, 4.79, 4.99],
    "LCOL": [100, 200, 300, 400, 500],
    "EMOD": [3600, 4000, 5000],
}

commands = ds.jobs.parametric_sweep.generate(command, sweep, str(input_dir))
job = ds.jobs.parametric_sweep.submit(...)
```

The placeholder is named `EMOD` rather than `E` on purpose. Token-style placeholders match anywhere a word appears, so a single-letter key like `E` also rewrites the `--E` flag in every generated command.

## Results

The archived job contains `ml_results/` with the fitted model as JSON, per-task predictions as CSV, and a diagnostics figure (histograms, predicted versus truth, residuals, coefficients). The notebook downloads and displays them.

```python
job.download_output(
    "inputDirectory/ml_results/opensees_ml_diagnostics.png",
    "opensees_ml_diagnostics.png",
)
```

On Stampede3, the 75 tasks take about 42 seconds of task time, and the regression recovers `[0.500, 1.500, -0.500]` with `R² = 1.0`.

## The same study as a DAG workflow

`DS_OpenSees_ML_Workflow_DAG.ipynb` splits the pipeline into two jobs, a 48-core sweep and a one-core training task, connected as an explicit graph with `dapi.workflows`. dapi points the training job's input at the sweep's archive through an output reference and resolves it to the real path before submitting, retraining costs one core instead of a resweep, and the run streams live per-task progress in the notebook. The [Workflows guide](../workflows.md) covers the API.

## Files

| File | Role |
|---|---|
| `DS_OpenSees_ML_Example.ipynb` | Defines the sweep, bundles inputs, submits, inspects outputs |
| `DS_OpenSees_ML_Workflow_DAG.ipynb` | The same study as a two-job DAG via `dapi.workflows` |
| `cantilever.py` | One task, an OpenSeesPy pushover that writes `metrics.json` |
| `aggregate_and_train.py` | Collects all `metrics.json` and fits the regression |
| `postprocess.py` | Renders the diagnostics PDF and PNG |
| `setup.sh` | Pre-script that stages TACC OpenSeesPy |
| `ml_post.sh` | Post-script that runs training and plotting on the compute node |
| `requirements.txt` | Extra packages for the per-job environment |

The example also runs locally without Tapis. The [README](https://github.com/DesignSafe-CI/dapi/tree/main/examples/opensees_ml) shows the two-task local dry run.
