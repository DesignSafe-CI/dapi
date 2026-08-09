# dapi/projects.py
import requests
import pandas as pd
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from .exceptions import FileOperationError
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


_DS_PROJECTS_API = "https://designsafe-ci.org/api/projects/v2/"


def _get_auth_headers(t: Tapis) -> Dict[str, str]:
    """Build authentication headers from a Tapis client."""
    token = t.access_token.access_token
    return {"X-Tapis-Token": token, "Authorization": f"Bearer {token}"}


def _extract_pi(users: List[Dict]) -> Optional[Dict]:
    """Extract the PI from a project's users list."""
    return next((u for u in users if u.get("role") == "pi"), None)


def _pi_display(pi: Optional[Dict]) -> str:
    """Format PI dict as display name."""
    if not pi:
        return ""
    return f"{pi.get('fname', '')} {pi.get('lname', '')}".strip()


def list_projects(
    t: Tapis,
    limit: int = 100,
    offset: int = 0,
    output: str = "df",
) -> Union[pd.DataFrame, List[Dict]]:
    """List DesignSafe projects the authenticated user has access to.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        limit (int, optional): Maximum number of projects to return. Defaults to 100.
        offset (int, optional): Number of projects to skip. Defaults to 0.
        output (str, optional): Output format. "df" returns a pandas DataFrame
            (default), "list" returns a list of dicts.

    Returns:
        Union[pd.DataFrame, List[Dict]]: Projects in the requested format.
            DataFrame columns: projectId, title, pi, type, created, lastUpdated, uuid.

    Raises:
        FileOperationError: If the API request fails.
        ValueError: If output format is invalid.
    """
    if output not in ("df", "list"):
        raise ValueError(f"output must be 'df' or 'list', got '{output}'")

    headers = _get_auth_headers(t)
    try:
        resp = requests.get(
            _DS_PROJECTS_API,
            headers=headers,
            params={"limit": limit, "offset": offset},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FileOperationError(f"Failed to list projects: {e}") from e

    data = resp.json()
    projects = []
    for p in data.get("result", []):
        val = p.get("value", {})
        users = val.get("users", [])
        pi = _extract_pi(users)
        projects.append(
            {
                "projectId": val.get("projectId"),
                "title": val.get("title"),
                "pi": _pi_display(pi),
                "type": val.get("projectType"),
                "created": p.get("created"),
                "lastUpdated": p.get("lastUpdated"),
                "uuid": p.get("uuid"),
            }
        )

    if output == "list":
        return projects

    df = pd.DataFrame(projects)
    if not df.empty:
        for col in ("created", "lastUpdated"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def get_project(t: Tapis, project_id: str) -> Dict:
    """Get detailed metadata for a DesignSafe project.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        project_id (str): Project ID (e.g., "PRJ-1305") or project UUID.

    Returns:
        Dict: Project metadata with keys:
            - uuid (str): Project UUID
            - projectId (str): Project ID
            - title (str): Project title
            - description (str): Project description
            - pi (str): Principal investigator name
            - coPis (list): Co-PIs
            - teamMembers (list): Team members
            - awardNumbers (list): Award/grant numbers
            - keywords (list): Keywords
            - dois (list): Associated DOIs
            - projectType (str): Project type
            - created (str): Creation timestamp
            - lastUpdated (str): Last update timestamp
            - systemId (str): Tapis system ID for file access

    Raises:
        FileOperationError: If the project is not found or the API request fails.
    """
    headers = _get_auth_headers(t)
    try:
        resp = requests.get(
            f"{_DS_PROJECTS_API}{project_id}/",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FileOperationError(f"Failed to get project '{project_id}': {e}") from e

    data = resp.json()
    bp = data.get("baseProject", {})
    val = bp.get("value", {})
    users = val.get("users", [])
    pi = _extract_pi(users)
    uuid = bp.get("uuid", "")

    return {
        "uuid": uuid,
        "projectId": val.get("projectId"),
        "title": val.get("title"),
        "description": val.get("description"),
        "pi": _pi_display(pi),
        "coPis": val.get("coPis", []),
        "teamMembers": val.get("teamMembers", []),
        "awardNumbers": val.get("awardNumbers", []),
        "keywords": val.get("keywords", []),
        "dois": val.get("dois", []),
        "projectType": val.get("projectType"),
        "created": bp.get("created"),
        "lastUpdated": bp.get("lastUpdated"),
        "systemId": f"project-{uuid}" if uuid else None,
    }


def get_project_users(t: Tapis, project_id: str) -> List[Dict]:
    """List the users of a DesignSafe project (PI, co-PIs, team members).

    Args:
        t (Tapis): Authenticated Tapis client instance.
        project_id (str): Project ID (e.g., "PRJ-1305") or project UUID.

    Returns:
        List[Dict]: One dict per user with keys ``username``, ``fname``,
            ``lname``, ``email``, and ``role`` (e.g., "pi", "co_pi").

    Raises:
        FileOperationError: If the project is not found or the request fails.

    Example:
        >>> users = get_project_users(t, "PRJ-1305")
        >>> [u["username"] for u in users]
        ['jdoe', 'asmith']
    """
    headers = _get_auth_headers(t)
    try:
        resp = requests.get(
            f"{_DS_PROJECTS_API}{project_id}/",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FileOperationError(f"Failed to get project '{project_id}': {e}") from e

    users = resp.json().get("baseProject", {}).get("value", {}).get("users", [])
    return [
        {
            "username": u.get("username"),
            "fname": u.get("fname"),
            "lname": u.get("lname"),
            "email": u.get("email"),
            "role": u.get("role"),
        }
        for u in users
    ]


def list_project_files(
    t: Tapis,
    project_id: str,
    path: str = "/",
    limit: int = 100,
    output: str = "df",
) -> Union[pd.DataFrame, List]:
    """List files in a DesignSafe project.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        project_id (str): Project ID (e.g., "PRJ-1305").
        path (str, optional): Path within the project. Defaults to "/".
        limit (int, optional): Maximum number of items to return. Defaults to 100.
        output (str, optional): Output format. "df" returns a pandas DataFrame
            (default), "raw" returns Tapis file objects.

    Returns:
        Union[pd.DataFrame, List]: Files in the requested format.
            DataFrame columns: name, type, size, lastModified, path.

    Raises:
        FileOperationError: If the project is not found or file listing fails.
        ValueError: If output format is invalid.
    """
    if output not in ("df", "raw"):
        raise ValueError(f"output must be 'df' or 'raw', got '{output}'")

    project = get_project(t, project_id)
    system_id = project["systemId"]
    if not system_id:
        raise FileOperationError(
            f"Could not determine Tapis system ID for project '{project_id}'."
        )

    if not path:
        path = "/"

    try:
        results = t.files.listFiles(systemId=system_id, path=path, limit=limit)
    except BaseTapyException as e:
        raise FileOperationError(
            f"Failed to list files in project '{project_id}' at path '{path}': {e}"
        ) from e

    if output == "raw":
        return results

    rows = []
    for f in results:
        rows.append(
            {
                "name": getattr(f, "name", ""),
                "type": getattr(f, "type", ""),
                "size": getattr(f, "size", 0),
                "lastModified": getattr(f, "lastModified", ""),
                "path": getattr(f, "path", ""),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty and "lastModified" in df.columns:
        df["lastModified"] = pd.to_datetime(df["lastModified"], errors="coerce")
    return df


def resolve_project_uuid(t: Tapis, project_id: str) -> str:
    """Resolve a DesignSafe project ID (e.g., PRJ-1305) to its Tapis system ID.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        project_id (str): The DesignSafe project ID (e.g., "PRJ-1305").

    Returns:
        str: The Tapis system ID (e.g., "project-7997906542076432871-242ac11c-0001-012").

    Raises:
        FileOperationError: If the project cannot be found.
    """
    headers = _get_auth_headers(t)
    try:
        resp = requests.get(
            _DS_PROJECTS_API,
            headers=headers,
            params={"limit": 100},
            timeout=30,
        )
        resp.raise_for_status()
        projects = resp.json().get("result", [])
        for p in projects:
            val = p.get("value", {})
            if val.get("projectId", "") == project_id:
                uuid = p["uuid"]
                return f"project-{uuid}"
    except requests.RequestException as e:
        raise FileOperationError(
            f"Failed to query DesignSafe projects API for '{project_id}': {e}"
        ) from e

    raise FileOperationError(
        f"Project '{project_id}' not found. Ensure you have access to this project."
    )


def get_permissions(t: Tapis, project_id: str, path: str = "/") -> List[Dict]:
    """Report who can actually see *path* in a project, member by member.

    Combines the Tapis grant layer with the POSIX ACLs on Corral (the
    ground truth). A member shows ``effective: none`` when a file was
    moved in without ACL inheritance, and a reduced ``effective`` when a
    tool like scp preserved a restrictive mode and clobbered the ACL
    mask, the two ways command-line transfers break project sharing.

    Args:
        t: Authenticated Tapis client.
        project_id: Project ID (e.g. "PRJ-6457").
        path: Path inside the project. Defaults to "/".

    Returns:
        One dict per project member: username, role, tapis permission,
        the named POSIX ACL entry, the ACL mask, and the effective access.
    """
    system_id = resolve_project_uuid(t, project_id)
    members = get_project_users(t, project_id)

    acl_entries = t.files.getFacl(systemId=system_id, path=path)
    named = {}
    mask = None
    other = None
    for e in acl_entries:
        if getattr(e, "defaultAcl", False):
            continue
        if e.type == "user" and e.principal:
            named[str(e.principal)] = e.permissions
        elif e.type == "mask":
            mask = e.permissions
        elif e.type == "other":
            other = e.permissions

    def effective(entry: Optional[str]) -> str:
        # named ACL entry filtered through the mask, with the file's
        # world bits as a floor: a world-readable file stays readable
        # by members (who can traverse the project directory) even
        # when their ACL entry is missing or masked out.
        acl_part = "---"
        if entry is not None:
            acl_part = (
                entry
                if mask is None
                else "".join(
                    c if c != "-" and m != "-" else "-" for c, m in zip(entry, mask)
                )
            )
        floor = other or "---"
        eff = "".join(a if a != "-" else o for a, o in zip(acl_part, floor))
        return eff if eff.strip("-") else "none"

    report = []
    for m in members:
        user = m["username"]
        try:
            tapis_perm = t.files.getPermissions(
                systemId=system_id, path=path, username=user
            ).permission
        except Exception:
            tapis_perm = "UNKNOWN"
        entry = named.get(user)
        report.append(
            {
                "username": user,
                "role": m.get("role"),
                "tapis": tapis_perm,
                "posix_acl": entry or "missing",
                "mask": mask or "-",
                "other": other or "---",
                "effective": effective(entry),
            }
        )
    return report


def fix_project_permissions(
    t: Tapis,
    project_id: str,
    path: str = "/",
    recursive: bool = True,
    dry_run: bool = False,
) -> Dict:
    """Restore project-member access to *path* and everything under it.

    Rebuilds what command-line transfers (scp, mv, rsync) silently break:
    adds a named POSIX ACL entry for every project member, restores the
    ACL mask, and re-installs the default ACLs so files created later
    inherit access. Runs as the calling user, so the owner of the files
    can repair them without administrator help.

    Args:
        t: Authenticated Tapis client.
        project_id: Project ID (e.g. "PRJ-6457").
        path: Path inside the project to repair. Defaults to "/".
        recursive: Apply to everything under *path*. Defaults to True.
        dry_run: Report the ACL string without applying it.

    Returns:
        Dict with the aclString applied (or planned) and the Tapis result.
    """
    system_id = resolve_project_uuid(t, project_id)
    members = get_project_users(t, project_id)

    entries = [f"user:{m['username']}:rwX" for m in members]
    acl = ",".join(entries + ["mask::rwX"])
    acl_with_defaults = (
        acl
        + ","
        + ",".join(
            [f"default:user:{m['username']}:rwX" for m in members]
            + ["default:mask::rwX"]
        )
    )
    plan = {
        "system": system_id,
        "path": path,
        "aclString": acl_with_defaults,
        "recursive": recursive,
        "members": [m["username"] for m in members],
    }
    if dry_run:
        plan["applied"] = False
        return plan

    result = t.files.setFacl(
        systemId=system_id,
        path=path,
        operation="ADD",
        recursionMethod="PHYSICAL" if recursive else "NONE",
        aclString=acl_with_defaults,
    )
    plan["applied"] = True
    plan["exitCode"] = getattr(result, "exitCode", None)
    plan["stdErr"] = getattr(result, "stdErr", "") or ""
    logger.info(f"Repaired ACLs on {system_id}:{path} for {len(members)} member(s)")
    return plan
