"""Dapi - A Python wrapper for interacting with DesignSafe resources via the Tapis API.

This package provides a high-level, user-friendly interface for working with DesignSafe 
resources through the Tapis V3 API. It simplifies complex operations and provides 
organized access to different service areas including authentication, file operations,
job submission and monitoring, application discovery, system information, and database access.

Key Features:
    - Simplified authentication with credential resolution hierarchy
    - DesignSafe path translation (MyData, projects, etc.) to Tapis URIs  
    - High-level job submission with automatic app parameter mapping
    - Job monitoring with progress bars and status interpretation
    - File upload/download with automatic directory creation
    - Application discovery and detailed retrieval
    - System queue information and resource limits
    - Database access for DesignSafe research databases
    - Comprehensive error handling with descriptive exceptions

Main Components:
    DSClient: Main client class providing organized access to all services
    SubmittedJob: Class for managing and monitoring submitted Tapis jobs
    Exception classes: Specific exceptions for different error types

Example:
    Basic usage with automatic authentication:
    
    >>> from dapi import DSClient
    >>> client = DSClient()
    Enter DesignSafe Username: myuser
    Enter DesignSafe Password: [hidden]
    Authentication successful.
    
    >>> # File operations
    >>> client.files.upload("/local/file.txt", "/MyData/uploads/file.txt")
    >>> files = client.files.list("/MyData/uploads/")
    
    >>> # Job submission and monitoring
    >>> job_request = client.jobs.generate_request(
    ...     app_id="matlab-r2023a",
    ...     input_dir_uri="/MyData/analysis/input/",
    ...     script_filename="run_analysis.m"
    ... )
    >>> job = client.jobs.submit_request(job_request)
    >>> final_status = job.monitor()
    
    >>> # Database access
    >>> df = client.db.ngl.read_sql("SELECT * FROM earthquake_data LIMIT 10")

Attributes:
    __version__ (str): The version number of the dapi package.
    DSClient: Main client class for DesignSafe API interactions.
    SubmittedJob: Class for managing submitted Tapis jobs.
    Exception classes: Custom exceptions for specific error conditions.
"""
from .client import DSClient

# Import exceptions
from .exceptions import (
    DapiException,
    AuthenticationError,
    FileOperationError,
    AppDiscoveryError,
    SystemInfoError,
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


def _get_version():
    """Read version from pyproject.toml"""
    import tomllib
    from pathlib import Path

    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        return pyproject["tool"]["poetry"]["version"]
    except (FileNotFoundError, KeyError, ImportError):
        # Fallback version if pyproject.toml can't be read
        return "unknown"


__version__ = _get_version()

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
    "SystemInfoError" "JobSubmissionError",
    "JobMonitorError",
]
