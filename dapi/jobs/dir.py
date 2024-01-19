import os


def get_ds_path_uri(ag, path):
    """
    Given a path on DesignSafe, determine the correct input URI.

    Args:
        ag (object): Agave object to fetch profiles or metadata.
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
            path = path.split(pattern).pop()
            input_dir = ag.profiles.get()["username"] + path if use_username else path
            input_uri = f"agave://{storage}/{input_dir}"
            return input_uri.replace(" ", "%20")

    project_patterns = [
        ("jupyter/MyProjects", "project-"),
        ("jupyter/projects", "project-"),
    ]

    for pattern, prefix in project_patterns:
        if pattern in path:
            path = path.split(pattern + "/").pop()
            project_id = path.split("/")[0]
            query = {"value.projectId": str(project_id)}
            path = path.split(project_id).pop()
            project_uuid = ag.meta.listMetadata(q=str(query))[0]["uuid"]
            input_uri = f"agave://{prefix}{project_uuid}{path}"
            return input_uri.replace(" ", "%20")

    raise ValueError(f"No matching directory pattern found for: {path}")
