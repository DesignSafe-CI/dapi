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


def _acl_state(t: Tapis, system_id: str, path: str, member_names: List[str]):
    """Classify a path: (disease, named_entries, mask).

    disease is None (healthy), "mask" (entries present but capped),
    or "missing" (member entries absent, the mv/cp -p case).
    """
    named = {}
    mask = None
    for e in t.files.getFacl(systemId=system_id, path=path):
        if getattr(e, "defaultAcl", False):
            continue
        if e.type == "user" and e.principal:
            named[str(e.principal)] = e.permissions
        elif e.type == "mask":
            mask = e.permissions
    missing = [u for u in member_names if u not in named]
    if missing:
        return "missing", named, mask
    if mask is not None and "r" not in mask:
        return "mask", named, mask
    if mask is not None and "w" not in mask:
        return "mask", named, mask
    return None, named, mask


_LOCAL_MOUNT_BASES = [
    "~/MyProjects",
    "/home/jupyter/MyProjects",
    "~/projects",
    "/home/jupyter/projects",
]


def _discover_local_root(
    project_id: str,
    title: str,
    uuid: str,
    remote_names: List[str],
    bases: Optional[List[str]] = None,
) -> Optional[str]:
    """Find this project's directory on a local mount (JupyterHub).

    Scans the known DesignSafe mount locations for a folder whose name
    matches the project id, title, or uuid, then validates the match by
    checking that files known to exist in the project also exist there.
    Returns None when not on a machine with the project mounted.
    """
    import os as _os

    keys = {project_id.lower(), title.lower(), uuid.lower()}
    for base in bases or _LOCAL_MOUNT_BASES:
        base = _os.path.expanduser(base)
        if not _os.path.isdir(base):
            continue
        for name in sorted(_os.listdir(base)):
            low = name.lower()
            if low not in keys and project_id.lower() not in low:
                continue
            cand = _os.path.join(base, name)
            if not _os.path.isdir(cand):
                continue
            if not remote_names or any(
                _os.path.exists(_os.path.join(cand, rn.lstrip("/")))
                for rn in remote_names[:3]
            ):
                logger.info(f"Using local project mount at {cand}")
                return cand
    return None


