"""
Dapi - A Python wrapper for interacting with DesignSafe resources via the Tapis API.
"""
from .client import DSClient

# Import exceptions
from .exceptions import (
    DapiException,
    AuthenticationError,
    FileOperationError,
    AppDiscoveryError,
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


__version__ = "1.1.0"

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
    "JobSubmissionError",
    "JobMonitorError",
]
