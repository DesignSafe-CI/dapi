# dapi/systems.py
import pandas as pd
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException, UnauthorizedError, NotFoundError
from typing import Dict, List, Any, Optional, Union
from .exceptions import SystemInfoError, CredentialError


# Known DesignSafe system categories
_KNOWN_HPC = {"stampede3", "frontera", "ls6", "vista"}
_KNOWN_STORAGE = {
    "designsafe.storage.default",
    "designsafe.storage.community",
    "designsafe.storage.published",
    "nees.public",
}
_INTERNAL_PREFIXES = ("project-", "apcd.", "wma-", "ds-stko", "cloud.data", "c4-")
_DUPLICATE_SUFFIXES = (".tms", ".designsafe", "-simcenter")
_STORAGE_PREFIXES = ("designsafe.storage.",)


def list_systems(
    t: Tapis,
    category: Optional[str] = None,
    output: str = "df",
) -> Union[pd.DataFrame, List[Dict]]:
    """List Tapis systems the user has access to.

    Filters out internal, duplicate, and project-specific systems by default,
    showing only the systems useful for job submission and data access.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        category (str, optional): Filter by category:
            "hpc" for execution systems (stampede3, frontera, ls6, vista),
            "storage" for storage systems (MyData, CommunityData, etc.),
            "all" for all systems without filtering.
            If None, shows HPC + storage (excludes internal/project systems).
        output (str, optional): "df" for DataFrame (default), "list" for dicts.

    Returns:
        Union[pd.DataFrame, List[Dict]]: Systems with id, host, type, category, credentials.

    Raises:
        SystemInfoError: If the API request fails.
        ValueError: If output or category is invalid.
    """
    if output not in ("df", "list"):
        raise ValueError(f"output must be 'df' or 'list', got '{output}'")
    if category is not None and category not in ("hpc", "storage", "all"):
        raise ValueError(
            f"category must be 'hpc', 'storage', 'all', or None, got '{category}'"
        )

    try:
        all_systems = t.systems.getSystems(listType="ALL", limit=200)
    except BaseTapyException as e:
        raise SystemInfoError(f"Failed to list systems: {e}") from e

    username = getattr(t, "username", None)
    rows = []

    for s in all_systems:
        sid = s.id
        host = getattr(s, "host", "")
        can_exec = getattr(s, "canExec", False)
        authn = getattr(s, "defaultAuthnMethod", "")

        # Classify
        if sid in _KNOWN_HPC:
            cat = "hpc"
        elif sid in _KNOWN_STORAGE:
            cat = "storage"
        elif (
            any(sid.startswith(pfx) for pfx in _STORAGE_PREFIXES)
            and sid not in _KNOWN_STORAGE
        ):
            cat = "internal"
        elif sid.startswith("project-"):
            cat = "project"
        elif any(sid.endswith(sfx) for sfx in _DUPLICATE_SUFFIXES):
            cat = "internal"
        elif any(sid.startswith(pfx) for pfx in _INTERNAL_PREFIXES):
            cat = "internal"
        elif sid == "maverick2":
            cat = "internal"
        elif can_exec:
            cat = "hpc"
        else:
            cat = "other"

        # Filter
        if category == "hpc" and cat != "hpc":
            continue
        if category == "storage" and cat != "storage":
            continue
        if category is None and cat not in ("hpc", "storage"):
            continue
        # category == "all" shows everything

        # Check TMS credentials for HPC systems
        has_creds = None
        if cat == "hpc" and authn == "TMS_KEYS" and username:
            try:
                has_creds = check_credentials(t, sid, username)
            except Exception:
                has_creds = None

        rows.append(
            {
                "id": sid,
                "host": host,
                "category": cat,
                "authn": authn,
                "credentials": has_creds,
            }
        )

    if output == "list":
        return rows

    return pd.DataFrame(rows)