def fix_project_permissions(
    t: Tapis,
    project_id: str,
    path: str = "/",
    recursive: bool = True,
    dry_run: bool = False,
    local_root: Optional[str] = None,
) -> Dict:
    """Restore project-member access, using the strongest strategy each file allows.

    Command-line transfers into My Projects break sharing in two ways:
    a restrictive mode caps the ACL mask (scp, cp), or the member ACL
    entries are wiped entirely (mv, cp -p, rsync -a). Tapis operates as
    the project service account, so what it can repair depends on each
    file's owner and readability. This routine tries, per broken file:

    1. **direct**: ``setFacl`` (works on everything the service account
       owns, including the new-member-added-later case).
    2. **local**: when *local_root* points at the project on a mounted
       filesystem (JupyterHub), fix as the calling user: ``chmod`` for
       mask damage, copy-in-place for wiped entries.
    3. **copy**: Tapis copy-recreate (new file owned by the service
       account, inherits healthy ACLs), then swap it over the original.
       Requires the file to be readable by the service account; changes
       the file's owner to the service account.
    4. Otherwise the file is reported **unfixable** with the exact
       command its owner can paste into any TACC shell.

    Healthy files are skipped. Directories get their default ACLs
    refreshed so future files inherit access for all current members.

    Args:
        t: Authenticated Tapis client.
        project_id: Project ID (e.g. "PRJ-6457").
        path: File or directory inside the project. Defaults to "/".
        recursive: Descend into directories. Defaults to True.
        dry_run: Classify and plan only; change nothing.
        local_root: Local path of the project root when it is mounted
            (e.g. "~/MyProjects/My Project" on JupyterHub). Auto-detected
            on JupyterHub when omitted; pass it explicitly for unusual
            mount locations. Enables the local tier.

    Returns:
        Dict with ``fixed`` (path -> strategy), ``skipped_healthy``,
        ``dirs_refreshed``, and ``unfixable`` (path, disease, and the
        owner command).
    """
    import os as _os
    import shutil as _shutil

    system_id = resolve_project_uuid(t, project_id)
    members = get_project_users(t, project_id)
    names = [m["username"] for m in members]
    entries = ",".join([f"user:{u}:rwX" for u in names] + ["mask::rwX"])
    dir_entries = (
        entries
        + ","
        + ",".join([f"default:user:{u}:rwX" for u in names] + ["default:mask::rwX"])
    )
    root_dir = getattr(t.systems.getSystem(systemId=system_id), "rootDir", "")

    # collect targets
    files, dirs = [], []
    top = t.files.listFiles(systemId=system_id, path=path)
    is_dir = (
        len(top) != 1
        or getattr(top[0], "type", "") == "dir"
        or (getattr(top[0], "path", "").strip("/") != path.strip("/"))
    )
    if is_dir:
        dirs.append(path)
        listing = t.files.listFiles(systemId=system_id, path=path, recurse=recursive)
        for item in listing:
            rel = "/" + getattr(item, "path", item.name).lstrip("/")
            (dirs if getattr(item, "type", "file") == "dir" else files).append(rel)
    else:
        files.append(path)

    if local_root is None:
        try:
            proj = get_project(t, project_id)
            local_root = _discover_local_root(
                project_id,
                str(proj.get("title", "")),
                str(proj.get("uuid", "")),
                [f.lstrip("/") for f in files[:3]],
            )
        except Exception as e:
            logger.debug(f"Local mount discovery skipped: {e}")

    report = {
        "fixed": {},
        "skipped_healthy": [],
        "dirs_refreshed": [],
        "unfixable": [],
        "local_root": local_root,
    }

    def _set(path_, acl):
        return t.files.setFacl(
            systemId=system_id,
            path=path_,
            operation="ADD",
            recursionMethod="NONE",
            aclString=acl,
        )

    def _owner_cmd(path_, disease):
        target = f"{root_dir.rstrip('/')}/{path_.lstrip('/')}"
        if disease == "mask":
            return f"chmod g+rwX '{target}'"
        return f"cp -p '{target}' '{target}.tmp' && cp '{target}.tmp' '{target}' && rm '{target}.tmp'"

    for d in dirs:
        if dry_run:
            report["dirs_refreshed"].append(d + " (planned)")
            continue
        r = _set(d, dir_entries)
        if getattr(r, "exitCode", 1) == 0:
            report["dirs_refreshed"].append(d)

    for fpath in files:
        disease, _named, _mask = _acl_state(t, system_id, fpath, names)
        if disease is None:
            report["skipped_healthy"].append(fpath)
            continue
        if dry_run:
            report["fixed"][fpath] = f"planned ({disease})"
            continue

        # tier 1: direct setFacl
        r = _set(fpath, entries)
        if getattr(r, "exitCode", 1) == 0:
            report["fixed"][fpath] = "direct"
            continue

        # tier 2: local mount as the calling user. Mounted filesystems can
        # silently drop chmod (returning success while changing nothing on
        # the backing store), so never trust the local call: re-check the
        # ACL state through Tapis before claiming the fix.
        if local_root:
            local_path = _os.path.join(
                _os.path.expanduser(local_root), fpath.lstrip("/")
            )
            try:
                if disease == "mask":
                    st = _os.stat(local_path)
                    _os.chmod(local_path, st.st_mode | 0o060)
                else:  # missing entries: copy-in-place inherits defaults
                    tmp = local_path + ".dapi-tmp"
                    _shutil.copyfile(local_path, tmp)
                    _os.replace(tmp, local_path)
                verified, _n, _m = _acl_state(t, system_id, fpath, names)
                if verified is None:
                    report["fixed"][fpath] = "local"
                    continue
                logger.debug(
                    f"local fix had no effect on {fpath} "
                    f"(mount dropped the change); trying the next tier"
                )
            except OSError as e:
                logger.debug(f"local fix failed for {fpath}: {e}")

        # tier 3: Tapis copy-recreate (readable files only)
        tmp_remote = fpath + ".dapi-fixing"
        try:
            t.files.moveCopy(
                systemId=system_id,
                path=fpath,
                operation="COPY",
                newPath=tmp_remote,
            )
            _set(tmp_remote, entries)
            t.files.delete(systemId=system_id, path=fpath)
            t.files.moveCopy(
                systemId=system_id,
                path=tmp_remote,
                operation="MOVE",
                newPath=fpath,
            )
            report["fixed"][fpath] = "copy (owner is now the project service account)"
            continue
        except Exception as e:
            logger.debug(f"copy-recreate failed for {fpath}: {e}")
            try:
                t.files.delete(systemId=system_id, path=tmp_remote)
            except Exception:
                pass

        report["unfixable"].append(
            {
                "path": fpath,
                "disease": disease,
                "owner_fix": _owner_cmd(fpath, disease),
            }
        )

    logger.info(
        f"fix_permissions on {project_id}{path}: "
        f"{len(report['fixed'])} fixed, {len(report['skipped_healthy'])} healthy, "
        f"{len(report['unfixable'])} need the owner"
    )
    return report
