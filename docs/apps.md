# Apps

Tapis apps are the executables jobs run against. Find the apps DesignSafe ships, or register your own.

## Find apps

Search by name. Use an empty string to list everything.

```python
from dapi import DSClient

ds = DSClient()

ds.apps.find("matlab")
# Found 3 matching apps:
# - matlab-r2023a (Version: 1.0, Owner: designsafe)
# - matlab-parallel (Version: 2.1, Owner: tacc)
# - matlab-desktop (Version: 1.5, Owner: designsafe)

ds.apps.find("opensees")
ds.apps.find("mpm")

# All apps (quiet mode)
all_apps = ds.apps.find("", verbose=False)
len(all_apps)
```

The search matches partially, so `"matlab"` finds any app with "matlab" in the ID.

You can filter by ownership:

```python
# Only apps you own
ds.apps.find("", list_type="OWNED")

# Only shared/public apps
ds.apps.find("", list_type="SHARED_PUBLIC")
```

`list_type` accepts `"ALL"` (the default), `"OWNED"`, `"SHARED_PUBLIC"`, `"SHARED_DIRECT"`, `"READ_PERM"`, and `"MINE"`.

## App details

```python
app = ds.apps.get_details("mpm-s3")
# App Details:
#   ID: mpm-s3
#   Version: 0.1.0
#   Owner: designsafe
#   Execution System: frontera
#   Description: ...
```

Access job configuration:

```python
attrs = app.jobAttributes
print(attrs.execSystemId)  # frontera
print(attrs.maxMinutes)  # 2880
print(attrs.coresPerNode)  # 56
print(attrs.execSystemLogicalQueue)  # normal
```

Request a specific version:

```python
app = ds.apps.get_details("mpm-s3", app_version="0.1.0")
```

Returns `None` if the app doesn't exist (instead of raising).

## Common apps

| App ID | Description |
|---|---|
| `python-s3` | General-purpose Python or any binary, PyLauncher, pre/post scripts |
| `matlab-r2023a` | MATLAB |
| `opensees-express` | OpenSees (serial) |
| `opensees-mp-s3` | OpenSees (MPI parallel) |
| `mpm-s3` | Material Point Method |
| `adcirc-v55` | ADCIRC coastal modeling |
| `ls-dyna` | LS-DYNA finite element |

## Build your own app

Registering an app requires no administrator. You own the record, the wrapper assets live in your own MyData, and only you see the app until you share it.

**Step 1. Scaffold.** Pick a template (decision table below) and write the two app files.

```python
ds.apps.scaffold("my-opensees", template="zip")  # writes ./my-opensees/
```