def list_system_queues(
    t: Tapis,
    system_id: str,
    output: str = "df",
) -> Union[pd.DataFrame, List[Any]]:
    """List batch queues available on a Tapis execution system.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        system_id (str): The ID of the execution system (e.g., "stampede3").
        output (str, optional): "df" for DataFrame (default), "raw" for Tapis objects.

    Returns:
        Union[pd.DataFrame, List]: Queues with name, maxNodes, maxMinutes, maxCoresPerNode, etc.

    Raises:
        SystemInfoError: If the system is not found or an API error occurs.
        ValueError: If system_id is empty or output is invalid.
    """
    if not system_id:
        raise ValueError("system_id cannot be empty.")
    if output not in ("df", "raw"):
        raise ValueError(f"output must be 'df' or 'raw', got '{output}'")

    try:
        system_details = t.systems.getSystem(systemId=system_id)
        queues = getattr(system_details, "batchLogicalQueues", [])

        if not queues:
            if output == "raw":
                return []
            return pd.DataFrame()

        if output == "raw":
            return queues

        rows = []
        for q in queues:
            rows.append(
                {
                    "name": getattr(q, "name", ""),
                    "hpcQueue": getattr(q, "hpcQueueName", ""),
                    "maxNodes": getattr(q, "maxNodeCount", None),
                    "maxCoresPerNode": getattr(q, "maxCoresPerNode", None),
                    "maxMinutes": getattr(q, "maxMinutes", None),
                    "maxMemoryMB": getattr(q, "maxMemoryMB", None),
                    "maxJobsPerUser": getattr(q, "maxJobsPerUser", None),
                }
            )
        return pd.DataFrame(rows)

    except BaseTapyException as e:
        if hasattr(e, "response") and e.response and e.response.status_code == 404:
            raise SystemInfoError(f"Execution system '{system_id}' not found.") from e
        raise SystemInfoError(
            f"Failed to retrieve queues for system '{system_id}': {e}"
        ) from e


def _resolve_username(t: Tapis, username: Optional[str] = None) -> str:
    """Resolve the effective username from an explicit parameter or the Tapis client.

    Args:
        t: Authenticated Tapis client instance.
        username: Explicit username. If None, falls back to t.username.

    Returns:
        The resolved username string.

    Raises:
        ValueError: If username cannot be determined from either source.
    """
    effective = username or getattr(t, "username", None)
    if not effective:
        raise ValueError(
            "Username must be provided or available on the Tapis client (t.username)."
        )
    return effective


def check_credentials(t: Tapis, system_id: str, username: Optional[str] = None) -> bool:
    """Check whether TMS credentials exist for a user on a Tapis system.

    Args:
        t: Authenticated Tapis client instance.
        system_id: The ID of the Tapis system (e.g., 'frontera', 'stampede3').
        username: The username to check. If None, auto-detected from t.username.

    Returns:
        True if credentials exist, False if they do not.

    Raises:
        ValueError: If system_id is empty or username cannot be determined.
        CredentialError: If an unexpected API error occurs during the check.
    """
    if not system_id:
        raise ValueError("system_id cannot be empty.")

    effective_username = _resolve_username(t, username)

    try:
        t.systems.checkUserCredential(systemId=system_id, userName=effective_username)
        return True
    except (UnauthorizedError, NotFoundError):
        return False
    except BaseTapyException as e:
        raise CredentialError(
            f"Failed to check credentials for user '{effective_username}' "
            f"on system '{system_id}': {e}"
        ) from e
    except Exception as e:
        raise CredentialError(
            f"Unexpected error checking credentials for user '{effective_username}' "
            f"on system '{system_id}': {e}"
        ) from e


def establish_credentials(
    t: Tapis,
    system_id: str,
    username: Optional[str] = None,
    force: bool = False,
    verbose: bool = True,
) -> None:
    """Establish TMS credentials for a user on a Tapis system.

    Idempotent: if credentials already exist and force is False, no action is taken.
    Only systems with defaultAuthnMethod 'TMS_KEYS' are supported.

    Args:
        t: Authenticated Tapis client instance.
        system_id: The ID of the Tapis system (e.g., 'frontera', 'stampede3').
        username: The username. If None, auto-detected from t.username.
        force: If True, create credentials even if they already exist.
        verbose: If True, prints status messages.

    Raises:
        ValueError: If system_id is empty or username cannot be determined.
        CredentialError: If the system does not use TMS_KEYS, if the system is
            not found, or if credential creation fails.
    """
    if not system_id:
        raise ValueError("system_id cannot be empty.")

    effective_username = _resolve_username(t, username)

    # Verify system exists and uses TMS_KEYS authentication
    try:
        system_details = t.systems.getSystem(systemId=system_id)
        authn_method = getattr(system_details, "defaultAuthnMethod", None)
    except BaseTapyException as e:
        if hasattr(e, "response") and e.response and e.response.status_code == 404:
            raise CredentialError(f"System '{system_id}' not found.") from e
        raise CredentialError(f"Failed to retrieve system '{system_id}': {e}") from e

    if authn_method != "TMS_KEYS":
        raise CredentialError(
            f"System '{system_id}' uses authentication method '{authn_method}', "
            f"not 'TMS_KEYS'. TMS credential management is only supported "
            f"for TMS_KEYS systems."
        )

    # Check existing credentials unless force is True
    if not force:
        if check_credentials(t, system_id, effective_username):
            if verbose:
                print(
                    f"Credentials already exist for user '{effective_username}' "
                    f"on system '{system_id}'. No action taken."
                )
            return

    # Create credentials
    try:
        t.systems.createUserCredential(
            systemId=system_id,
            userName=effective_username,
            createTmsKeys=True,
        )
        if verbose:
            print(
                f"TMS credentials established for user '{effective_username}' "
                f"on system '{system_id}'."
            )
    except BaseTapyException as e:
        raise CredentialError(
            f"Failed to create credentials for user '{effective_username}' "
            f"on system '{system_id}': {e}"
        ) from e
    except Exception as e:
        raise CredentialError(
            f"Unexpected error creating credentials for user '{effective_username}' "
            f"on system '{system_id}': {e}"
        ) from e


