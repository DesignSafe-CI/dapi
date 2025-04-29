"""Custom exceptions for the Dapi library."""


class DapiException(Exception):
    """Base exception for dapi errors."""

    pass


class AuthenticationError(DapiException):
    """Error during authentication."""

    pass


class FileOperationError(DapiException):
    """Error during file operations (upload, download, list, path translation)."""

    pass


class AppDiscoveryError(DapiException):
    """Error finding or getting details about Tapis applications."""

    pass

class SystemInfoError(DapiException):
    """Error retrieving information about Tapis systems or queues."""
    pass


class JobSubmissionError(DapiException):
    """Error during job definition validation or submission."""

    def __init__(self, message, request=None, response=None):
        super().__init__(message)
        self.request = request
        self.response = response

    def __str__(self):
        msg = super().__str__()
        if self.request:
            msg += f"\nRequest URL: {self.request.url}"
            msg += f"\nRequest Method: {self.request.method}"
            # Potentially add headers/body if safe and useful
        if self.response:
            msg += f"\nResponse Status: {self.response.status_code}"
            try:
                msg += f"\nResponse Body: {self.response.text}"  # Use text to avoid JSON errors
            except Exception:
                msg += "\nResponse Body: <Could not decode>"
        return msg


class JobMonitorError(DapiException):
    """Error while monitoring or managing a submitted job."""

    pass
