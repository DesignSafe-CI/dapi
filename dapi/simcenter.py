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
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from tapipy.tapis import Tapis

from . import profiles
from .exceptions import FileOperationError
from .jobs import SubmittedJob

# The env variable name the wrapper script expects for the staged input dir.
INPUT_DIR_ENV_KEY = "inputDirectory"

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
) -> Dict[str, Any]:
    """Point a SimCenter workflow JSON at the backend on the execution system.

    The SimCenter desktop applications write local paths into the workflow
    JSON (``remoteAppDir``/``remoteAppWorkingDir``). Before submission these
    must be rewritten to the backend installation on the execution system,
    which the app wrapper reads back with ``jq`` to locate the UQ engine.

    Args:
        input_dir (str): Local path to the job input directory (the folder
            containing ``tmp.SimCenter/templatedir/``).
        input_filename (str, optional): Workflow JSON filename inside
            ``tmp.SimCenter/templatedir/``. Defaults to "scInput.json".
        backend_dir (str, optional): SimCenter backend installation path on
            the execution system. If None, looked up from
            ``DEFAULT_BACKEND_DIRS`` by app_id.
        app_id (str, optional): Tapis app id used for the backend lookup.
            Defaults to "simcenter-uq-stampede3".

    Returns:
        Dict[str, Any]: Summary of the prepared workflow with keys
            ``workflow_json`` (path), ``backend_dir``, ``uq_engine``,
            ``uq_type``, ``random_variables``, and ``edps``.

    Raises:
        ValueError: If no backend directory is known for app_id and none given.
        FileNotFoundError: If the workflow JSON cannot be found.

    Example:
        >>> info = ds.jobs.prepare_inputs("simcenter-uq-stampede3", "./DS_input")
        >>> info["random_variables"]
        ['Dr', 'G0', 'hpo']
    """
    if backend_dir is None:
        backend_dir = DEFAULT_BACKEND_DIRS.get(app_id)
        if backend_dir is None:
            raise ValueError(
                f"No known SimCenter backend directory for app '{app_id}'. "
                f"Pass backend_dir explicitly. "
                f"Known apps: {sorted(DEFAULT_BACKEND_DIRS)}"
            )

    workflow_path = os.path.join(
        input_dir, "tmp.SimCenter", "templatedir", input_filename
    )
    if not os.path.isfile(workflow_path):
        raise FileNotFoundError(
            f"SimCenter workflow JSON not found at '{workflow_path}'. "
            f"Expected '{input_filename}' inside "
            f"'{input_dir}/tmp.SimCenter/templatedir/'."
        )

    with open(workflow_path, "r") as f:
        workflow = json.load(f)

    workflow["remoteAppDir"] = backend_dir
    workflow["remoteAppWorkingDir"] = backend_dir

    with open(workflow_path, "w") as f:
        json.dump(workflow, f, indent=2)

    uq = workflow.get("UQ", {})
    summary = {
        "workflow_json": workflow_path,
        "backend_dir": backend_dir,
        "uq_engine": uq.get("uqEngine"),
        "uq_type": uq.get("uqType"),
        "random_variables": [rv["name"] for rv in workflow.get("randomVariables", [])],
        "edps": [edp["name"] for edp in workflow.get("EDP", [])],
    }
    print(f"Updated remoteAppDir in {workflow_path}")
    print(f"UQ engine: {summary['uq_engine']} ({summary['uq_type']})")
    print(f"Random variables: {summary['random_variables']}")
    print(f"EDPs: {summary['edps']}")
    return summary


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
    print(
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

    print(f"Parsed {len(samples)} samples from dakotaTab.out.")
    if sobol_indices is not None:
        print(f"Parsed Sobol indices for {len(sobol_indices)} outputs.")
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
