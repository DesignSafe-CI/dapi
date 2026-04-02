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

__version__ = "0.5.2"

__all__ = [
    "DSClient",
    "SubmittedJob",
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
