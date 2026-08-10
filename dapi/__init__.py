"""Python client for submitting, monitoring, and managing TAPIS v3 jobs on DesignSafe.

Also provides access to DesignSafe research databases (NGL, Earthquake Recovery, VP)
and file operations (path translation, upload, download).

Classes:
    DSClient: Entry point. Provides access to jobs, files, apps, systems, and databases.
    SubmittedJob: Returned by ``DSClient.jobs.submit()``. Used to monitor and inspect a job.

Example::

    from dapi import DSClient

    client = DSClient()
    job_request = client.jobs.generate(
        app_id="matlab-r2023a",
        input_dir_uri="/MyData/analysis/input/",
        script_filename="run_analysis.m",
    )
    job = client.jobs.submit(job_request)
    final_status = job.monitor()

    df = client.db.ngl.read_sql("SELECT * FROM SITE LIMIT 10")
"""

from .client import DSClient

# Import exceptions
from .exceptions import (
    DapiException,
    AuthenticationError,
    FileOperationError,
    AppDiscoveryError,
    SystemInfoError,
    CredentialError,
    JobSubmissionError,
    JobMonitorError,
)

# Import key classes/functions from simcenter module
from .simcenter import SimCenterResults

# Import key classes/functions from jobs module
from .jobs import (
    SubmittedJob,
    interpret_job_status,
    # Import status constants for user access if needed
    STATUS_TIMEOUT,
    STATUS_INTERRUPTED,
    STATUS_MONITOR_ERROR,
    STATUS_UNKNOWN,
    TAPIS_TERMINAL_STATES,
)

import logging as _logging
import os as _os
import sys as _sys

_logger = _logging.getLogger("dapi")
_logger.addHandler(_logging.NullHandler())
_handler: _logging.Handler | None = None


def set_log_level(level="INFO") -> None:
    """Set dapi's console log verbosity.

    Args:
        level: ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, ``"ERROR"``, or
            ``"QUIET"`` (silence everything below CRITICAL). An ``int``
            logging level is also accepted.

    At ``INFO`` (the default) dapi reports concise milestones — staging
    relocations, uploads, job submission, monitoring start. ``DEBUG`` adds
    the detailed step-by-step trace (path translations, per-file transfers,
    request construction). The default can also be set with the
    ``DAPI_LOG_LEVEL`` environment variable before import.

    The handler writes to stdout (not stderr) so output renders normally
    in Jupyter notebooks and stays in order with prints and progress bars.

    Example:
        >>> import dapi
        >>> dapi.set_log_level("DEBUG")  # full trace
        >>> dapi.set_log_level("QUIET")  # silence dapi
    """
    global _handler
    if isinstance(level, str):
        name = level.upper()
        numeric = _logging.CRITICAL if name == "QUIET" else getattr(_logging, name)
    else:
        numeric = level
    if _handler is None:
        _handler = _logging.StreamHandler(_sys.stdout)
        _logger.addHandler(_handler)
    fmt = (
        "%(name)s %(levelname)s: %(message)s"
        if numeric <= _logging.DEBUG
        else "%(message)s"
    )
    _handler.setFormatter(_logging.Formatter(fmt))
    _logger.setLevel(numeric)
    _handler.setLevel(numeric)


set_log_level(_os.environ.get("DAPI_LOG_LEVEL", "INFO"))


__version__ = "0.6.0"

__all__ = [
    "DSClient",
    "SubmittedJob",
    "SimCenterResults",
    "set_log_level",
    "interpret_job_status",
    # Export status constants
    "STATUS_TIMEOUT",
    "STATUS_INTERRUPTED",
    "STATUS_MONITOR_ERROR",
    "STATUS_UNKNOWN",
    "TAPIS_TERMINAL_STATES",
    # Export exceptions
    "DapiException",
    "AuthenticationError",
    "FileOperationError",
    "AppDiscoveryError",
    "SystemInfoError",
    "CredentialError",
    "JobSubmissionError",
    "JobMonitorError",
]
