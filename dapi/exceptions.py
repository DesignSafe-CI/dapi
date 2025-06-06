"""Custom exceptions for the Dapi library.

This module defines a hierarchy of exception classes that provide specific error handling
for different types of failures that can occur when interacting with DesignSafe resources
via the Tapis API.

Typical Usage:
    >>> try:
    ...     client.auth.authenticate()
    ... except AuthenticationError as e:
    ...     print(f"Authentication failed: {e}")
    
    >>> try:
    ...     client.files.upload("/local/file.txt", "tapis://system/path/file.txt")
    ... except FileOperationError as e:
    ...     print(f"File operation failed: {e}")
"""


class DapiException(Exception):
    """Base exception class for all dapi-related errors.

    This is the parent class for all custom exceptions in the dapi library.
    It can be used to catch any dapi-specific error or as a base for
    creating new custom exceptions.

    Args:
        message (str): Human-readable description of the error.

    Example:
        >>> try:
        ...     # Some dapi operation
        ...     pass
        ... except DapiException as e:
        ...     print(f"A dapi error occurred: {e}")
    """

    pass


class AuthenticationError(DapiException):
    """Exception raised when authentication with Tapis fails.

    This exception is raised when there are issues during the authentication
    process, such as invalid credentials, network connectivity problems,
    or Tapis service unavailability.

    Args:
        message (str): Description of the authentication failure.

    Example:
        >>> try:
        ...     client = DSClient(username="invalid", password="wrong")
        ... except AuthenticationError as e:
        ...     print(f"Authentication failed: {e}")
    """

    pass


class FileOperationError(DapiException):
    """Exception raised when file operations fail.

    This exception covers various file-related operations including uploads,
    downloads, directory listings, path translations, and file existence checks.

    Args:
        message (str): Description of the file operation failure.

    Example:
        >>> try:
        ...     client.files.upload("/nonexistent/file.txt", "tapis://system/file.txt")
        ... except FileOperationError as e:
        ...     print(f"File upload failed: {e}")
    """

    pass


class AppDiscoveryError(DapiException):
    """Exception raised when application discovery or retrieval fails.

    This exception is raised when searching for Tapis applications fails,
    when a specific application cannot be found, or when retrieving
    application details encounters an error.

    Args:
        message (str): Description of the application discovery failure.

    Example:
        >>> try:
        ...     app = client.apps.get_details("nonexistent-app")
        ... except AppDiscoveryError as e:
        ...     print(f"App discovery failed: {e}")
    """

    pass


class SystemInfoError(DapiException):
    """Exception raised when retrieving system information fails.

    This exception is raised when operations involving Tapis execution systems
    fail, such as retrieving system details, listing available queues,
    or checking system availability.

    Args:
        message (str): Description of the system information retrieval failure.

    Example:
        >>> try:
        ...     queues = client.systems.list_queues("nonexistent-system")
        ... except SystemInfoError as e:
        ...     print(f"System info retrieval failed: {e}")
    """

    pass


class JobSubmissionError(DapiException):
    """Exception raised when job submission or validation fails.

    This exception is raised when there are errors during job request generation,
    validation, or submission to Tapis. It includes additional context about
    the HTTP request and response when available.

    Args:
        message (str): Description of the job submission failure.
        request (requests.Request, optional): The HTTP request object that failed.
        response (requests.Response, optional): The HTTP response object received.

    Attributes:
        request (requests.Request): The failed HTTP request, if available.
        response (requests.Response): The HTTP response received, if available.

    Example:
        >>> try:
        ...     job = client.jobs.submit_request(invalid_job_request)
        ... except JobSubmissionError as e:
        ...     print(f"Job submission failed: {e}")
        ...     if e.response:
        ...         print(f"Status code: {e.response.status_code}")
    """

    def __init__(self, message, request=None, response=None):
        """Initialize JobSubmissionError with optional request/response context.

        Args:
            message (str): Description of the job submission failure.
            request (requests.Request, optional): The HTTP request that failed.
            response (requests.Response, optional): The HTTP response received.
        """
        super().__init__(message)
        self.request = request
        self.response = response

    def __str__(self):
        """Return detailed string representation including HTTP context.

        Returns:
            str: Formatted error message including request/response details when available.
        """
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
    """Exception raised when job monitoring or management fails.

    This exception is raised when there are errors during job status monitoring,
    job cancellation, retrieving job details, or accessing job outputs.

    Args:
        message (str): Description of the job monitoring failure.

    Example:
        >>> try:
        ...     status = job.monitor(timeout_minutes=60)
        ... except JobMonitorError as e:
        ...     print(f"Job monitoring failed: {e}")
    """

    pass
