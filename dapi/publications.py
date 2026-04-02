# dapi/publications.py
import requests
import pandas as pd
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from .exceptions import FileOperationError
from typing import Dict, List, Optional, Union


_DS_PUBLICATIONS_API = "https://designsafe-ci.org/api/publications/v2/"
_PUBLISHED_SYSTEM_ID = "designsafe.storage.published"


def _get_auth_headers(t: Tapis) -> Dict[str, str]:
    """Build authentication headers from a Tapis client."""
    token = t.access_token.access_token
    return {"X-Tapis-Token": token, "Authorization": f"Bearer {token}"}


def _pi_display(pi: Optional[Dict]) -> str:
    """Format PI dict as display name."""
    if not pi:
        return ""
    return f"{pi.get('fname', '')} {pi.get('lname', '')}".strip()


def list_publications(
    t: Tapis,
    limit: int = 100,
    offset: int = 0,
    output: str = "df",
) -> Union[pd.DataFrame, List[Dict]]:
    """List published datasets on DesignSafe.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        limit (int, optional): Maximum number of publications to return. Defaults to 100.
        offset (int, optional): Number of publications to skip. Defaults to 0.
        output (str, optional): Output format. "df" returns a pandas DataFrame
            (default), "list" returns a list of dicts.

    Returns:
        Union[pd.DataFrame, List[Dict]]: Publications in the requested format.
            DataFrame columns: projectId, title, pi, type, keywords, created.

    Raises:
        FileOperationError: If the API request fails.
        ValueError: If output format is invalid.
    """
    if output not in ("df", "list"):
        raise ValueError(f"output must be 'df' or 'list', got '{output}'")

    headers = _get_auth_headers(t)
    try:
        resp = requests.get(
            _DS_PUBLICATIONS_API,
            headers=headers,
            params={"limit": limit, "offset": offset},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FileOperationError(f"Failed to list publications: {e}") from e

    data = resp.json()
    pubs = []
    for p in data.get("result", []):
        pi = p.get("pi")
        pubs.append(
            {
                "projectId": p.get("projectId"),
                "title": p.get("title"),
                "pi": _pi_display(pi),
                "type": p.get("type"),
                "keywords": p.get("keywords", []),
                "created": p.get("created"),
            }
        )

    if output == "list":
        return pubs

    df = pd.DataFrame(pubs)
    if not df.empty and "created" in df.columns:
        df["created"] = pd.to_datetime(df["created"], errors="coerce")
    return df


def search_publications(
    t: Tapis,
    query: Optional[str] = None,
    *,
    pi: Optional[str] = None,
    keyword: Optional[str] = None,
    publication_type: Optional[str] = None,
    limit: int = 100,
    output: str = "df",
) -> Union[pd.DataFrame, List[Dict]]:
    """Search published datasets with optional filters.

    All filters are case-insensitive and combined with AND logic.
    At least one filter (query, pi, keyword, or publication_type) must be provided.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        query (str, optional): General search across title, description, keywords, and PI.
        pi (str, optional): Filter by PI name (partial match).
        keyword (str, optional): Filter by keyword (partial match against keywords list).
        publication_type (str, optional): Filter by type: "simulation", "experimental",
            "field_recon", "other", "hybrid_simulation".
        limit (int, optional): Max publications to fetch before filtering. Defaults to 100.
        output (str, optional): "df" for DataFrame (default), "list" for list of dicts.

    Returns:
        Union[pd.DataFrame, List[Dict]]: Matching publications.

    Raises:
        FileOperationError: If the API request fails.
        ValueError: If output format is invalid or no filters provided.
    """
    if output not in ("df", "list"):
        raise ValueError(f"output must be 'df' or 'list', got '{output}'")

    if not any([query, pi, keyword, publication_type]):
        raise ValueError(
            "At least one filter must be provided: query, pi, keyword, or publication_type."
        )

    headers = _get_auth_headers(t)
    try:
        resp = requests.get(
            _DS_PUBLICATIONS_API,
            headers=headers,
            params={"limit": limit, "offset": 0},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FileOperationError(f"Failed to search publications: {e}") from e

    data = resp.json()
    matches = []
    for p in data.get("result", []):
        # Apply filters with AND logic
        if query:
            searchable = " ".join(
                [
                    str(p.get("title", "")),
                    str(p.get("description", "")),
                    " ".join(p.get("keywords", [])),
                    _pi_display(p.get("pi")),
                    str(p.get("projectId", "")),
                ]
            ).lower()
            if query.lower() not in searchable:
                continue

        if pi:
            pi_name = _pi_display(p.get("pi")).lower()
            if pi.lower() not in pi_name:
                continue

        if keyword:
            kw_lower = keyword.lower()
            kw_list = [k.lower() for k in p.get("keywords", [])]
            if not any(kw_lower in k for k in kw_list):
                continue

        if publication_type:
            if (p.get("type") or "").lower() != publication_type.lower():
                continue

        matches.append(
            {
                "projectId": p.get("projectId"),
                "title": p.get("title"),
                "pi": _pi_display(p.get("pi")),
                "type": p.get("type"),
                "keywords": p.get("keywords", []),
                "created": p.get("created"),
            }
        )

    if output == "list":
        return matches

    df = pd.DataFrame(matches)
    if not df.empty and "created" in df.columns:
        df["created"] = pd.to_datetime(df["created"], errors="coerce")
    return df


def get_publication(t: Tapis, project_id: str) -> Dict:
    """Get detailed metadata for a published dataset.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        project_id (str): Project ID (e.g., "PRJ-1271").

    Returns:
        Dict: Publication metadata with keys:
            - projectId (str): Project ID
            - title (str): Publication title
            - description (str): Description
            - pi (str): PI display name
            - dois (list): DOIs
            - keywords (list): Keywords
            - dataTypes (list): Data types
            - projectType (str): Project type
            - created (str): Publication date

    Raises:
        FileOperationError: If the publication is not found or the API request fails.
    """
    headers = _get_auth_headers(t)
    try:
        resp = requests.get(
            f"{_DS_PUBLICATIONS_API}{project_id}/",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FileOperationError(
            f"Failed to get publication '{project_id}': {e}"
        ) from e

    data = resp.json()

    # Detail comes from tree.children[0].value (the actual project data)
    tree = data.get("tree", {})
    children = tree.get("children", [])
    if children:
        val = children[0].get("value", {})
        users = val.get("users", [])
        pi = next((u for u in users if u.get("role") == "pi"), None)
        return {
            "projectId": val.get("projectId"),
            "title": val.get("title"),
            "description": val.get("description"),
            "pi": _pi_display(pi),
            "dois": val.get("dois", []),
            "keywords": val.get("keywords", []),
            "dataTypes": val.get("dataTypes", []),
            "projectType": val.get("projectType"),
            "awardNumbers": val.get("awardNumbers", []),
            "created": children[0].get("publicationDate"),
        }

    # Fallback: try baseProject
    bp = data.get("baseProject", {})
    val = bp.get("value", {})
    return {
        "projectId": val.get("projectId", project_id),
        "title": val.get("title"),
        "description": val.get("description"),
        "pi": "",
        "dois": val.get("dois", []),
        "keywords": val.get("keywords", []),
        "dataTypes": val.get("dataTypes", []),
        "projectType": val.get("projectType"),
        "awardNumbers": val.get("awardNumbers", []),
        "created": bp.get("created"),
    }


def list_publication_files(
    t: Tapis,
    project_id: str,
    path: str = "/",
    limit: int = 100,
    output: str = "df",
) -> Union[pd.DataFrame, List]:
    """List files in a published dataset.

    Files are accessed via the Tapis Files API on designsafe.storage.published.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        project_id (str): Project ID (e.g., "PRJ-1271").
        path (str, optional): Path within the publication. Defaults to "/".
        limit (int, optional): Maximum items to return. Defaults to 100.
        output (str, optional): "df" for DataFrame (default), "raw" for Tapis file objects.

    Returns:
        Union[pd.DataFrame, List]: Files in the requested format.

    Raises:
        FileOperationError: If the file listing fails.
        ValueError: If output format is invalid.
    """
    if output not in ("df", "raw"):
        raise ValueError(f"output must be 'df' or 'raw', got '{output}'")

    full_path = (
        f"/{project_id}{path}" if not path.startswith(f"/{project_id}") else path
    )
    if not full_path:
        full_path = "/"

    try:
        results = t.files.listFiles(
            systemId=_PUBLISHED_SYSTEM_ID, path=full_path, limit=limit
        )
    except BaseTapyException as e:
        raise FileOperationError(
            f"Failed to list files in publication '{project_id}' at path '{path}': {e}"
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
