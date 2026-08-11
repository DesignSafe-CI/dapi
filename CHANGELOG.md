# Changelog

## v0.6.1 (unreleased)

### Changed

- **Workflows execute through the Tapis Workflows service.** TACC authorized the service for the designsafe tenant, and `run()` now compiles the graph to a pipeline that the service executes server-side, submitting each job on the user's behalf when its dependencies finish; the notebook streams live per-task transitions and can close mid-campaign without stopping the run. The client-side coordinator is removed, and `run()`'s results no longer include a `uuid` field. Internally, dapi splices no-op function tasks between dependent jobs to absorb the engine's implicit output-passing, which strict-input apps reject, and pins job fields the engine would otherwise serialize as null. Both executed workflow notebooks ship with service runs in their outputs.
- **`ds.apps.scaffold` is renamed `ds.apps.new`.**

### Fixed

- **`parametric_sweep.submit` verifies a translated path before staging from it**: a local folder whose path merely contains a DesignSafe segment (a laptop's `~/MyData`) used to translate to a remote URI that pointed at nothing, and the job failed at input staging; the translated location is now checked and, when it does not exist while the local folder does, the sweep uploads the folder instead.
- **OpenSeesMP example repaired for current OpenSees**: the four `Profile*.tcl` inputs used the legacy inline TimeSeries form (`pattern Plain 10 "Path -dt ..."`), which current OpenSees rejects with `tag is not specified`, so the dynamic stage never ran and the acceleration recorders archived empty files; they now declare `timeSeries Path 100` explicitly. `OpenSeesMP-dapi.ipynb` runs from any machine (inputs auto-upload off JupyterHub, recorder outputs download before plotting), uses the standard allocation placeholder, and ships executed with the response-spectra figure.
- The OpenSees example links on the examples index point at the notebook's actual CommunityData path.

### Documentation and examples

- **`pylauncher_sweep.ipynb` sweeps something real**: the placeholder `alpha * beta` task is replaced by a one-parameter resonance study, each task integrates a 5%-damped oscillator at one forcing frequency, and the notebook reassembles the resonance curve from the archived results over the closed-form amplification it must match, executed end to end with a live sweep.
- New `examples/pylauncher/pylauncher_opensees_exercise.ipynb`: the OpenSees PyLauncher sweep posed as four TODOs with hints; the solution notebook now submits the sweep live (a local folder uploads automatically), monitors it, and plots the family of pushover curves from the archived recorders.
- New PM4Sand free-field exercise and solution (`examples/opensees/pm4sand/`), superseding the `jupyter-templates/opensees` notebook's pre-DSClient API and carrying over its interactive time-slider plots (`interactiveplot.py`, now taking a results directory): the University of Washington freeFieldJupyterPM4Sand example rebuilt on dapi, an executed solution and a four-TODO exercise, with the model's input motion declared in the modern `timeSeries` form (current OpenSees rejects the original inline form, leaving recorders empty) and plotting scripts that take the results folder as an argument.
- New `examples/custom-container-app.ipynb`: registers a container app with `ds.apps.new`/`deploy` and runs the GitHub-published site-response image on a compute node.
- New `examples/workflows/pi_fanout/DS_Pi_Fanout_Exercise.ipynb`: the fan-out/fan-in build posed as four TODOs with hints, paired with the executed solution.
- New `examples/workflows/pi_fanout/DS_Pi_Fanout_Workflow.ipynb`: three parallel Monte-Carlo jobs and a fan-in aggregator through the workflow service, self-contained and self-checking against pi, with a docs page (`docs/examples/pi-fanout.md`) on the examples index.
- Workflow and container documentation describes the service-side execution semantics.

## v0.6.0

### Fixed

- **Staging now guards against running out of disk space, twice**: a pre-write check fails fast with needed-vs-available and the `staged_dir=` override, and a mid-write `ENOSPC` (space can vanish during a long copy, and network mounts misreport free space) is caught, partial staging is removed, and the same clear guidance is raised. Temporary staging often lands on `/tmp`, whose capacity varies widely: containers allot a few GB, and Stampede3 node-local `/tmp` ranges from 90 GB (SKX) through 150 GB (SPR) and 200 GB (ICX) to 3.5 TB (GPU nodes).

### New features

- **`parametric_sweep.submit` accepts local-only input directories**: a sweep directory that is not a recognizable DesignSafe path (laptop, CI, temp dir) is uploaded once over the Tapis files API to `staging_destination` (default `/MyData/dapi-staging`) and submitted from there, matching the `prepare_inputs` behavior. The OpenSees ML notebook now runs end-to-end from any machine.
- **DAG workflows (`dapi.workflows`)**: compose Tapis jobs into an explicit directed acyclic graph. `Workflow`/`JobTask` with declared `depends_on` edges (referencing a task's output also declares the edge), validation that rejects cycles and unknown references, and `Workflow.visualize()` drawing the DAG with edges labeled by the output flowing across them. Each task gets a deterministic per-run archive directory, so `OutputRef("archive_uri", suffix=...)` resolves to a concrete path at compile time (one directory input per edge). `run()` coordinates the graph, submitting each job with the user's credentials when its dependencies finish, running independent branches in parallel, streaming live per-task status transitions, and blocking dependents of failed tasks; already-submitted jobs survive the coordinating process and re-attach via `ds.jobs.job(uuid)`. Verified end to end on Stampede3 with the OpenSees ML pipeline (75-run sweep feeding a training job).
- **`workflows.sequence_job()` packs sequential steps into one job on one node**: a generated fail-fast driver runs the steps in order inside a single `python-s3` allocation (one queue wait, shared working directory, no archive hop between steps).
- **Project permission check and repair (`ds.projects.permissions` / `ds.projects.fix_permissions`)**: command-line transfers into a My Projects area (scp, mv, rsync) leave files invisible to project members, either missing the named POSIX ACL entries entirely or carrying a clobbered ACL mask, and until now only administrators could fix it. `permissions()` reports every member's effective access on a path (Tapis grant, named ACL, mask, and the computed result); `fix_permissions()` repairs each broken file with the strongest strategy POSIX allows it: direct `setFacl` on service-owned files (covers members added after files existed), Tapis copy-recreate for files the service account can read, an owner tier through the `cloud.data` system (which executes as the calling user on the storage host, so researchers repair their own scp/cp/mv transfers from any machine, no shell or mount needed), and files owned by another member are reported with the exact `fix_permissions` call for that person to run. Every repair is verified against the storage before being reported as fixed. Healthy files are skipped; directory default ACLs are refreshed so future files inherit.

- **App scaffolding and deployment (`ds.apps.scaffold` / `ds.apps.deploy`)**: build a user-owned Tapis app in two calls. `scaffold()` writes `app.json` and `tapisjob_app.sh` from a template shipped with dapi (`ds.apps.templates()`); `deploy()` zips the wrapper, uploads it to MyData, and registers the version under the caller's ownership, updating in place on redeploy. The `container` template runs any image (`docker://` or staged `.sif`) via apptainer with `CONTAINER_IMAGE` and `COMMAND` as job parameters, one deployed app for every image a group builds.

### Documentation and examples

- New `examples/custom-app.ipynb`: develops a Tapis app end to end, scaffold from the `zip` template, edit the definition, `deploy()`, submit a job against it, and read the archived results, with a docs page (`docs/examples/custom-app.md`) on the examples index.
- New Workflows page in the user guide (`docs/workflows.md`): building a graph, passing outputs with `OutputRef`, live progress, failure semantics, parallel fan-in via the run-root pattern, archive filters with measured timings, and `sequence_job`.
- New Custom Containers page in the user guide (`docs/containers.md`): build on a TACC base image, deliver by registry pull (verified working from Stampede3 compute nodes) or by `docker save` tarball staged as job input, run via a `python-s3` driver, no Tapis registration anywhere; working demo in `examples/workflows/container-demo/`.
- New docs page for the OpenSees ML example (`docs/examples/opensees_ml.md`), added to the examples TOC and index; the notebook is enriched with a "learning task" section (data, features, target, model, split, and why log space turns the period equation into learnable exponents) and notebook-side plotting cells.
- The OpenSees ML notebook now ships fully executed, with a live Stampede3 sweep submitted from a laptop through the local-directory sweep upload above (job `f370f8ba`).
- New documentation for project file sharing: a permissions section on the Projects page (column meanings, repair strategies, prevention rules) and an example page wired to the examples index.
- New `examples/project-permissions.ipynb`: breaks, audits, and repairs project file sharing, creating a member-invisible file the way scp does, auditing per-member effective access, and repairing it with one `fix_permissions` call.

## v0.5.7

### Fixed

- **Read-only detection hardened for FUSE/NFS-style mounts** (the JupyterHub CommunityData mount reports writable mode bits while writes fail with `EROFS`): writability is now determined by attempting the operation, not by `os.access`. The workflow-JSON patch writes atomically (temp file + `os.replace`) so a failing mount can never truncate the source, and the staging-directory choice probes with a real write before using the sibling `_staged` location.

### New features

- **Leveled logging with a global verbosity control**: dapi's console output now goes through Python's standard `logging` (`dapi.*` loggers) instead of bare prints. The default `INFO` level reports concise milestones only (staging relocation, bundle built, upload done, job submitted, monitoring start); the step-by-step trace users saw before (path translations, per-file transfers, request construction, profile dispatch) moved to `DEBUG`. Control it with `dapi.set_log_level("DEBUG"|"INFO"|"WARNING"|"ERROR"|"QUIET")` or the `DAPI_LOG_LEVEL` environment variable. The handler writes to stdout so output renders normally in Jupyter (no red stderr boxes) and stays in order with prints and progress bars; applications can silence or reroute the `dapi` logger with standard `logging` configuration. Explicit display functions (`print_runtime_summary`, `interpret_status`, `apps.find(verbose=True)`) still print directly.

- **`ds.jobs.prepare_inputs` always returns a stageable `staged_dir`**: when local staging lands somewhere Tapis cannot see (the temp-dir fallback for read-only sources, or any local-machine path), the staged files are uploaded automatically over the Tapis files API — a remote upload; no MyData mount or Jupyter environment is assumed — and `staged_dir` is returned as the full `tapis://designsafe.storage.default/<username>/...` URL, which `ds.files.to_uri` passes through unchanged. The local copy is reported as `local_staged_dir`.
- New `staging_destination` parameter on `ds.jobs.prepare_inputs` (default `/MyData/dapi-staging`): any translatable DesignSafe path, e.g. a project path, receives the auto-upload instead.

### Documentation and examples

- quoFEM notebook and docs pass `bundle=True` explicitly (the default is unchanged; bundling only ever applies to SimCenter-profile apps whose wrapper unpacks natively — it is a no-op for MPM, OpenSees, and all other app ids).
- All four migrated example notebooks executed cell-by-cell (`python-s3-pi` end-to-end including a live Stampede3 job; `pylauncher_sweep` and `pylauncher_opensees` fully; `opensees_ml` client-side cells — submission requires the JupyterHub MyData mount).

## v0.5.6

### Fixed

- **`prepare_inputs` from read-only sources (CommunityData, published datasets)**: staging no longer writes into the source tree. The workflow-JSON backend patch is applied in place only when the source is writable; otherwise it travels inside the staged bundle (or a patched staged copy when `bundle=False`). The default `<input_dir>_staged` sibling falls back to a local temporary directory when the parent is not writable (fast local disk rather than the sometimes-flaky MyData mount); a printed hint shows the one `ds.files.upload` call needed to push the bundle before submitting.
- An input directory that already ships `tmpSimCenter.zip` (no extracted `tmp.SimCenter/` tree) is now reused instead of failing: only its workflow-JSON entry is rewritten into the staged bundle (`reused_bundle: true` in the summary).
- `parametric_sweep.generate` docstring now warns that token-style placeholders match anywhere a word appears — a single-letter key like `E` also rewrites the `--E` flag; use distinct names (`EMOD`) or `placeholder_style="braces"`.

### Documentation and examples

- All examples and docs migrated from the community `designsafe-agnostic-app` to the deployed general-purpose **`python-s3`** app (quickstart, apps table, PyLauncher pages and notebooks, OpenSees ML example). The ML example was verified end-to-end on Stampede3 (75-task PyLauncher sweep, temp job venv via `PIP_REQUIREMENTS`, TACC OpenSeesPy via pre-script, bundled inputs via `UNZIP_INPUTS`; recovered `T = 2π·√(M·L³/3EI)` with R² = 1.0).
- New Generic Python example (`examples/python/python-s3-pi.ipynb`, `docs/examples/python.md`): Monte Carlo π across 48 cores with `concurrent.futures`, verified on Stampede3, including the machine-readable `job-summary.json` run record.
- OpenSeesPy staging recipes handle the `opensees/3.8.0` module layout (`bin/opensees.so`; older modules shipped `bin/OpenSeesPy.so`).
- `pylauncher_opensees` example now stages the TACC OpenSeesPy explicitly (`EXTRA_MODULES` + `setup.sh` pre-script) — the old app injected it implicitly, `python-s3` deliberately does not.
- Updated ds-workflows links to `designsafe-ci.github.io/ds-workflows` and `monitor(timeout_minutes=...)` guidance (the default equals the job's `max_minutes`, which queue/staging waits can exhaust).

## v0.5.5

### New features

- **Job sharing** (`job.share()` / `job.shares`): share a job (READ) with explicit users and/or every member of a DesignSafe project. All grantees are validated **before** any grant is issued — usernames against the tenant's user profiles, projects against the DesignSafe projects API — and the job owner is excluded automatically.
  - `job.share(user_id="jdoe")`, `job.share(user_id=[...])`, `job.share(project_id="PRJ-1234")`
  - Grants cover `JOB_HISTORY`, `JOB_RESUBMIT_REQUEST`, `JOB_OUTPUT`, and `JOB_INPUT` by default (Tapis job shares are READ-only); restrict with `resources=[...]`
  - `job.shares` returns the current grants as a DataFrame
- **`ds.jobs.list(list_type=...)`**: `"MY_JOBS"` (default), `"SHARED_JOBS"` (jobs shared with you), or `"ALL_JOBS"`
- **`ds.projects.members("PRJ-1234")`**: list a project's users (username, name, email, role) — useful to preview who `job.share(project_id=...)` would reach

### Documentation

- New quoFEM example page (`docs/examples/quofem.md`): SimCenter app profile behavior, complete workflow (prepare → generate → submit → `get_results()` → Sobol plots), project archiving, and the input-bundling rationale with measured staging times; added to the docs sidebar and examples index
- New "Sharing Jobs" section in `docs/jobs.md`: user and project shares, grantee-side discovery, sharing vs. project archiving
- New `examples/job-sharing.ipynb`: share an existing job with a user or project team and inspect grants; grantee-side walkthrough — discover via `SHARED_JOBS`, open the shared job, and access its outputs through the share-aware Tapis job-output endpoints
- quoFEM example notebook installs the latest dapi (`--user --upgrade`, unpinned) instead of pinning a version; `--user` is required on DesignSafe Jupyter where the system site-packages is not writable

### Infrastructure

- CI: pinned `ruff>=0.16,<0.17` and made the lint rule selection explicit (`E4`, `E7`, `E9`, `F`) so ruff upgrades cannot silently change what CI enforces; reformatted markdown code blocks for ruff 0.16, which now formats them

### Notes

- Revoking shares is intentionally not included: the Tapis share-deletion endpoint (`deleteJobShare`) currently fails with a server-side Security Kernel error in the designsafe tenant (reported to TACC). `job.unshare()` will be added once the service is fixed.
- Job shares grant access through the Tapis **jobs** service. dapi's output methods (`list_outputs`, `get_output_content`, `get_results`) currently read via the **files** service, which does not see job shares — so grantees should access outputs of jobs archived to MyData via the DesignSafe portal for now, or the owner should archive to a shared project. Routing dapi's output methods through the share-aware jobs-output endpoints is planned.

## v0.5.4

### New features

- **Input bundling for SimCenter apps** (`ds.jobs.prepare_inputs`): the Tapis transfers service pays a fixed per-file scheduling cost (measured ~40s/file under tenant load), so staging many small input files dominates job wall time. For `simcenter-*` apps, `prepare_inputs` now zips the prepared `tmp.SimCenter/` tree into a single `tmpSimCenter.zip` — which the app wrapper unpacks natively on the execution system — inside a staging directory (`<input_dir>_staged`). Staging transfers ~2 objects instead of one per file.
  - Default **on** for SimCenter apps (matching what quoFEM desktop submits); pass `bundle=False` to stage the loose tree as before. Apps without a profile are unaffected.
  - Every `prepare_inputs` summary now includes `staged_dir` — the directory to pass to `ds.files.to_uri()`; the original input directory is never modified beyond the workflow-JSON patch.

## v0.5.3

### New features

- **App profiles** (`dapi.profiles`): some Tapis apps (notably the SimCenter apps — quoFEM, EE-UQ, WE-UQ backends such as `simcenter-uq-stampede3`) declare no fileInputs or envVariables in their app definitions; their contract lives in the app wrapper script. Profiles encode such contracts and are dispatched automatically by app id, so the public API stays app-agnostic:
  - `ds.jobs.generate()` now finalizes requests through the matching profile. For `simcenter-*` apps this adds the `inputFile`/`driverFile` env variables and exposes the input directory as the `inputDirectory` env variable (`envKey`) with contents unpacked into the job working directory (`targetPath "*"`) — without this the wrapper exits immediately with code 1
  - `ds.jobs.prepare_inputs(app_id, input_dir)`: new lifecycle step for local input preparation before staging; a no-op for apps that need none. For SimCenter apps it points the workflow JSON (`scInput.json`) at the backend installation on the execution system (`remoteAppDir`/`remoteAppWorkingDir`) and reports the UQ engine, random variables, and EDPs
  - `job.get_results()` on `SubmittedJob`: fetches and parses results via the job's app profile. For SimCenter jobs, reads `results.zip` from the archive in memory and returns a `SimCenterResults` with the `dakotaTab.out` sample table as a DataFrame and parsed Sobol sensitivity indices
  - Known SimCenter backend installations registered in `dapi.simcenter.DEFAULT_BACKEND_DIRS` (overridable via `backend_dir=`)

### Bug fixes

- `ds.files.download()` no longer crashes on binary files: tapipy returns raw bytes for non-JSON responses, which broke the streaming code path (`'bytes' object has no attribute 'iter_content'`)

## v0.5.2

### New features

- **Publications module** (`ds.publications`): search and access published datasets on DesignSafe
  - `ds.publications.list()`: DataFrame of all published datasets (1,500+)
  - `ds.publications.search()`: filter by `query`, `pi`, `keyword`, `publication_type` (AND logic)
  - `ds.publications.get("PRJ-XXXX")`: full metadata with DOIs, description, keywords
  - `ds.publications.files("PRJ-XXXX")`: list files in a published dataset
- **Systems listing** (`ds.systems.list()`): DataFrame of available HPC and storage systems
  - Filter by category: `"hpc"`, `"storage"`, `"all"`
  - Shows TMS credential status for HPC systems
  - Filters out internal, duplicate, and project-specific systems
- **`ds.systems.queues()`** now returns a clean DataFrame instead of printing verbose output

### Documentation

- New `docs/publications.md` with search filter reference
- Updated `docs/systems.md` with `list()` and DataFrame queues
- Added `examples/publications.ipynb` and `examples/systems.ipynb`
- Updated examples sidebar with all new notebooks

## v0.5.1

### New features

- **Projects module** (`ds.projects`): list, inspect, and access files in DesignSafe projects
  - `ds.projects.list()`: returns a DataFrame of all projects you have access to
  - `ds.projects.get("PRJ-XXXX")`: get full project metadata (title, PI, DOIs, keywords, team, systemId)
  - `ds.projects.files("PRJ-XXXX")`: list files in a project as a DataFrame
  - PRJ number to Tapis UUID resolution via DesignSafe portal API (`/api/projects/v2/`)
- **NHERI-Published and NEES storage support**: `ds.files.to_uri()` and `ds.files.to_path()` now handle `/NHERI-Published/` (`designsafe.storage.published`) and `/NEES/` (`nees.public`) paths
- **`ds.jobs.job(uuid)`**: get a `SubmittedJob` object for an existing job by UUID

### Fixes

- Fix `ds.files.list()` failing on root paths (e.g., `tapis://designsafe.storage.community/`) where the parsed path was empty
- Fix project PRJ resolution: replaced broken Tapis system description search with DesignSafe portal API lookup

### Documentation

- New `docs/projects.md` with full API reference and "How it works" section
- Updated `docs/files.md` with NHERI-Published and NEES path formats
- Added development section to `docs/installation.md` (dev branch install, editable install, pre-commit hook, running tests)

### Developer experience

- Added `scripts/pre-commit` hook: auto-formats with `ruff format` and blocks commits failing `ruff check`
- Added `examples/files.ipynb` and `examples/projects.ipynb`

## v0.5.0

### New features

- **PyLauncher parameter sweeps** (`ds.jobs.parametric_sweep`): generate and submit parameter sweeps
  - `ds.jobs.parametric_sweep.generate()`: generate `runsList.txt` and `call_pylauncher.py`, or preview as DataFrame
  - `ds.jobs.parametric_sweep.submit()`: submit sweep jobs to TACC
- **`ds.jobs.list()`**: list jobs with optional filtering by app_id and status, returns DataFrame by default
- **Auto-TMS credentials**: `DSClient()` automatically sets up TMS credentials on TACC execution systems at init
- **Ruff**: switched from black to ruff for formatting and linting

### API changes

- Renamed methods for brevity: `ds.jobs.generate()` (was `generate_job_info`), `ds.jobs.submit()` (was `submit_job`)
- `ds.jobs.list()` supports `output="df"` (default), `"list"`, or `"raw"`
- Added `ds.files.to_uri()` and `ds.files.to_path()` for path translation

### Infrastructure

- Migrated from Poetry to uv + hatchling
- Migrated docs from mkdocs to Jupyter Book v2 (MyST)
- Added TMS credential management (`ds.systems.establish_credentials()`, `check_credentials()`, `revoke_credentials()`)
