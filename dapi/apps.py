import json
import logging
import os
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from tapipy.errors import BaseTapyException
from tapipy.tapis import Tapis

from .exceptions import AppDiscoveryError

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates" / "apps"


def list_app_templates() -> List[str]:
    """Names of the app templates that ship with dapi."""
    return sorted(p.name for p in _TEMPLATES_DIR.iterdir() if p.is_dir())


def new_app(app_id: str, target_dir: str = ".", template: str = "container") -> str:
    """Write the files for a new Tapis app from a dapi template.

    Creates ``<target_dir>/<app_id>/`` containing ``app.json`` (the app
    definition) and ``tapisjob_app.sh`` (the wrapper the job executes).
    Edit them as needed, then register the app with :func:`deploy_app`.

    Args:
        app_id: Id for the new app (also the directory name).
        target_dir: Where to create the app directory.
        template: One of :func:`list_app_templates`. The ``container``
            template runs any image (``docker://`` or staged ``.sif``)
            via apptainer, with CONTAINER_IMAGE and COMMAND as job
            parameters.

    Returns:
        Path of the created app directory.
    """
    src = _TEMPLATES_DIR / template
    if not src.is_dir():
        raise AppDiscoveryError(
            f"Unknown app template '{template}'. Available: {list_app_templates()}"
        )
    dest = Path(target_dir) / app_id
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.iterdir()):
        out = dest / f.name
        if out.exists():
            raise AppDiscoveryError(f"{out} already exists; not overwriting.")
        out.write_text(f.read_text().replace("__APP_ID__", app_id))
        if f.suffix == ".sh":
            out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
    logger.info(f"Created app '{app_id}' from template '{template}' at {dest}")
    return str(dest)


