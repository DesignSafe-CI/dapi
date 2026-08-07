# Changelog

## v0.5.5

### New features

- **Job sharing** (`job.share()` / `job.unshare()` / `job.shares`): share a job (READ) with explicit users and/or every member of a DesignSafe project. All grantees are validated **before** any grant is issued — usernames against the tenant's user profiles, projects against the DesignSafe projects API — and the job owner is excluded automatically.
  - `job.share(user_id="parduino")`, `job.share(user_id=[...])`, `job.share(project_id="PRJ-1234")`
  - Grants cover `JOB_HISTORY`, `JOB_RESUBMIT_REQUEST`, `JOB_OUTPUT`, and `JOB_INPUT` by default (Tapis job shares are READ-only); restrict with `resources=[...]`
  - `job.shares` returns the current grants as a DataFrame; `job.unshare(...)` revokes
- **`ds.jobs.list(list_type=...)`**: `"MY_JOBS"` (default), `"SHARED_JOBS"` (jobs shared with you), or `"ALL_JOBS"`
- **`ds.projects.members("PRJ-1234")`**: list a project's users (username, name, email, role) — useful to preview who `job.share(project_id=...)` would reach

### Documentation

- New quoFEM example page (`docs/examples/quofem.md`): SimCenter app profile behavior, complete workflow (prepare → generate → submit → `get_results()` → Sobol plots), project archiving, and the input-bundling rationale with measured staging times; added to the docs sidebar and examples index
- New "Sharing Jobs" section in `docs/jobs.md`: user and project shares, grantee-side discovery, sharing vs. project archiving
- New `examples/job-sharing.ipynb`: share an existing job with a user or project team, inspect and revoke grants; grantee-side walkthrough — discover via `SHARED_JOBS`, open the shared job, and access its outputs through the share-aware Tapis job-output endpoints
- quoFEM example notebook installs the latest dapi (`--upgrade`, unpinned) instead of pinning a version

### Infrastructure

- CI: pinned `ruff>=0.16,<0.17` and made the lint rule selection explicit (`E4`, `E7`, `E9`, `F`) so ruff upgrades cannot silently change what CI enforces; reformatted markdown code blocks for ruff 0.16, which now formats them

### Notes

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
