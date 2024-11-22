import os
from tapipy.tapis import Tapis


def get_ds_path_uri(t: Tapis, path: str) -> str:
    """
    Given a path on DesignSafe, determine the correct input URI for Tapis v3.

    Args:
    t (Tapis): Tapis object to fetch profiles or metadata.
    path (str): The directory path.

    Returns:
    str: The corresponding input URI.

    Raises:
    ValueError: If no matching directory pattern is found.
    """
    # If any of the following directory patterns are found in the path,
    # process them accordingly.
    directory_patterns = [
        ("jupyter/MyData", "designsafe.storage.default", True),
        ("jupyter/mydata", "designsafe.storage.default", True),
        ("jupyter/CommunityData", "designsafe.storage.community", False),
        ("/MyData", "designsafe.storage.default", True),
        ("/mydata", "designsafe.storage.default", True),
    ]

    for pattern, storage, use_username in directory_patterns:
        if pattern in path:
            path = path.split(pattern, 1)[1].lstrip("/")
            input_dir = f"{t.username}/{path}" if use_username else path
            input_uri = f"tapis://{storage}/{input_dir}"
            return input_uri.replace(" ", "%20")

    project_patterns = [
        ("jupyter/MyProjects", "project-"),
        ("jupyter/projects", "project-"),
    ]

    for pattern, prefix in project_patterns:
        if pattern in path:
            path = path.split(pattern, 1)[1].lstrip("/")
            project_id, *rest = path.split("/", 1)
            path = rest[0] if rest else ""

            # Using Tapis v3 to get project UUID
            resp = t.get(f"https://designsafe-ci.org/api/projects/v2/{project_id}")
            project_uuid = resp.json()["baseProject"]["uuid"]

            input_uri = f"tapis://{prefix}{project_uuid}/{path}"
            return input_uri.replace(" ", "%20")

    raise ValueError(f"No matching directory pattern found for: {path}")
