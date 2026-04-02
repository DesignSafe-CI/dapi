# dapi/projects.py
import requests
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from .exceptions import FileOperationError
from typing import Dict, List, Optional


_DS_PROJECTS_API = "https://designsafe-ci.org/api/projects/v2/"


def _get_auth_headers(t: Tapis) -> Dict[str, str]:
    """Build authentication headers from a Tapis client."""
    token = t.access_token.access_token
    return {"X-Tapis-Token": token, "Authorization": f"Bearer {token}"}


def list_projects(t: Tapis, limit: int = 100, offset: int = 0) -> List[Dict]:
    """List DesignSafe projects the authenticated user has access to.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        limit (int, optional): Maximum number of projects to return. Defaults to 100.
        offset (int, optional): Number of projects to skip. Defaults to 0.

    Returns:
        List[Dict]: List of project dictionaries with keys:
            - uuid (str): Project UUID
            - projectId (str): Project ID (e.g., "PRJ-1305")
            - title (str): Project title
            - pi (dict): Principal investigator info (username, fname, lname)
            - created (str): Creation timestamp
            - lastUpdated (str): Last update timestamp

    Raises:
        FileOperationError: If the API request fails.
    """
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
        pi = next((u for u in users if u.get("role") == "pi"), None)
        projects.append(
            {
                "uuid": p.get("uuid"),
                "projectId": val.get("projectId"),
                "title": val.get("title"),
                "pi": pi,
                "created": p.get("created"),
                "lastUpdated": p.get("lastUpdated"),
            }
        )
    return projects


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
            - pi (dict): Principal investigator info
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
    pi = next((u for u in users if u.get("role") == "pi"), None)
    uuid = bp.get("uuid", "")

    return {
        "uuid": uuid,
        "projectId": val.get("projectId"),
        "title": val.get("title"),
        "description": val.get("description"),
        "pi": pi,
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


def list_project_files(
    t: Tapis, project_id: str, path: str = "/", limit: int = 100
) -> List:
    """List files in a DesignSafe project.

    Resolves the project ID to a Tapis system and lists files at the given path.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        project_id (str): Project ID (e.g., "PRJ-1305").
        path (str, optional): Path within the project. Defaults to "/".
        limit (int, optional): Maximum number of items to return. Defaults to 100.

    Returns:
        List: List of Tapis file objects with name, type, size, etc.

    Raises:
        FileOperationError: If the project is not found or file listing fails.
    """
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
        return results
    except BaseTapyException as e:
        raise FileOperationError(
            f"Failed to list files in project '{project_id}' at path '{path}': {e}"
        ) from e


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
