"""SimCenter application helpers for DesignSafe.

SimCenter research applications (quoFEM, EE-UQ, WE-UQ) run on DesignSafe
through Tapis apps such as ``simcenter-uq-stampede3``. These apps declare no
fileInputs or envVariables in their app definitions; the interface contract
lives inside the app's wrapper script:

- The staged input directory must be exposed to the wrapper as the
  ``inputDirectory`` environment variable (fileInput ``envKey``) with its
  contents unpacked into the job working directory (``targetPath: "*"``).
- The ``inputFile`` and ``driverFile`` environment variables name the
  workflow JSON (e.g. ``scInput.json``) and the per-sample driver script,
  both inside ``tmp.SimCenter/templatedir/`` of the input directory.
- The workflow JSON's ``remoteAppDir``/``remoteAppWorkingDir`` fields must
  point at the SimCenter backend installation on the execution system.
- The wrapper collects the UQ engine outputs (``dakota.out``,
  ``dakotaTab.out``, ``dakota.err``) into ``results.zip`` in the job archive.

This module encodes that contract as a dapi app profile (see
:mod:`dapi.profiles`), so it is applied automatically by the app-agnostic
API: ``ds.jobs.prepare_inputs`` patches the workflow JSON,
``ds.jobs.generate`` finalizes the job request, and
``SubmittedJob.get_results()`` parses the outputs.
"""

import io
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from tapipy.tapis import Tapis

from . import profiles
from .exceptions import FileOperationError
from .jobs import SubmittedJob

import logging

logger = logging.getLogger(__name__)

# The env variable name the wrapper script expects for the staged input dir.
INPUT_DIR_ENV_KEY = "inputDirectory"

# Archive name the SimCenter wrapper script unpacks natively on the exec
# system ("unzip tmpSimCenter.zip" is its first action in the input dir).
BUNDLE_NAME = "tmpSimCenter.zip"

# SimCenter backend installations per app id. These paths change when
# SimCenter redeploys the backend; update alongside a dapi release.
DEFAULT_BACKEND_DIRS: Dict[str, str] = {
    "simcenter-uq-stampede3": (
        "/work2/00477/tg457427/stampede3/SimCenterBackendApplications/v26.05.26"
    ),
}


