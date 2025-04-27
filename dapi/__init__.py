"""
Dapi - A Python wrapper for interacting with DesignSafe resources via the Tapis API.
"""
from .client import DSClient

# Import exceptions from the exceptions module
# Make sure ALL exceptions you want to expose are listed here
from .exceptions import (
    DapiException,
    AuthenticationError,
    FileOperationError,
    AppDiscoveryError,
    JobSubmissionError,
    JobMonitorError,
)


__version__ = "1.0.0"

# Define what gets imported with 'from dapi import *'
# Also helps linters and clarifies the public API
__all__ = [
    "DSClient",
    # List ALL exported exceptions here
    "DapiException",
    "AuthenticationError",
    "FileOperationError",
    "AppDiscoveryError",
    "JobSubmissionError",
    "JobMonitorError",
]
