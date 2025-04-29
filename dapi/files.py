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
    """Helper to parse tapis://system_id/path URIs."""
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


def get_ds_path_uri(t: Tapis, path: str, verify_exists: bool = False) -> str:
    """
    Given a path string commonly used in DesignSafe (e.g., /MyData/folder,
    /projects/PRJ-XXXX/folder), determine the correct Tapis system URI.
    Uses the user's provided logic for MyData (relies on t.username) and
    Tapis v3 system search for projects.

    Args:
        t: Authenticated Tapis client.
        path: The DesignSafe-style path string.
        verify_exists: If True, attempts to verify the existence of the
                       translated path on the Tapis system using files.listFiles.
                       Raises FileOperationError if the path does not exist.
                       Defaults to False.

    Returns:
        The corresponding Tapis URI (e.g., tapis://system-id/path).

    Raises:
        FileOperationError: If path translation, project lookup, or path
                            verification (if requested) fails.
        AuthenticationError: If username is needed but t.username is not available.
        ValueError: If the input path format is unrecognized or incomplete.
    """
    path = path.strip()
    if not path:
        raise ValueError("Input path cannot be empty.")

    # --- Use t.username directly as per user's working code ---
    current_username = getattr(t, "username", None)
    # ---

    input_uri = None # Initialize variable

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
                tapis_path = f"{current_username}/{path_remainder}" if path_remainder else current_username
            else:
                tapis_path = path_remainder
            encoded_path = urllib.parse.quote(tapis_path)
            input_uri = f"tapis://{storage_system_id}/{encoded_path}"
            print(f"Translated '{path}' to '{input_uri}' using t.username")
            break # Found match, exit loop

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
                break # Found match, exit loop

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
                    raise ValueError(f"Project path '{path}' is incomplete. Missing project ID.")
                parts = path_remainder_full.split("/", 1)
                project_id_part = parts[0]
                path_within_project = parts[1] if len(parts) > 1 else ""

                print(f"Searching Tapis systems for project ID '{project_id_part}'...")
                found_system_id = None
                try:
                    search_query = f"description.like.%{project_id_part}%&id.like.{system_prefix}*"
                    systems = t.systems.getSystems(search=search_query, listType="ALL", select="id,owner,description", limit=10)
                    matches = []
                    if systems:
                        for sys in systems:
                            if project_id_part.lower() in getattr(sys, "description", "").lower():
                                matches.append(sys.id)
                    if len(matches) == 1:
                        found_system_id = matches[0]
                        print(f"Found unique matching system: {found_system_id}")
                    elif len(matches) == 0:
                        if "-" in project_id_part and len(project_id_part) > 30:
                            potential_sys_id = f"{system_prefix}{project_id_part}"
                            print(f"Search failed, attempting direct lookup for system ID: {potential_sys_id}")
                            try:
                                t.systems.getSystem(systemId=potential_sys_id, select="id") # Select minimal field
                                found_system_id = potential_sys_id
                                print(f"Direct lookup successful: {found_system_id}")
                            except BaseTapyException:
                                print(f"Direct lookup for {potential_sys_id} also failed.")
                                raise FileOperationError(f"No project system found matching ID '{project_id_part}' via Tapis v3 search or direct UUID lookup.")
                        else:
                            raise FileOperationError(f"No project system found matching ID '{project_id_part}' via Tapis v3 search.")
                    else:
                        raise FileOperationError(f"Multiple project systems found potentially matching ID '{project_id_part}': {matches}. Cannot determine unique system.")
                except BaseTapyException as e:
                    raise FileOperationError(f"Tapis API error searching for project system '{project_id_part}': {e}") from e
                except Exception as e:
                    raise FileOperationError(f"Unexpected error searching for project system '{project_id_part}': {e}") from e

                if not found_system_id:
                    raise FileOperationError(f"Could not resolve project ID '{project_id_part}' to a Tapis system ID.")

                encoded_path_within_project = urllib.parse.quote(path_within_project)
                input_uri = f"tapis://{found_system_id}/{encoded_path_within_project}"
                print(f"Translated '{path}' to '{input_uri}' using Tapis v3 lookup")
                break # Found match, exit loop

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
            if hasattr(e, 'response') and e.response and e.response.status_code == 404:
                raise FileOperationError(f"Verification failed: Path '{decoded_remote_path}' does not exist on system '{system_id}'. Translated URI: {input_uri}") from e
            else:
                # Re-raise other Tapis errors encountered during verification
                raise FileOperationError(f"Verification error for path '{decoded_remote_path}' on system '{system_id}': {e}") from e
        except ValueError as e: # Catch errors from _parse_tapis_uri if input_uri was bad
             raise FileOperationError(f"Verification failed: Could not parse translated URI '{input_uri}' for verification. Error: {e}") from e
        except Exception as e:
             # Catch other unexpected errors during verification
            raise FileOperationError(f"Unexpected verification error for path at '{input_uri}': {e}") from e

    return input_uri


def upload_file(t: Tapis, local_path: str, remote_uri: str):
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
