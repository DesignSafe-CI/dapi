# Exceptions

Custom exception classes for DAPI error handling and debugging.

## Exception Hierarchy

All exceptions inherit from Python's built-in `Exception` via `DapiException`:

```
Exception
 └── DapiException
      ├── AuthenticationError
      ├── FileOperationError
      ├── AppDiscoveryError
      ├── SystemInfoError
      ├── CredentialError
      ├── JobSubmissionError
      └── JobMonitorError
```

You can catch `DapiException` to handle any dapi-specific error, or catch a more specific subclass for targeted error handling.

---

## Base Exception

### `DapiException`

```python
class dapi.exceptions.DapiException(message: str)
```

Base exception class for all dapi-related errors.

This is the parent class for all custom exceptions in the dapi library. It can be used to catch any dapi-specific error or as a base for creating new custom exceptions.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `message` | `str` | Human-readable description of the error. |

---

## Authentication Exceptions

### `AuthenticationError`

```python
class dapi.exceptions.AuthenticationError(message: str)
```

*Inherits from {py:class}`~dapi.exceptions.DapiException`.*

Raised when authentication with Tapis fails. This includes invalid credentials, network connectivity problems, or Tapis service unavailability.

**Raised by:** `dapi.auth.init()` when credentials are invalid, missing, or the Tapis service is unreachable.

---

## File Operation Exceptions

### `FileOperationError`

```python
class dapi.exceptions.FileOperationError(message: str)
```

*Inherits from {py:class}`~dapi.exceptions.DapiException`.*

Raised when file operations fail, including uploads, downloads, directory listings, path translations, and file existence checks.

---

## Application Discovery Exceptions

### `AppDiscoveryError`

```python
class dapi.exceptions.AppDiscoveryError(message: str)
```

*Inherits from {py:class}`~dapi.exceptions.DapiException`.*

Raised when searching for Tapis applications fails, when a specific application cannot be found, or when retrieving application details encounters an error.

---

## System Information Exceptions

### `SystemInfoError`

```python
class dapi.exceptions.SystemInfoError(message: str)
```

*Inherits from {py:class}`~dapi.exceptions.DapiException`.*

Raised when operations involving Tapis execution systems fail, such as retrieving system details, listing available queues, or checking system availability.

---

## Credential Management Exceptions

### `CredentialError`

```python
class dapi.exceptions.CredentialError(message: str)
```

*Inherits from {py:class}`~dapi.exceptions.DapiException`.*

Raised when credential management operations involving Tapis Managed Secrets (TMS) fail, such as checking, establishing, or revoking user credentials on a Tapis execution system.

---

## Job Management Exceptions

### `JobSubmissionError`

```python
class dapi.exceptions.JobSubmissionError(message: str, request=None, response=None)
```

*Inherits from {py:class}`~dapi.exceptions.DapiException`.*

Raised when job submission or validation fails. This includes errors during job request generation, validation, or submission to Tapis. It carries additional context about the HTTP request and response when available.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `str` | *(required)* | Description of the job submission failure. |
| `request` | `requests.Request` | `None` | The HTTP request object that failed. |
| `response` | `requests.Response` | `None` | The HTTP response object received. |

**Attributes:**

| Name | Type | Description |
|------|------|-------------|
| `request` | `requests.Request` | The failed HTTP request, if available. |
| `response` | `requests.Response` | The HTTP response received, if available. |

The string representation includes request URL, method, response status code, and response body when available.

**Example:**

```python
try:
    job = client.jobs.submit(job_request)
except JobSubmissionError as e:
    print(f"Job submission failed: {e}")
    if e.response:
        print(f"Status code: {e.response.status_code}")
```

---

### `JobMonitorError`

```python
class dapi.exceptions.JobMonitorError(message: str)
```

*Inherits from {py:class}`~dapi.exceptions.DapiException`.*

Raised when job monitoring or management fails, including errors during job status monitoring, job cancellation, retrieving job details, or accessing job outputs.

**Example:**

```python
try:
    status = job.monitor(timeout_minutes=60)
except JobMonitorError as e:
    print(f"Job monitoring failed: {e}")
```
