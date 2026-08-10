# Build Your Own Tapis App

The [custom-app notebook](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/custom-app.ipynb) develops a Tapis app end to end with dapi: create app.json and the wrapper from a template, edit the definition, register the app under your own account, submit a job against it, and read the results.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/custom-app.ipynb)

## From two calls to archived results

1. **Scaffold.** `ds.apps.new("my-first-app", template="zip")` writes `app.json` and `tapisjob_app.sh`, then the notebook prints both so every field is visible.
2. **Edit.** The notebook edits the JSON in place, adding a description and small serial defaults (`skx-dev`, one core, ten minutes).
3. **Deploy.** `ds.apps.deploy("my-first-app")` zips the wrapper, uploads it to MyData, and registers version 0.1.0 under your ownership. Rerunning updates the app in place.
4. **Run.** The notebook uploads a pure-stdlib analysis script and its data as job inputs, and a job against the new app runs `COMMAND="python3 analyze.py example_input.txt"` on one skx-dev core.
5. **Results.** The archived `summary.json` comes back through `get_output_content`, and the closing cells show sharing (`shareApp`) and cleanup (`deleteApp`).

The analysis script travels with the job, not with the app, which is the pattern that lets one registered app serve every variation of an analysis.

## App Definition and Wrapper

`app.json` declares the app's interface: one required Input Directory, the `COMMAND` and `EXTRA_MODULES` parameters, and default resources. `tapisjob_app.sh` is the wrapper SLURM runs; the template loads requested modules and executes `COMMAND` in the staged input directory. [Apps](../apps.md) documents every field of both, and the `container` template swaps the wrapper for one that runs any container image ([Custom Containers](../containers.md)).
