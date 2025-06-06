# dapi/files.py
import os
import urllib.parse

# No JWT needed if we rely on t.username
# import jwt
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
import json
from .exceptions import FileOperationError, AuthenticationError
from typing import List


# _parse_tapis_uri helper remains the same
def _parse_tapis_uri(tapis_uri: str) -> (str, str):
    """Parse a Tapis URI into system ID and path components.

    Args:
        tapis_uri (str): URI in the format 'tapis://system_id/path'.

    Returns:
        tuple: A tuple containing (system_id, path) where path is URL-decoded.

    Raises:
        ValueError: If the URI format is invalid or missing required components.

    Example:
        >>> system_id, path = _parse_tapis_uri("tapis://mysystem/folder/file.txt")
        >>> print(system_id)  # "mysystem"
        >>> print(path)       # "folder/file.txt"
    """
    if not tapis_uri.startswith("tapis://"):
        raise ValueError(
            f"Invalid Tapis URI: '{tapis_uri}'. Must start with 'tapis://'"
        )
    try:
        parsed = urllib.parse.urlparse(tapis_uri)
        system_id = parsed.netloc
        path = parsed.path.lstrip("/") if parsed.path else ""
        if not system_id:
            raise ValueError(f"Invalid Tapis URI: '{tapis_uri}'. Missing system ID.")
        return system_id, path
    except Exception as e:
        raise ValueError(f"Could not parse Tapis URI '{tapis_uri}': {e}") from e


def tapis_uri_to_local_path(tapis_uri: str) -> str:
    """Convert a Tapis URI to the corresponding DesignSafe local path.

    Converts Tapis system URIs back to their equivalent DesignSafe local paths
    that would be accessible in a Jupyter environment. This is the reverse
    operation of get_ds_path_uri().

    Args:
        tapis_uri (str): The Tapis URI to convert. Supported formats:
            - "tapis://designsafe.storage.default/username/path" -> "/home/jupyter/MyData/path"
            - "tapis://designsafe.storage.community/path" -> "/home/jupyter/CommunityData/path"
            - "tapis://project-*/path" -> "/home/jupyter/MyProjects/path"

    Returns:
        str: The corresponding DesignSafe local path, or the original URI if
             it's not a recognized Tapis URI format.

    Raises:
        ValueError: If the Tapis URI format is invalid.

    Example:
        >>> local_path = tapis_uri_to_local_path("tapis://designsafe.storage.default/user/data/file.txt")
        >>> print(local_path)  # "/home/jupyter/MyData/data/file.txt"

        >>> local_path = tapis_uri_to_local_path("tapis://designsafe.storage.community/datasets/earthquake.csv")
        >>> print(local_path)  # "/home/jupyter/CommunityData/datasets/earthquake.csv"
    """
    if not tapis_uri.startswith("tapis://"):
        # Not a Tapis URI, return as-is
        return tapis_uri

    try:
        # Parse the URI using the existing helper function
        system_id, path = _parse_tapis_uri(tapis_uri)

        # Handle different system types
        if system_id == "designsafe.storage.default":
            # For MyData: tapis://designsafe.storage.default/username/path -> /home/jupyter/MyData/path
            # Remove the username (first path component)
            path_parts = path.split("/", 1) if path else [""]
            if len(path_parts) > 1:
                user_path = path_parts[1]
                return f"/home/jupyter/MyData/{user_path}"
            else:
                return "/home/jupyter/MyData/"

        elif system_id == "designsafe.storage.community":
            # For CommunityData: tapis://designsafe.storage.community/path -> /home/jupyter/CommunityData/path
            return (
                f"/home/jupyter/CommunityData/{path}"
                if path
                else "/home/jupyter/CommunityData/"
            )

        elif system_id.startswith("project-"):
            # For Projects: tapis://project-*/path -> /home/jupyter/MyProjects/path
            return (
                f"/home/jupyter/MyProjects/{path}"
                if path
                else "/home/jupyter/MyProjects/"
            )

        else:
            # Unknown system type, return original URI
            return tapis_uri

    except ValueError:
        # Invalid URI format, return original
        return tapis_uri