def deploy_app(
    t: Tapis,
    app_dir: str,
    version: Optional[str] = None,
    assets_system: str = "designsafe.storage.default",
    assets_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Register (or update) a user-owned Tapis app from an app directory.

    Zips every file in *app_dir* except ``app.json`` (the wrapper script
    plus any helpers), uploads the zip to your storage, points the app
    definition's ``containerImage`` at it, and registers the version
    with the Tapis apps service. Rerunning with the same version updates
    the existing app in place, so iterate freely.

    Args:
        t: Authenticated Tapis client.
        app_dir: Directory containing ``app.json`` and the wrapper.
        version: Override the version in ``app.json``.
        assets_system: Storage system for the zip.
        assets_path: Path for the zip on *assets_system*. Defaults to
            ``<username>/apps/<app_id>/<version>``.

    Returns:
        Dict with ``app_id``, ``version``, and ``container_image``.
    """
    app_dir_path = Path(app_dir)
    spec = json.loads((app_dir_path / "app.json").read_text())
    spec.pop("owner", None)  # the caller owns the app
    app_id = spec["id"]
    version = version or spec["version"]
    spec["version"] = version

    username = t.username
    assets_path = assets_path or f"{username}/apps/{app_id}/{version}"

    tmp = tempfile.mkdtemp(prefix="dapi-app-")
    zip_path = os.path.join(tmp, f"{app_id}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(app_dir_path.iterdir()):
            if f.is_file() and f.name != "app.json":
                info = zipfile.ZipInfo(f.name)
                info.external_attr = 0o755 << 16  # keep scripts executable
                zf.writestr(info, f.read_bytes())
    t.upload(
        system_id=assets_system,
        source_file_path=zip_path,
        dest_file_path=f"{assets_path}/{app_id}.zip",
    )
    spec["containerImage"] = f"tapis://{assets_system}/{assets_path}/{app_id}.zip"

    try:
        t.apps.createAppVersion(**spec)
        logger.info(f"Registered app {app_id} v{version}")
    except BaseTapyException as e:
        if "APPAPI_APP_EXISTS" not in str(e) and "already exists" not in str(e):
            raise
        t.apps.putApp(appId=app_id, appVersion=version, **spec)
        logger.info(f"Updated existing app {app_id} v{version}")

    return {
        "app_id": app_id,
        "version": version,
        "container_image": spec["containerImage"],
    }


def find_apps(
    t: Tapis, search_term: str, list_type: str = "ALL", verbose: bool = True
) -> List[Tapis]:
    """Search for Tapis apps matching a search term.

    Searches through available Tapis applications using partial name matching.
    This function helps discover applications available for job submission.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        search_term (str): Name or partial name to search for. Use empty string
            for all apps. Supports partial matching with wildcards.
        list_type (str, optional): Type of apps to list. Must be one of:
            'OWNED', 'SHARED_PUBLIC', 'SHARED_DIRECT', 'READ_PERM', 'MINE', 'ALL'.
            Defaults to "ALL".
        verbose (bool, optional): If True, prints summary of found apps including
            ID, version, and owner information. Defaults to True.

    Returns:
        List[Tapis]: List of matching Tapis app objects with selected fields
            (id, version, owner).

    Raises:
        AppDiscoveryError: If the Tapis API search fails or an unexpected
            error occurs during the search operation.

    Example:
        >>> find_apps(client, "matlab", verbose=True)
        Found 3 matching apps:
        - matlab-r2023a (Version: 1.0, Owner: designsafe)
        - matlab-parallel (Version: 2.1, Owner: tacc)
        - matlab-desktop (Version: 1.5, Owner: designsafe)
    """
    try:
        # Use id.like for partial matching, ensure search term is handled
        search_query = f"(id.like.*{search_term}*)" if search_term else None
        results = t.apps.getApps(
            search=search_query, listType=list_type, select="id,version,owner"
        )  # Select fewer fields for speed

        if verbose:
            if not results:
                print(
                    f"No apps found matching '{search_term}' with listType '{list_type}'"
                )
            else:
                print(f"\nFound {len(results)} matching apps:")
                for app in results:
                    print(f"- {app.id} (Version: {app.version}, Owner: {app.owner})")
                print()
        return results
    except BaseTapyException as e:
        raise AppDiscoveryError(
            f"Failed to search for apps matching '{search_term}': {e}"
        ) from e
    except Exception as e:
        raise AppDiscoveryError(
            f"An unexpected error occurred while searching for apps: {e}"
        ) from e


def get_app_details(
    t: Tapis, app_id: str, app_version: Optional[str] = None, verbose: bool = True
) -> Optional[Tapis]:
    """Get detailed information for a specific app ID and version.

    Retrieves comprehensive details about a specific Tapis application,
    including job attributes, execution system, and parameter definitions.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        app_id (str): Exact app ID to look up. Must match exactly.
        app_version (Optional[str], optional): Specific app version to retrieve.
            If None, fetches the latest available version. Defaults to None.
        verbose (bool, optional): If True, prints basic app information including
            ID, version, owner, execution system, and description. Defaults to True.

    Returns:
        Optional[Tapis]: Tapis app object with full details including jobAttributes,
            parameterSet, and other configuration. Returns None if the app is not found.

    Raises:
        AppDiscoveryError: If the Tapis API call fails (except for 404 not found)
            or an unexpected error occurs during retrieval.

    Example:
        >>> app = get_app_details(client, "matlab-r2023a", "1.0")
        App Details:
          ID: matlab-r2023a
          Version: 1.0
          Owner: designsafe
          Execution System: frontera
          Description: MATLAB R2023a runtime environment
    """
    try:
        if app_version:
            app_info = t.apps.getApp(appId=app_id, appVersion=app_version)
        else:
            app_info = t.apps.getAppLatestVersion(appId=app_id)

        if verbose:
            print("\nApp Details:")
            print(f"  ID: {app_info.id}")
            print(f"  Version: {app_info.version}")
            print(f"  Owner: {app_info.owner}")
            if hasattr(app_info, "jobAttributes") and hasattr(
                app_info.jobAttributes, "execSystemId"
            ):
                print(f"  Execution System: {app_info.jobAttributes.execSystemId}")
            else:
                print("  Execution System: Not specified in jobAttributes")
            print(f"  Description: {app_info.description}")
        return app_info
    except BaseTapyException as e:
        # Check for 404 specifically
        if hasattr(e, "response") and e.response and e.response.status_code == 404:
            print(f"App '{app_id}' (Version: {app_version or 'latest'}) not found.")
            # Optionally, try searching for similar apps
            # print("\nAttempting to find similar apps:")
            # find_apps(t, app_id, verbose=True)
            return None
        else:
            print(
                f"Error getting app info for '{app_id}' (Version: {app_version or 'latest'}): {e}"
            )
            raise AppDiscoveryError(
                f"Failed to get details for app '{app_id}': {e}"
            ) from e
    except Exception as e:
        print(f"An unexpected error occurred getting app info for '{app_id}': {e}")
        raise AppDiscoveryError(
            f"Unexpected error getting details for app '{app_id}': {e}"
        ) from e
