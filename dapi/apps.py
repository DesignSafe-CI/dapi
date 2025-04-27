from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from typing import List, Any, Optional
from .exceptions import AppDiscoveryError

def find_apps(
    t: Tapis, search_term: str, list_type: str = "ALL", verbose: bool = True
) -> List[Tapis]:
    """
    Search for Tapis apps matching a search term.

    Args:
        t: Authenticated Tapis client instance.
        search_term: Name or partial name to search for. Use "" for all.
        list_type: One of 'OWNED', 'SHARED_PUBLIC', 'SHARED_DIRECT', 'READ_PERM', 'MINE', 'ALL'.
        verbose: If True, prints summary of found apps.

    Returns:
        List of matching Tapis app objects.

    Raises:
        AppDiscoveryError: If the search fails.
    """
    try:
        # Use id.like for partial matching, ensure search term is handled
        search_query = f"(id.like.*{search_term}*)" if search_term else None
        results = t.apps.getApps(search=search_query, listType=list_type, select="id,version,owner") # Select fewer fields for speed

        if verbose:
            if not results:
                print(f"No apps found matching '{search_term}' with listType '{list_type}'")
            else:
                print(f"\nFound {len(results)} matching apps:")
                for app in results:
                    print(f"- {app.id} (Version: {app.version}, Owner: {app.owner})")
                print()
        return results
    except BaseTapyException as e:
        raise AppDiscoveryError(f"Failed to search for apps matching '{search_term}': {e}") from e
    except Exception as e:
        raise AppDiscoveryError(f"An unexpected error occurred while searching for apps: {e}") from e


def get_app_details(t: Tapis, app_id: str, app_version: Optional[str] = None, verbose: bool = True) -> Optional[Tapis]:
    """
    Get detailed information for a specific app ID and version (or latest).

    Args:
        t: Authenticated Tapis client instance.
        app_id: Exact app ID to look up.
        app_version: Specific app version. If None, fetches the latest version.
        verbose: If True, prints basic app info.

    Returns:
        Tapis app object with full details, or None if not found.

    Raises:
        AppDiscoveryError: If fetching the app details fails.
    """
    try:
        if app_version:
            app_info = t.apps.getApp(appId=app_id, appVersion=app_version)
        else:
            app_info = t.apps.getAppLatestVersion(appId=app_id)

        if verbose:
            print(f"\nApp Details:")
            print(f"  ID: {app_info.id}")
            print(f"  Version: {app_info.version}")
            print(f"  Owner: {app_info.owner}")
            if hasattr(app_info, 'jobAttributes') and hasattr(app_info.jobAttributes, 'execSystemId'):
                 print(f"  Execution System: {app_info.jobAttributes.execSystemId}")
            else:
                 print("  Execution System: Not specified in jobAttributes")
            print(f"  Description: {app_info.description}")
        return app_info
    except BaseTapyException as e:
        # Check for 404 specifically
        if hasattr(e, 'response') and e.response and e.response.status_code == 404:
             print(f"App '{app_id}' (Version: {app_version or 'latest'}) not found.")
             # Optionally, try searching for similar apps
             # print("\nAttempting to find similar apps:")
             # find_apps(t, app_id, verbose=True)
             return None
        else:
             print(f"Error getting app info for '{app_id}' (Version: {app_version or 'latest'}): {e}")
             raise AppDiscoveryError(f"Failed to get details for app '{app_id}': {e}") from e
    except Exception as e:
        print(f"An unexpected error occurred getting app info for '{app_id}': {e}")
        raise AppDiscoveryError(f"Unexpected error getting details for app '{app_id}': {e}") from e