"""
Dapi - A Python wrapper for interacting with DesignSafe resources via the Tapis API.
"""
# Import the renamed client class
from .client import DSClient
from .exceptions import DapiException, FileOperationError, JobSubmissionError, JobMonitorError
# Import JobDefinition here too for easier access like dapi.JobDefinition
from .jobs import JobDefinition

__version__ = "1.1.0" # Example version

__all__ = [
    "DSClient", # Export the renamed class
    "JobDefinition", # Export JobDefinition
    "DapiException",
    "FileOperationError",
    "JobSubmissionError",
    "JobMonitorError",
]