def revoke_credentials(
    t: Tapis,
    system_id: str,
    username: Optional[str] = None,
    verbose: bool = True,
) -> None:
    """Remove TMS credentials for a user on a Tapis system.

    Idempotent: if credentials do not exist, no error is raised.

    Args:
        t: Authenticated Tapis client instance.
        system_id: The ID of the Tapis system (e.g., 'frontera', 'stampede3').
        username: The username. If None, auto-detected from t.username.
        verbose: If True, prints status messages.

    Raises:
        ValueError: If system_id is empty or username cannot be determined.
        CredentialError: If credential removal fails unexpectedly.
    """
    if not system_id:
        raise ValueError("system_id cannot be empty.")

    effective_username = _resolve_username(t, username)

    try:
        t.systems.removeUserCredential(systemId=system_id, userName=effective_username)
        if verbose:
            print(
                f"Credentials revoked for user '{effective_username}' "
                f"on system '{system_id}'."
            )
    except (UnauthorizedError, NotFoundError):
        if verbose:
            print(
                f"No credentials found for user '{effective_username}' "
                f"on system '{system_id}'. No action taken."
            )
    except BaseTapyException as e:
        raise CredentialError(
            f"Failed to revoke credentials for user '{effective_username}' "
            f"on system '{system_id}': {e}"
        ) from e
    except Exception as e:
        raise CredentialError(
            f"Unexpected error revoking credentials for user '{effective_username}' "
            f"on system '{system_id}': {e}"
        ) from e


# Default TACC execution systems that use TMS_KEYS
TACC_SYSTEMS = ["frontera", "stampede3", "ls6"]


def setup_tms_credentials(
    t: Tapis,
    systems: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Check and establish TMS credentials on execution systems.

    For each system, checks if credentials exist and creates them if missing.
    Failures are handled gracefully — a system that can't be reached or where
    the user lacks an allocation is skipped with a warning.

    Args:
        t: Authenticated Tapis client instance.
        systems: List of system IDs to set up. Defaults to TACC_SYSTEMS
            (frontera, stampede3, ls6).

    Returns:
        Dict mapping system_id to status: "ready", "created", or "skipped".
    """
    if systems is None:
        systems = TACC_SYSTEMS

    username = getattr(t, "username", None)
    if not username:
        print("Warning: Could not determine username. Skipping TMS setup.")
        return {s: "skipped" for s in systems}

    results = {}

    for system_id in systems:
        try:
            # Check if system uses TMS_KEYS
            system_details = t.systems.getSystem(systemId=system_id)
            authn_method = getattr(system_details, "defaultAuthnMethod", None)

            if authn_method != "TMS_KEYS":
                results[system_id] = "skipped"
                continue

            # Check existing credentials
            if check_credentials(t, system_id, username):
                results[system_id] = "ready"
                continue

            # Try to create credentials
            t.systems.createUserCredential(
                systemId=system_id,
                userName=username,
                createTmsKeys=True,
            )
            results[system_id] = "created"

        except Exception:
            results[system_id] = "skipped"

    # Print summary
    ready = [s for s, v in results.items() if v in ("ready", "created")]
    created = [s for s, v in results.items() if v == "created"]
    skipped = [s for s, v in results.items() if v == "skipped"]

    if ready:
        msg = f"TMS credentials ready: {', '.join(ready)}"
        if created:
            msg += f" (newly created: {', '.join(created)})"
        print(msg)
    if skipped:
        print(f"TMS credentials skipped: {', '.join(skipped)}")

    return results