def get_ds_path_uri(t: Tapis, path: str, verify_exists: bool = False) -> str:
    """Translate DesignSafe-style paths to Tapis URIs.

    Converts commonly used DesignSafe path formats (e.g., /MyData/folder,
    /projects/PRJ-XXXX/folder) to their corresponding Tapis system URIs.
    Supports MyData, CommunityData, and project-specific paths with automatic
    system discovery for projects.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        path (str): The DesignSafe-style path string to translate. Supported formats:
            - MyData paths: "/MyData/folder", "jupyter/MyData/folder"
            - Community paths: "/CommunityData/folder"
            - Project paths: "/projects/PRJ-XXXX/folder"
            - Direct Tapis URIs: "tapis://system-id/path"
        verify_exists (bool, optional): If True, verifies the translated path
            exists on the target Tapis system. Defaults to False.

    Returns:
        str: The corresponding Tapis URI (e.g., "tapis://system-id/path").

    Raises:
        FileOperationError: If path translation fails, project system lookup
            fails, or path verification fails (when verify_exists=True).
        AuthenticationError: If username is required for MyData paths but
            t.username is not available.
        ValueError: If the input path format is unrecognized, empty, or incomplete.

    Example:
        >>> uri = get_ds_path_uri(client, "/MyData/analysis/results")
        Translated '/MyData/analysis/results' to 'tapis://designsafe.storage.default/username/analysis/results' using t.username

        >>> uri = get_ds_path_uri(client, "/projects/PRJ-1234/data", verify_exists=True)
        Searching Tapis systems for project ID 'PRJ-1234'...
        Found unique matching system: project-1234-abcd-ef01-2345-6789abcdef01
        Verifying existence of translated path: tapis://project-1234-abcd-ef01-2345-6789abcdef01/data
        Verification successful: Path exists.
    """
    path = path.strip()
    if not path:
        raise ValueError("Input path cannot be empty.")

    # --- Use t.username directly as per user's working code ---
    current_username = getattr(t, "username", None)
    # ---

    input_uri = None  # Initialize variable

    # 1. Handle MyData variations
    mydata_patterns = [
        # Pattern, Tapis System ID, Use Username in Path?
        ("jupyter/MyData", "designsafe.storage.default", True),
        ("jupyter/mydata", "designsafe.storage.default", True),
        ("/MyData", "designsafe.storage.default", True),
        ("/mydata", "designsafe.storage.default", True),
        ("MyData", "designsafe.storage.default", True),
        ("mydata", "designsafe.storage.default", True),
        ("/home/jupyter/MyData", "designsafe.storage.default", True),
        ("/home/jupyter/mydata", "designsafe.storage.default", True),
    ]
    for pattern, storage_system_id, use_username in mydata_patterns:
        if pattern in path:
            if use_username and not current_username:
                raise AuthenticationError(
                    "Username is required for MyData paths but t.username is not available on the Tapis client."
                )
            path_remainder = path.split(pattern, 1)[1].lstrip("/")
            if use_username:
                tapis_path = (
                    f"{current_username}/{path_remainder}"
                    if path_remainder
                    else current_username
                )
            else:
                tapis_path = path_remainder
            encoded_path = urllib.parse.quote(tapis_path)
            input_uri = f"tapis://{storage_system_id}/{encoded_path}"
            print(f"Translated '{path}' to '{input_uri}' using t.username")
            break  # Found match, exit loop

    # 2. Handle Community variations (if not already matched)
    if input_uri is None:
        community_patterns = [
            ("jupyter/CommunityData", "designsafe.storage.community", False),
            ("/CommunityData", "designsafe.storage.community", False),
            ("CommunityData", "designsafe.storage.community", False),
        ]
        for pattern, storage_system_id, use_username in community_patterns:
            if pattern in path:
                path_remainder = path.split(pattern, 1)[1].lstrip("/")
                tapis_path = path_remainder
                encoded_path = urllib.parse.quote(tapis_path)
                input_uri = f"tapis://{storage_system_id}/{encoded_path}"
                print(f"Translated '{path}' to '{input_uri}'")
                break  # Found match, exit loop

    # 3. Handle Project variations (if not already matched)
    if input_uri is None:
        project_patterns = [
            ("jupyter/MyProjects", "project-"),
            ("jupyter/projects", "project-"),
            ("/projects", "project-"),
            ("projects", "project-"),
            ("/MyProjects", "project-"),
        ]
        for pattern, system_prefix in project_patterns:
            if pattern in path:
                path_remainder_full = path.split(pattern, 1)[1].lstrip("/")
                if not path_remainder_full:
                    raise ValueError(
                        f"Project path '{path}' is incomplete. Missing project ID."
                    )
                parts = path_remainder_full.split("/", 1)
                project_id_part = parts[0]
                path_within_project = parts[1] if len(parts) > 1 else ""

                print(f"Searching Tapis systems for project ID '{project_id_part}'...")
                found_system_id = None
                try:
                    search_query = (
                        f"description.like.%{project_id_part}%&id.like.{system_prefix}*"
                    )
                    systems = t.systems.getSystems(
                        search=search_query,
                        listType="ALL",
                        select="id,owner,description",
                        limit=10,
                    )
                    matches = []
                    if systems:
                        for sys in systems:
                            if (
                                project_id_part.lower()
                                in getattr(sys, "description", "").lower()
                            ):
                                matches.append(sys.id)
                    if len(matches) == 1:
                        found_system_id = matches[0]
                        print(f"Found unique matching system: {found_system_id}")
                    elif len(matches) == 0:
                        if "-" in project_id_part and len(project_id_part) > 30:
                            potential_sys_id = f"{system_prefix}{project_id_part}"
                            print(
                                f"Search failed, attempting direct lookup for system ID: {potential_sys_id}"
                            )
                            try:
                                t.systems.getSystem(
                                    systemId=potential_sys_id, select="id"
                                )  # Select minimal field
                                found_system_id = potential_sys_id
                                print(f"Direct lookup successful: {found_system_id}")
                            except BaseTapyException:
                                print(
                                    f"Direct lookup for {potential_sys_id} also failed."
                                )
                                raise FileOperationError(
                                    f"No project system found matching ID '{project_id_part}' via Tapis v3 search or direct UUID lookup."
                                )
                        else:
                            raise FileOperationError(
                                f"No project system found matching ID '{project_id_part}' via Tapis v3 search."
                            )
                    else:
                        raise FileOperationError(
                            f"Multiple project systems found potentially matching ID '{project_id_part}': {matches}. Cannot determine unique system."
                        )
                except BaseTapyException as e:
                    raise FileOperationError(
                        f"Tapis API error searching for project system '{project_id_part}': {e}"
                    ) from e
                except Exception as e:
                    raise FileOperationError(
                        f"Unexpected error searching for project system '{project_id_part}': {e}"
                    ) from e

                if not found_system_id:
                    raise FileOperationError(
                        f"Could not resolve project ID '{project_id_part}' to a Tapis system ID."
                    )

                encoded_path_within_project = urllib.parse.quote(path_within_project)
                input_uri = f"tapis://{found_system_id}/{encoded_path_within_project}"
                print(f"Translated '{path}' to '{input_uri}' using Tapis v3 lookup")
                break  # Found match, exit loop

    # 4. Handle direct tapis:// URI input (if not already matched)
    if input_uri is None and path.startswith("tapis://"):
        print(f"Path '{path}' is already a Tapis URI.")
        input_uri = path

    # Check if any pattern matched
    if input_uri is None:
        raise ValueError(
            f"Unrecognized DesignSafe path format: '{path}'. Could not translate to Tapis URI."
        )

    # Verification Step
    if verify_exists:
        print(f"Verifying existence of translated path: {input_uri}")
        try:
            system_id, remote_path = _parse_tapis_uri(input_uri)
            # Decode the path part for the listFiles call, as it expects unencoded paths
            decoded_remote_path = urllib.parse.unquote(remote_path)
            print(f"Checking system '{system_id}' for path '{decoded_remote_path}'...")
            # Use limit=1 for efficiency, we only care if it *exists*
            # Note: listFiles might return successfully for the *parent* directory
            # if the final component doesn't exist. A more robust check might
            # involve checking the result count or specific item name, but this
            # basic check catches non-existent parent directories.
            t.files.listFiles(systemId=system_id, path=decoded_remote_path, limit=1)
            print(f"Verification successful: Path exists.")
        except BaseTapyException as e:
            # Specifically check for 404 on the listFiles call
            if hasattr(e, "response") and e.response and e.response.status_code == 404:
                raise FileOperationError(
                    f"Verification failed: Path '{decoded_remote_path}' does not exist on system '{system_id}'. Translated URI: {input_uri}"
                ) from e
            else:
                # Re-raise other Tapis errors encountered during verification
                raise FileOperationError(
                    f"Verification error for path '{decoded_remote_path}' on system '{system_id}': {e}"
                ) from e
        except (
            ValueError
        ) as e:  # Catch errors from _parse_tapis_uri if input_uri was bad
            raise FileOperationError(
                f"Verification failed: Could not parse translated URI '{input_uri}' for verification. Error: {e}"
            ) from e
        except Exception as e:
            # Catch other unexpected errors during verification
            raise FileOperationError(
                f"Unexpected verification error for path at '{input_uri}': {e}"
            ) from e

    return input_uri


