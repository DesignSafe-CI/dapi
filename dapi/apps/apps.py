from tapipy.tapis import Tapis
from typing import List, Dict, Any, Optional


def find_apps(
    t: Tapis, search_term: str, list_type: str = "ALL", verbose: bool = True
) -> List[Any]:
    """
    Search for Tapis apps matching a search term.

    Args:
        t (Tapis): Tapis client instance
        search_term (str): Name or partial name to search for
        list_type (str): One of 'OWNED', 'SHARED_PUBLIC', 'SHARED_DIRECT', 'READ_PERM', 'MINE', 'ALL'
        verbose (bool): If True, prints all found apps

    Returns:
        List[Any]: List of matching app objects
    """
    results = t.apps.getApps(search=f"(id.like.*{search_term}*)", listType=list_type)

    if verbose:
        if not results:
            print(f"No apps found matching '{search_term}'")
        else:
            print(f"\nFound {len(results)} matching apps:")
            for app in results:
                print(f"- {app.id}")
            print()

    return results


def get_app_version(t: Tapis, app_id: str, verbose: bool = True) -> Optional[Any]:
    """
    Get latest version info for a specific app ID.

    Args:
        t (Tapis): Tapis client instance
        app_id (str): Exact app ID to look up
        verbose (bool): If True, prints basic app info

    Returns:
        Optional[Any]: Latest version info for the app, or None if not found
    """
    try:
        app_info = t.apps.getAppLatestVersion(appId=app_id)
        if verbose:
            print(f"App: {app_info.id}")
            print(f"Version: {app_info.version}")
            print(f"System: {app_info.jobAttributes.execSystemId}")
        return app_info
    except Exception as e:
        print(f"Error getting app info for '{app_id}': {str(e)}")
        print("\nCouldn't find exact match. Here are similar apps:")
        _ = find_apps(t, app_id)
        return None
