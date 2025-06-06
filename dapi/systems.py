# dapi/systems.py
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from typing import List, Any, Optional
from .exceptions import SystemInfoError


def list_system_queues(t: Tapis, system_id: str, verbose: bool = True) -> List[Any]:
    """
    Retrieves the list of batch logical queues available on a specific Tapis execution system.

    Args:
        t: Authenticated Tapis client instance.
        system_id: The ID of the execution system (e.g., 'frontera', 'stampede2').
        verbose: If True, prints the found queues.

    Returns:
        A list of queue objects (typically TapisResult instances or similar dict-like structures)
        defined for the system. Returns an empty list if the system exists but has no queues defined.

    Raises:
        SystemInfoError: If the system is not found or an API error occurs.
    """
    if not system_id:
        raise ValueError("system_id cannot be empty.")

    try:
        if verbose:
            print(f"\nFetching queue information for system '{system_id}'...")

        # Get system details - Fetch the full object to ensure queues are included
        # Removed 'select' parameter for simplicity and robustness against API variations
        system_details = t.systems.getSystem(systemId=system_id)

        # Use 'batchLogicalQueues' based on the direct API call result
        queues = getattr(system_details, "batchLogicalQueues", [])

        if not queues:
            # Check if the system itself was found but just has no queues
            try:
                # Minimal check to confirm system existence if queues list was empty
                # This might be slightly redundant if getSystem above succeeded, but safe.
                t.systems.getSystem(systemId=system_id, select="id")
                if verbose:
                    # Updated message
                    print(
                        f"System '{system_id}' found, but it has no batch logical queues defined."
                    )
                return []  # Return empty list as system exists but has no queues
            except BaseTapyException as e_check:
                # If this minimal check fails with 404, the system wasn't found initially
                if (
                    hasattr(e_check, "response")
                    and e_check.response
                    and e_check.response.status_code == 404
                ):
                    raise SystemInfoError(
                        f"Execution system '{system_id}' not found."
                    ) from e_check
                else:  # Other error during the existence check
                    raise SystemInfoError(
                        f"Error confirming existence of system '{system_id}': {e_check}"
                    ) from e_check

        if verbose:
            # Updated message
            print(f"Found {len(queues)} batch logical queues for system '{system_id}':")
            for q in queues:
                name = getattr(q, "name", "N/A")
                hpc_queue = getattr(
                    q, "hpcQueueName", "N/A"
                )  # Actual scheduler queue name
                max_jobs = getattr(q, "maxJobs", "N/A")
                max_user_jobs = getattr(q, "maxUserJobs", "N/A")
                max_mins = getattr(q, "maxMinutes", "N/A")
                max_nodes = getattr(q, "maxNodeCount", "N/A")
                # Add more attributes if desired (e.g., maxMemoryMB, maxCoresPerNode)
                print(
                    f"  - Name: {name} (HPC Queue: {hpc_queue}, Max Jobs: {max_jobs}, Max User Jobs: {max_user_jobs}, Max Mins: {max_mins}, Max Nodes: {max_nodes})"
                )

            print()

        # The items in the list are TapisResult objects themselves
        return queues

    except BaseTapyException as e:
        if hasattr(e, "response") and e.response and e.response.status_code == 404:
            raise SystemInfoError(f"Execution system '{system_id}' not found.") from e
        else:
            raise SystemInfoError(
                f"Failed to retrieve queues for system '{system_id}': {e}"
            ) from e
    except Exception as e:
        raise SystemInfoError(
            f"An unexpected error occurred while fetching queues for system '{system_id}': {e}"
        ) from e