def upload_file(t: Tapis, local_path: str, remote_uri: str):
    """Upload a local file to a Tapis storage system.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        local_path (str): Path to the local file to upload.
        remote_uri (str): Tapis URI destination (e.g., "tapis://system/path/file.txt").

    Raises:
        FileNotFoundError: If the local file does not exist.
        ValueError: If local_path is not a file or remote_uri is invalid.
        FileOperationError: If the Tapis upload operation fails.

    Example:
        >>> upload_file(client, "/local/data.txt", "tapis://mysystem/uploads/data.txt")
        Uploading '/local/data.txt' to system 'mysystem' at path 'uploads/data.txt'...
        Upload complete.
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")
    if not os.path.isfile(local_path):
        raise ValueError(f"Local path '{local_path}' is not a file.")
    try:
        system_id, dest_path = _parse_tapis_uri(remote_uri)
        print(
            f"Uploading '{local_path}' to system '{system_id}' at path '{dest_path}'..."
        )
        t.upload(
            system_id=system_id, source_file_path=local_path, dest_file_path=dest_path
        )
        print("Upload complete.")
    except BaseTapyException as e:
        raise FileOperationError(
            f"Tapis upload failed for '{local_path}' to '{remote_uri}': {e}"
        ) from e
    except (ValueError, Exception) as e:
        raise FileOperationError(
            f"Failed to upload file '{local_path}' to '{remote_uri}': {e}"
        ) from e


def download_file(t: Tapis, remote_uri: str, local_path: str):
    """Download a file from a Tapis storage system to local filesystem.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        remote_uri (str): Tapis URI of the file to download (e.g., "tapis://system/path/file.txt").
        local_path (str): Local filesystem path where the file should be saved.

    Raises:
        ValueError: If local_path is a directory or remote_uri is invalid.
        FileOperationError: If the download operation fails or remote file not found.

    Example:
        >>> download_file(client, "tapis://mysystem/data/results.txt", "/local/results.txt")
        Downloading from system 'mysystem' path 'data/results.txt' to '/local/results.txt'...
        Download complete.
    """
    if os.path.isdir(local_path):
        raise ValueError(
            f"Local path '{local_path}' is a directory. Please provide a full file path."
        )
    try:
        system_id, source_path = _parse_tapis_uri(remote_uri)
        print(
            f"Downloading from system '{system_id}' path '{source_path}' to '{local_path}'..."
        )
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)
        # Use getContents which returns the raw bytes
        # Set stream=True for potentially large files
        response = t.files.getContents(
            systemId=system_id, path=source_path, stream=True
        )

        # Write the streamed content to the local file
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):  # Process in chunks
                f.write(chunk)

        print("Download complete.")

    except BaseTapyException as e:
        if hasattr(e, "response") and e.response and e.response.status_code == 404:
            raise FileOperationError(f"Remote file not found at '{remote_uri}'") from e
        else:
            raise FileOperationError(
                f"Tapis download failed for '{remote_uri}': {e}"
            ) from e
    except (ValueError, Exception) as e:
        raise FileOperationError(
            f"Failed to download file from '{remote_uri}' to '{local_path}': {e}"
        ) from e


def list_files(
    t: Tapis, remote_uri: str, limit: int = 100, offset: int = 0
) -> List[Tapis]:
    """List files and directories in a Tapis storage system path.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        remote_uri (str): Tapis URI of the directory to list (e.g., "tapis://system/path/").
        limit (int, optional): Maximum number of items to return. Defaults to 100.
        offset (int, optional): Number of items to skip (for pagination). Defaults to 0.

    Returns:
        List[Tapis]: List of file and directory objects from the specified path.
        Each object contains metadata like name, size, type, and permissions.

    Raises:
        ValueError: If remote_uri is invalid.
        FileOperationError: If the listing operation fails or path not found.

    Example:
        >>> files = list_files(client, "tapis://mysystem/data/")
        Listing files in system 'mysystem' at path 'data/'...
        Found 5 items.
        >>> for file in files:
        ...     print(f"{file.name} ({file.type})")
    """
    try:
        system_id, path = _parse_tapis_uri(remote_uri)
        print(f"Listing files in system '{system_id}' at path '{path}'...")
        results = t.files.listFiles(
            systemId=system_id, path=path, limit=limit, offset=offset
        )
        print(f"Found {len(results)} items.")
        return results
    except BaseTapyException as e:
        if hasattr(e, "response") and e.response and e.response.status_code == 404:
            raise FileOperationError(f"Remote path not found at '{remote_uri}'") from e
        else:
            raise FileOperationError(
                f"Tapis file listing failed for '{remote_uri}': {e}"
            ) from e
    except (ValueError, Exception) as e:
        raise FileOperationError(f"Failed to list files at '{remote_uri}': {e}") from e