**Step 2. Edit `app.json`.** Set the target system, queue, default resources, and one `envVariables` entry per parameter your app takes. [App Definition - app.json](#app-json-fields) below covers every field and whether to touch it.

**Step 3. Edit `tapisjob_app.sh`.** The wrapper is a commented skeleton that ends by running `COMMAND` in the staged input directory. Replace that final section with your launch logic when one command is not enough, e.g. module loads plus an `ibrun` MPI launch plus a post-processing step.

**Step 4. Deploy.** Zips the wrapper, uploads it to MyData, and registers the app version under your ownership.

```python
ds.apps.deploy("./my-opensees")
```

**Step 5. Submit a job against it.** Your `envVariables` arrive as job parameters (full example below the tables).

**Step 6. Iterate and share.** Edit either file and `deploy()` again; the same version updates in place. Bump `version` in `app.json` when collaborators depend on the old one, and share with `ds.tapis.apps.shareApp`.

`ds.apps.templates()` lists the shipped templates. Choosing between them is choosing where the software stack lives.

| | `container` template | `zip` template |
|---|---|---|
| The deployed app runs | any container image via apptainer | any shell command on the compute node |
| Software stack comes from | the image, baked in at build time | TACC modules plus whatever the wrapper sets up |
| Job parameters | `CONTAINER_IMAGE`, `COMMAND` | `COMMAND`, `EXTRA_MODULES` |
| Change the software | rebuild and push the image; the app never changes | edit the wrapper, run `deploy()` again |
| Reproducibility | the image tag or digest pins the whole stack | module versions can move underneath you |
| Startup overhead | image pull and SIF conversion at job start | none |
| Best for | tools with their own stack (gmprocess), code built off-site, exact repeatability | codes that live on TACC modules (OpenSees), binaries in `$WORK`, MPI launches via `ibrun` |

Both templates stage one input directory, run inside it so outputs archive, and take a `COMMAND`. For building and delivering the images the `container` template runs, see [Custom Containers](containers.md).

(app-json-fields)=
### App Definition - app.json

`app.json` is the app definition Tapis registers, and every job against the app starts from its values. This is the `zip` template's definition in full.

```json
{
  "id": "my-app",
  "version": "0.1.0",
  "description": "Custom app: runs COMMAND on the staged input directory...",
  "runtime": "ZIP",
  "containerImage": "__SET_BY_DEPLOY__",
  "jobType": "BATCH",
  "strictFileInputs": true,
  "jobAttributes": {
    "execSystemId": "stampede3",
    "execSystemLogicalQueue": "skx",
    "execSystemExecDir": "${JobWorkingDir}",
    "execSystemInputDir": "${JobWorkingDir}",
    "execSystemOutputDir": "${JobWorkingDir}",
    "archiveSystemId": "designsafe.storage.default",
    "archiveSystemDir": "${JobOwner}/tapis-jobs-archive/${JobCreateDate}/${JobName}-${JobUUID}",
    "archiveOnAppError": true,
    "isMpi": false,
    "nodeCount": 1,
    "coresPerNode": 48,
    "maxMinutes": 60,
    "fileInputs": [
      {
        "name": "Input Directory",
        "inputMode": "REQUIRED",
        "targetPath": "inputDirectory"
      }
    ],
    "parameterSet": {
      "schedulerOptions": [
        {"name": "TACC Allocation", "inputMode": "REQUIRED", "arg": "-A ${allocation}"}
      ],
      "envVariables": [
        {"key": "COMMAND", "inputMode": "REQUIRED",
         "description": "Shell command executed in the staged input directory."},
        {"key": "EXTRA_MODULES", "value": "", "inputMode": "INCLUDE_ON_DEMAND",
         "description": "Comma-separated TACC modules to load first."}
      ],
      "archiveFilter": {"includeLaunchFiles": true}
    }
  }
}
```

| Field | Meaning | Edit it? |
|---|---|---|
| `id`, `version` | The app's identity. Jobs reference both. | Set by `scaffold()`. Bump `version` when a change should not overwrite what collaborators use; same version redeploys in place. |
| `description` | Shown by `ds.apps.find()` and the portal. | Yes, describe your app. |
| `runtime: ZIP` | The app's executable is a zip of scripts that Tapis unpacks on the node. | No. `deploy()` builds the zip for you. |
| `containerImage` | For ZIP apps, the path of that zip on storage. | No. `deploy()` overwrites it with the uploaded location. |
| `jobType: BATCH` | Runs through SLURM (the alternative, FORK, is for VMs). | No, for HPC apps. |
| `strictFileInputs` | Jobs may only supply the file inputs the app defines. | Keep `true` unless jobs must attach arbitrary extra inputs. |
| `execSystemId`, `execSystemLogicalQueue` | Target system and default queue. | Yes, e.g. `frontera`, or queue `skx-dev` for testing. Jobs can override the queue. |
| `execSystemExecDir/InputDir/OutputDir` | Where the wrapper runs, inputs stage, and outputs are collected, all pinned to the job working directory. | No. Unset, Tapis defaults them to a `jobs/<uuid>` subdirectory and wrapper paths break. |
| `archiveSystemId`, `archiveSystemDir` | Where results are copied when the job ends. The `${JobOwner}` and `${Job*}` macros expand per job. | Rarely. Jobs can override, e.g. to archive into a project. Avoid `HOST_EVAL($HOME)` on `designsafe.storage.default`; it resolves outside your writable area. |
| `archiveOnAppError` | Archive outputs even when the job fails, so logs survive for debugging. | Keep `true`. |
| `isMpi` | Whether Tapis itself prefixes the wrapper with an MPI launch. | Keep `false` and call `ibrun` inside the wrapper instead, the pattern production apps use. |
| `nodeCount`, `coresPerNode`, `maxMinutes` | Default resources; every job can override. | Yes, set sensible defaults for your code. |
| `fileInputs` | The staged inputs. `targetPath` is the folder name inside the job. | Add more entries only if the app genuinely takes several distinct inputs; one directory covers most apps. |
| `schedulerOptions` | Extra SLURM arguments. The allocation entry is required on TACC. | Leave the allocation entry; add e.g. reservations if needed. |
| `envVariables` | The app's parameters, delivered to the wrapper as environment variables. | Yes, this is your app's interface. One entry per knob the wrapper reads; `REQUIRED` forces jobs to set it, `INCLUDE_ON_DEMAND` makes it optional. |
| `archiveFilter` | Which files archive. `includes`/`excludes` glob patterns trim multi-gigabyte archives to results. | Yes for workflow nodes; see [Workflows](workflows.md#archive-filters). |

### Wrapper - tapisjob_app.sh

`tapisjob_app.sh` is the script SLURM runs on the compute node. Your `envVariables` arrive as ordinary environment variables (`$COMMAND`, `$EXTRA_MODULES`), and Tapis sets path variables the wrapper builds on.

| Variable | Value |
|---|---|
| `${_tapisJobWorkingDir}` | The job's working directory on scratch |
| `${_tapisExecSystemInputDir}` | Where file inputs staged; the Input Directory is at `.../inputDirectory` |
| `${_tapisExecSystemOutputDir}` | What gets archived (pinned to the working directory in the templates) |
| `${_tapisJobUUID}`, `${_tapisJobOwner}` | Job identity, useful in logs |

Two hard-won rules are already encoded in the templates. Load modules with `set -u` relaxed (`set +u; module load x; set -u`), because Lmod completion hooks reference unset variables. And write outputs into the input directory or working directory, because only what is there when the job ends survives to the archive.

A job against the deployed app supplies each `envVariables` entry as an ordinary parameter.

```python
job = {
    "name": "my-analysis",
    "appId": "my-opensees",
    "appVersion": "0.1.0",
    "execSystemLogicalQueue": "skx-dev",
    "nodeCount": 1,
    "coresPerNode": 1,
    "maxMinutes": 30,
    "fileInputs": [{"name": "Input Directory", "sourceUrl": inputs_uri}],
    "parameterSet": {
        "envVariables": [
            {"key": "COMMAND", "value": "python3 run_analysis.py model.json"},
            {"key": "EXTRA_MODULES", "value": "opensees"},
        ],
        "schedulerOptions": [{"name": "TACC Allocation", "arg": "-A MyAllocation"}],
    },
}
submitted = ds.jobs.submit(job)
```
