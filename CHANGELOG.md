# Changelog

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