def prepare_inputs(
    input_dir: str,
    input_filename: str = "scInput.json",
    backend_dir: Optional[str] = None,
    app_id: str = "simcenter-uq-stampede3",
    bundle: bool = True,
    staged_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Point a SimCenter workflow JSON at the backend and bundle the inputs.

    The SimCenter desktop applications write local paths into the workflow
    JSON (``remoteAppDir``/``remoteAppWorkingDir``). Before submission these
    must be rewritten to the backend installation on the execution system,
    which the app wrapper reads back with ``jq`` to locate the UQ engine.

    By default the prepared ``tmp.SimCenter/`` tree is then zipped into a
    single ``tmpSimCenter.zip`` inside a staging directory. The SimCenter
    wrapper unpacks this archive natively on the execution system, and
    staging one file instead of many avoids the Tapis transfers service's
    per-file overhead (which can add ~40s per file under tenant load).
    Stage the returned ``staged_dir``, not ``input_dir``, when bundling.

    Args:
        input_dir (str): Local path to the job input directory (the folder
            containing ``tmp.SimCenter/templatedir/``). Never modified
            beyond the workflow JSON patch.
        input_filename (str, optional): Workflow JSON filename inside
            ``tmp.SimCenter/templatedir/``. Defaults to "scInput.json".
        backend_dir (str, optional): SimCenter backend installation path on
            the execution system. If None, looked up from
            ``DEFAULT_BACKEND_DIRS`` by app_id.
        app_id (str, optional): Tapis app id used for the backend lookup.
            Defaults to "simcenter-uq-stampede3".
        bundle (bool, optional): Zip ``tmp.SimCenter/`` into
            ``tmpSimCenter.zip`` in a staging directory. Defaults to True.
            Pass False to stage the loose directory tree as before.
        staged_dir (str, optional): Where to place the bundle. Defaults to
            ``<input_dir>_staged`` next to the input directory; when that
            location is not writable (e.g. CommunityData or a published
            dataset), falls back to a local temporary directory — fast and
            always writable, but not visible to Tapis, so upload the bundle
            once with ``ds.files.upload(info["bundle"], ...)`` before
            submitting. For read-only sources the workflow patch is applied
            to the staged copy — the source is never written. An input
            directory that already contains ``tmpSimCenter.zip`` (and no
            ``tmp.SimCenter/`` tree) is reused rather than recompressed:
            only its workflow JSON entry is rewritten into the staged
            bundle.

    Returns:
        Dict[str, Any]: Summary of the prepared workflow with keys
            ``workflow_json`` (path), ``backend_dir``, ``uq_engine``,
            ``uq_type``, ``random_variables``, ``edps``, and ``staged_dir``
            (the directory to stage: the bundle directory when bundling,
            otherwise input_dir). When bundling, also ``bundle`` (zip path)
            and ``bundled_files`` (count).

    Raises:
        ValueError: If no backend directory is known for app_id and none given.
        FileNotFoundError: If the workflow JSON cannot be found.

    Example:
        >>> info = ds.jobs.prepare_inputs("simcenter-uq-stampede3", "./DS_input")
        >>> input_uri = ds.files.to_uri(info["staged_dir"])
    """
    if backend_dir is None:
        backend_dir = DEFAULT_BACKEND_DIRS.get(app_id)
        if backend_dir is None:
            raise ValueError(
                f"No known SimCenter backend directory for app '{app_id}'. "
                f"Pass backend_dir explicitly. "
                f"Known apps: {sorted(DEFAULT_BACKEND_DIRS)}"
            )

    workflow_relpath = f"tmp.SimCenter/templatedir/{input_filename}"
    workflow_path = os.path.join(
        input_dir, "tmp.SimCenter", "templatedir", input_filename
    )
    prebundled = os.path.join(input_dir, BUNDLE_NAME)

    if os.path.isfile(workflow_path):
        with open(workflow_path, "r") as f:
            workflow = json.load(f)
        source = "tree"
    elif os.path.isfile(prebundled):
        if not bundle:
            raise FileNotFoundError(
                f"'{input_dir}' contains only the pre-bundled {BUNDLE_NAME}; "
                f"staging it unbundled (bundle=False) is not supported. "
                f"Use bundle=True or extract the archive first."
            )
        with zipfile.ZipFile(prebundled) as zf:
            workflow = json.loads(zf.read(workflow_relpath))
        source = "zip"
        logger.debug(f"Reusing pre-bundled {BUNDLE_NAME} from {input_dir}")
    else:
        raise FileNotFoundError(
            f"SimCenter workflow JSON not found at '{workflow_path}' and no "
            f"{BUNDLE_NAME} present. Expected '{input_filename}' inside "
            f"'{input_dir}/tmp.SimCenter/templatedir/'."
        )

    workflow["remoteAppDir"] = backend_dir
    workflow["remoteAppWorkingDir"] = backend_dir
    workflow_text = json.dumps(workflow, indent=2)

    # Patch the source in place only when it is writable; CommunityData and
    # published datasets are read-only, so the patch travels with the staged
    # copy instead. Attempt the write rather than trusting os.access: on
    # FUSE/NFS-style mounts the mode bits can claim writable while every
    # actual write fails with EROFS.
    source_writable = False
    if source == "tree":
        tmp_path = workflow_path + ".dapi-tmp"
        try:
            with open(tmp_path, "w") as f:
                f.write(workflow_text)
            os.replace(tmp_path, workflow_path)
            source_writable = True
            logger.debug(f"Updated remoteAppDir in {workflow_path}")
        except OSError:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    if not source_writable:
        logger.debug(
            "Source is read-only; remoteAppDir patch applied to the staged copy"
        )

    uq = workflow.get("UQ", {})
    summary = {
        "workflow_json": workflow_path if source == "tree" else prebundled,
        "backend_dir": backend_dir,
        "uq_engine": uq.get("uqEngine"),
        "uq_type": uq.get("uqType"),
        "random_variables": [rv["name"] for rv in workflow.get("randomVariables", [])],
        "edps": [edp["name"] for edp in workflow.get("EDP", [])],
        "staged_dir": input_dir,
    }
    logger.debug(f"UQ engine: {summary['uq_engine']} ({summary['uq_type']})")
    logger.debug(f"Random variables: {summary['random_variables']}")
    logger.debug(f"EDPs: {summary['edps']}")

    if bundle:
        staged = staged_dir or _default_staged_dir(input_dir)
        if source == "zip":
            summary.update(
                _rewrite_bundle(
                    prebundled, staged, workflow_relpath, workflow_text, input_dir
                )
            )
        else:
            patched = None if source_writable else (workflow_relpath, workflow_text)
            summary.update(_bundle_inputs(input_dir, staged, patched))
    elif not source_writable:
        # Loose staging from a read-only source: stage a patched copy.
        # copytree preserves the source's read-only modes, so make the
        # copy writable before patching it.
        staged = staged_dir or _default_staged_dir(input_dir)
        shutil.copytree(input_dir, staged, dirs_exist_ok=True)
        for walk_root, _dirs, walk_files in os.walk(staged):
            os.chmod(walk_root, 0o755)
            for name in walk_files:
                os.chmod(os.path.join(walk_root, name), 0o644)
        staged_workflow = os.path.join(
            staged, "tmp.SimCenter", "templatedir", input_filename
        )
        with open(staged_workflow, "w") as f:
            f.write(workflow_text)
        summary["staged_dir"] = staged
        summary["workflow_json"] = staged_workflow
        logger.debug(f"Read-only input; patched copy staged at {staged}")
    return summary


def _default_staged_dir(input_dir: str) -> str:
    """``<input_dir>_staged`` when writable, else a temp-dir fallback.

    The fallback is a local temporary directory (fast local disk, always
    writable) rather than the MyData mount, which can be slow or flaky.
    A temp path is not visible to Tapis, so the bundle must be uploaded
    once before submission — see the hint printed below.
    """
    input_dir = os.path.abspath(input_dir.rstrip("/"))
    parent = os.path.dirname(input_dir)
    sibling = input_dir + "_staged"
    # Probe with a real write rather than os.access: FUSE/NFS-style mounts
    # can report writable mode bits while every write fails with EROFS.
    try:
        os.makedirs(sibling, exist_ok=True)
        probe = os.path.join(sibling, ".dapi-write-probe")
        with open(probe, "w") as f:
            f.write("")
        os.remove(probe)
        return sibling
    except OSError:
        pass
    base = os.path.basename(input_dir) + "_staged"
    staged = os.path.join(tempfile.mkdtemp(prefix="dapi-staging-"), base)
    logger.info(f"'{parent}' is not writable (e.g. CommunityData); staging to {staged}")
    logger.debug(
        "This is a local temporary directory. ds.jobs.prepare_inputs uploads "
        "it to /MyData/dapi-staging/ automatically; if calling "
        "dapi.simcenter.prepare_inputs directly, upload the bundle yourself "
        "with ds.files.upload before submitting."
    )
    return staged


def _bundle_inputs(
    input_dir: str,
    staged_dir: Optional[str],
    patched: Optional[tuple] = None,
) -> Dict[str, Any]:
    """Zip ``tmp.SimCenter/`` into ``tmpSimCenter.zip`` in a staging dir.

    The archive preserves the ``tmp.SimCenter/...`` layout the wrapper
    expects when it runs ``unzip tmpSimCenter.zip``. Any other top-level
    entries of input_dir are copied into the staging dir unchanged.

    When *patched* is given as ``(relpath, text)``, that archive entry is
    written from *text* instead of the on-disk file — used when the source
    is read-only and the workflow JSON could not be patched in place.
    """
    staged = staged_dir or input_dir.rstrip("/") + "_staged"
    os.makedirs(staged, exist_ok=True)

    patched_relpath, patched_text = patched if patched else (None, None)
    bundle_src = os.path.join(input_dir, "tmp.SimCenter")
    zip_path = os.path.join(staged, BUNDLE_NAME)
    bundled_files = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(bundle_src):
            for name in files:
                full_path = os.path.join(root, name)
                relpath = os.path.relpath(full_path, input_dir)
                if patched_relpath and relpath.replace(os.sep, "/") == patched_relpath:
                    zf.writestr(relpath, patched_text)
                else:
                    zf.write(full_path, relpath)
                bundled_files += 1

    # Preserve any sibling entries of tmp.SimCenter/ the app may expect
    # (but never a stale bundle, which would clobber the one just written).
    for entry in os.listdir(input_dir):
        if entry in ("tmp.SimCenter", BUNDLE_NAME):
            continue
        src = os.path.join(input_dir, entry)
        dst = os.path.join(staged, entry)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src) and os.path.abspath(src) != os.path.abspath(staged):
            shutil.copytree(src, dst, dirs_exist_ok=True)

    logger.info(f"Bundled {bundled_files} files into {zip_path}")
    logger.debug(f"Stage this directory: {staged}")
    return {"staged_dir": staged, "bundle": zip_path, "bundled_files": bundled_files}


def _rewrite_bundle(
    src_zip: str,
    staged_dir: str,
    workflow_relpath: str,
    workflow_text: str,
    input_dir: str,
) -> Dict[str, Any]:
    """Reuse a pre-bundled archive, rewriting only its workflow JSON entry.

    Avoids recompressing inputs that already ship as ``tmpSimCenter.zip``
    (e.g. from CommunityData or a previous staging run).
    """
    os.makedirs(staged_dir, exist_ok=True)
    zip_path = os.path.join(staged_dir, BUNDLE_NAME)
    bundled_files = 0
    with (
        zipfile.ZipFile(src_zip) as src,
        zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as dst,
    ):
        for item in src.infolist():
            if item.filename.rstrip("/") == workflow_relpath:
                dst.writestr(item.filename, workflow_text)
            else:
                dst.writestr(item, src.read(item.filename))
            bundled_files += 1

    for entry in os.listdir(input_dir):
        if entry in ("tmp.SimCenter", BUNDLE_NAME):
            continue
        src_path = os.path.join(input_dir, entry)
        dst_path = os.path.join(staged_dir, entry)
        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
        elif os.path.isdir(src_path) and os.path.abspath(src_path) != os.path.abspath(
            staged_dir
        ):
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

    logger.info(f"Rewrote workflow entry in reused bundle: {zip_path}")
    logger.debug(f"Stage this directory: {staged_dir}")
    return {
        "staged_dir": staged_dir,
        "bundle": zip_path,
        "bundled_files": bundled_files,
        "reused_bundle": True,
    }


def finalize_job_request(job_request: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the SimCenter wrapper contract to a generated job request.

    Adds what the app definition does not declare: the ``inputFile`` and
    ``driverFile`` environment variables (defaults ``scInput.json`` and
    ``driver``; values already present in the request — e.g. supplied via
    ``extra_env_vars`` — are kept), and the main file input exposed as the
    ``inputDirectory`` environment variable with its contents unpacked into
    the job working directory.

    Args:
        job_request (Dict[str, Any]): Job request dictionary from
            :func:`dapi.jobs.generate_job_request`.

    Returns:
        Dict[str, Any]: The adjusted job request.
    """
    param_set = job_request.setdefault("parameterSet", {})
    env_vars = param_set.setdefault("envVariables", [])
    present = {var.get("key") for var in env_vars}
    if "inputFile" not in present:
        env_vars.append({"key": "inputFile", "value": "scInput.json"})
    if "driverFile" not in present:
        env_vars.append({"key": "driverFile", "value": "driver"})

    # The wrapper script requires the staged input directory to be exposed
    # as $inputDirectory and unpacked into the job working directory.
    if job_request.get("fileInputs"):
        main_input = job_request["fileInputs"][0]
        main_input.setdefault("envKey", INPUT_DIR_ENV_KEY)
        main_input.setdefault("targetPath", "*")
    return job_request


@dataclass
class SimCenterResults:
    """UQ results extracted from a SimCenter job archive.

    Attributes:
        samples (pd.DataFrame): The sample table from ``dakotaTab.out``
            (one row per realization: random variables and EDPs).
        dakota_out (str): Raw text of ``dakota.out``.
        sobol_indices (pd.DataFrame, optional): Parsed Sobol sensitivity
            indices (rows: outputs, columns: main ``Sm(...)`` and total
            ``St(...)`` indices per random variable). None when
            ``dakota.out`` does not contain sensitivity results.
        archive_files (List[str]): Entry names inside ``results.zip``.
    """

    samples: pd.DataFrame
    dakota_out: str
    sobol_indices: Optional[pd.DataFrame] = None
    archive_files: List[str] = field(default_factory=list)


def parse_sensitivity_indices(dakota_out: str) -> Optional[pd.DataFrame]:
    """Parse Sobol sensitivity indices from SimCenterUQ ``dakota.out`` text.

    Expects the SimCenterUQ sensitivity block::

        * output names
        <one name per line>
        * Sm(RV1) Sm(RV2) ... St(RV1) St(RV2) ...
        <one row of indices per output>

    Args:
        dakota_out (str): Contents of ``dakota.out``.

    Returns:
        pd.DataFrame or None: Indices indexed by output name, or None if no
            sensitivity block is present.
    """
    lines = [line.strip() for line in dakota_out.splitlines()]

    outputs: List[str] = []
    if "* output names" in lines:
        for line in lines[lines.index("* output names") + 1 :]:
            if not line or line.startswith("*"):
                break
            outputs.append(line)

    header_idx = next(
        (i for i, line in enumerate(lines) if line.startswith("* Sm(")), None
    )
    if header_idx is None:
        return None

    columns = lines[header_idx].lstrip("*").split()
    rows: List[List[float]] = []
    for line in lines[header_idx + 1 :]:
        if not line or line.startswith("*"):
            break
        try:
            rows.append([float(value) for value in line.split()])
        except ValueError:
            break
    if not rows:
        return None

    indices = pd.DataFrame(rows, columns=columns)
    if len(outputs) == len(indices):
        indices.index = pd.Index(outputs, name="output")
    return indices


def get_results(
    tapis_client: Tapis,
    job: Union[str, SubmittedJob],
    results_filename: str = "results.zip",
) -> SimCenterResults:
    """Fetch and parse the UQ results of a finished SimCenter job.

    Downloads ``results.zip`` from the job archive in memory, reads the
    sample table from ``dakotaTab.out``, and parses Sobol sensitivity
    indices from ``dakota.out`` when present.

    Args:
        tapis_client (Tapis): Authenticated Tapis client instance.
        job (str or SubmittedJob): Job UUID or SubmittedJob object.
        results_filename (str, optional): Results archive filename in the
            job archive root. Defaults to "results.zip".

    Returns:
        SimCenterResults: Parsed results.

    Raises:
        FileOperationError: If the results archive or ``dakotaTab.out``
            cannot be retrieved.

    Example:
        >>> results = submitted_job.get_results()
        >>> results.samples.head()
        >>> results.sobol_indices
    """
    if isinstance(job, str):
        job = SubmittedJob(tapis_client, job)

    details = job.details
    if not details.archiveSystemId or not details.archiveSystemDir:
        raise FileOperationError(
            f"Job {job.uuid} archive system ID or directory not available."
        )

    archive_path = os.path.normpath(
        os.path.join(details.archiveSystemDir, results_filename)
    ).lstrip("/")
    logger.debug(
        f"Fetching '{results_filename}' from system "
        f"'{details.archiveSystemId}' path '{archive_path}'..."
    )
    content = tapis_client.files.getContents(
        systemId=details.archiveSystemId, path=archive_path, stream=True
    )
    if not isinstance(content, (bytes, bytearray)):
        raise FileOperationError(
            f"Unexpected content type {type(content)} fetching "
            f"'{results_filename}' for job {job.uuid}."
        )

    try:
        results_zip = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as e:
        raise FileOperationError(
            f"'{results_filename}' for job {job.uuid} is not a valid zip: {e}"
        ) from e

    names = results_zip.namelist()

    def _read(basename: str) -> Optional[bytes]:
        match = next((n for n in names if n.endswith(basename)), None)
        return results_zip.read(match) if match else None

    tab_bytes = _read("dakotaTab.out")
    if tab_bytes is None:
        raise FileOperationError(
            f"dakotaTab.out not found in '{results_filename}' for job "
            f"{job.uuid}. Archive entries: {names}"
        )
    samples = pd.read_csv(io.BytesIO(tab_bytes), sep=r"\s+")

    dakota_bytes = _read("dakota.out")
    dakota_out = dakota_bytes.decode(errors="replace") if dakota_bytes else ""
    sobol_indices = parse_sensitivity_indices(dakota_out) if dakota_out else None

    logger.debug(f"Parsed {len(samples)} samples from dakotaTab.out.")
    if sobol_indices is not None:
        logger.debug(f"Parsed Sobol indices for {len(sobol_indices)} outputs.")
    return SimCenterResults(
        samples=samples,
        dakota_out=dakota_out,
        sobol_indices=sobol_indices,
        archive_files=names,
    )


@profiles.register
class SimCenterProfile(profiles.AppProfile):
    """App profile for the SimCenter Tapis apps (``simcenter-*``).

    Dispatched automatically by ``ds.jobs.prepare_inputs``,
    ``ds.jobs.generate``, and ``SubmittedJob.get_results()``.
    """

    name = "simcenter"

    @classmethod
    def matches(cls, app_id: str) -> bool:
        return app_id.lower().startswith("simcenter-")

    @classmethod
    def prepare_inputs(
        cls, input_dir: str, app_id: str, **options: Any
    ) -> Dict[str, Any]:
        return prepare_inputs(input_dir, app_id=app_id, **options)

    @classmethod
    def finalize_job_request(cls, job_request: Dict[str, Any]) -> Dict[str, Any]:
        return finalize_job_request(job_request)

    @classmethod
    def parse_results(
        cls, tapis_client: Tapis, job: SubmittedJob, **options: Any
    ) -> SimCenterResults:
        return get_results(tapis_client, job, **options)
