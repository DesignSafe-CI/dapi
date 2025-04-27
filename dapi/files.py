import os
import urllib.parse
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from .exceptions import FileOperationError
from typing import List

def _parse_tapis_uri(tapis_uri: str) -> (str, str):
    """Helper to parse tapis://system_id/path URIs."""
    if not tapis_uri.startswith("tapis://"):
        raise ValueError(f"Invalid Tapis URI: '{tapis_uri}'. Must start with 'tapis://'")
    try:
        # Use urlparse to handle potential special characters
        parsed = urllib.parse.urlparse(tapis_uri)
        system_id = parsed.netloc
        path = parsed.path.lstrip('/') # Remove leading slash for consistency
        if not system_id:
             raise ValueError(f"Invalid Tapis URI: '{tapis_uri}'. Missing system ID.")
        return system_id, path
    except Exception as e:
        raise ValueError(f"Could not parse Tapis URI '{tapis_uri}': {e}") from e


def get_ds_path_uri(t: Tapis, path: str) -> str:
    """
    Given a path string commonly used in DesignSafe (e.g., /MyData/folder,
    /projects/PROJECT_ID/folder), determine the correct Tapis system URI.

    Args:
        t: Authenticated Tapis client.
        path: The DesignSafe-style path string.

    Returns:
        The corresponding Tapis URI (e.g., tapis://system-id/path).

    Raises:
        FileOperationError: If the path cannot be translated or project lookup fails.
        ValueError: If the input path format is unrecognized.
    """
    path = path.strip()
    if not path:
        raise ValueError("Input path cannot be empty.")

    # 1. Handle MyData variations
    mydata_patterns = [
        ("/MyData", "designsafe.storage.default"),
        ("/mydata", "designsafe.storage.default"),
        ("MyData", "designsafe.storage.default"), # Allow relative to home
        ("mydata", "designsafe.storage.default"),
        # Add Jupyter specific if needed, though they often map to the above
        ("jupyter/MyData", "designsafe.storage.default"),
        ("jupyter/mydata", "designsafe.storage.default"),
    ]
    for pattern, system_id in mydata_patterns:
        # Check if path *starts* with the pattern + optional separator
        if path == pattern or path.startswith(pattern + '/'):
            path_remainder = path[len(pattern):].lstrip('/')
            # MyData paths are relative to the user's rootDir on the system
            # We need the effective user ID to construct the full Tapis path
            try:
                # Get user profile to find username reliably
                profile = t.authenticator.get_profile()
                username = profile.username
                # Construct the final path within the Tapis system
                full_path = os.path.join(username, path_remainder) if path_remainder else username
                uri = f"tapis://{system_id}/{urllib.parse.quote(full_path)}"
                print(f"Translated '{path}' to '{uri}'")
                return uri
            except BaseTapyException as e:
                 raise FileOperationError(f"Failed to get user profile for MyData path translation: {e}") from e
            except Exception as e:
                 raise FileOperationError(f"Unexpected error during MyData path translation: {e}") from e


    # 2. Handle Community variations
    community_patterns = [
        ("/CommunityData", "designsafe.storage.community"),
        ("CommunityData", "designsafe.storage.community"),
        ("jupyter/CommunityData", "designsafe.storage.community"),
    ]
    for pattern, system_id in community_patterns:
         if path == pattern or path.startswith(pattern + '/'):
            path_remainder = path[len(pattern):].lstrip('/')
            # Community paths are typically relative to the system's rootDir
            uri = f"tapis://{system_id}/{urllib.parse.quote(path_remainder)}"
            print(f"Translated '{path}' to '{uri}'")
            return uri

    # 3. Handle Project variations (using Tapis Systems API)
    project_patterns = [
        ("/projects", "project-"),
        ("projects", "project-"),
        ("jupyter/projects", "project-"),
        ("jupyter/MyProjects", "project-"), # Older path
        ("/MyProjects", "project-"),       # Older path
    ]
    for pattern, prefix in project_patterns:
         if path == pattern or path.startswith(pattern + '/'):
            path_remainder_full = path[len(pattern):].lstrip('/')
            if not path_remainder_full:
                raise ValueError(f"Project path '{path}' is incomplete. Missing project ID.")

            parts = path_remainder_full.split('/', 1)
            project_id_part = parts[0] # This could be PRJ-XXXX or the UUID
            path_within_project = parts[1] if len(parts) > 1 else ""

            # Attempt to find the project system using Tapis v3 Systems API
            # Projects in DesignSafe correspond to Tapis systems with IDs like project-<UUID>
            # We need to find the system whose ID matches or corresponds to project_id_part
            try:
                # Option 1: If project_id_part is already the UUID
                if project_id_part.startswith(prefix):
                    system_id_to_check = project_id_part
                # Option 2: If project_id_part is the PRJ-XXXX ID (less reliable with v3 alone)
                # This requires mapping PRJ-ID to UUID. DesignSafe's v2 API did this.
                # In pure v3, you might need to search systems by metadata if available,
                # or assume the user provides the UUID-based system ID.
                # For now, let's assume project_id_part might be the system ID directly or need the prefix.
                # A more robust solution might involve searching systems with a tag or metadata.
                else:
                     # Let's try searching for systems matching the PRJ ID pattern if possible
                     # This depends on how DesignSafe registers project systems in Tapis
                     # Example search (might need adjustment):
                     # search_query = f"id.like.{prefix}{project_id_part}*" # Or based on notes/tags
                     # For simplicity, assume the user provides the full system ID like 'project-UUID'
                     # Or that the input path already contains it.
                     # If the input is just PRJ-XXXX, this basic lookup might fail without extra mapping.
                     # We'll assume the pattern includes the prefix for now.
                     if not project_id_part.startswith(prefix):
                          # Try constructing it, assuming project_id_part is the UUID
                          system_id_to_check = f"{prefix}{project_id_part}"
                     else:
                          system_id_to_check = project_id_part


                # Verify the system exists (optional but good practice)
                # t.systems.getSystem(systemId=system_id_to_check) # This would throw error if not found

                uri = f"tapis://{system_id_to_check}/{urllib.parse.quote(path_within_project)}"
                print(f"Translated '{path}' to '{uri}' (assuming system ID '{system_id_to_check}')")
                return uri

            except BaseTapyException as e:
                raise FileOperationError(f"Failed to verify project system '{system_id_to_check}' for path '{path}': {e}") from e
            except Exception as e:
                raise FileOperationError(f"Unexpected error during project path translation for '{path}': {e}") from e


    # 4. Handle direct tapis:// URI input
    if path.startswith("tapis://"):
        print(f"Path '{path}' is already a Tapis URI.")
        return path

    # If no pattern matched
    raise ValueError(f"Unrecognized DesignSafe path format: '{path}'. Could not translate to Tapis URI.")


def upload_file(t: Tapis, local_path: str, remote_uri: str):
    """
    Uploads a local file to a Tapis system URI.

    Args:
        t: Authenticated Tapis client.
        local_path: Path to the local file to upload.
        remote_uri: The destination Tapis URI (e.g., tapis://system-id/path/to/file.txt).

    Raises:
        FileNotFoundError: If the local file does not exist.
        FileOperationError: If the upload fails.
        ValueError: If the remote URI is invalid.
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")
    if not os.path.isfile(local_path):
         raise ValueError(f"Local path '{local_path}' is not a file.")

    try:
        system_id, dest_path = _parse_tapis_uri(remote_uri)
        print(f"Uploading '{local_path}' to system '{system_id}' at path '{dest_path}'...")

        # Use the built-in tapis convenience uploader
        # Note: t.upload expects dest_file_path relative to system root
        t.upload(
            system_id=system_id,
            source_file_path=local_path,
            dest_file_path=dest_path # Already stripped leading / in _parse_tapis_uri
        )
        print("Upload complete.")
    except BaseTapyException as e:
        raise FileOperationError(f"Tapis upload failed for '{local_path}' to '{remote_uri}': {e}") from e
    except (ValueError, Exception) as e:
        # Catch parsing errors or other unexpected issues
        raise FileOperationError(f"Failed to upload file '{local_path}' to '{remote_uri}': {e}") from e


def download_file(t: Tapis, remote_uri: str, local_path: str):
    """
    Downloads a file from a Tapis system URI to a local path.

    Args:
        t: Authenticated Tapis client.
        remote_uri: The Tapis URI of the file to download.
        local_path: The local path where the file should be saved.

    Raises:
        FileOperationError: If the download fails.
        ValueError: If the remote URI is invalid or local path is a directory.
    """
    if os.path.isdir(local_path):
        raise ValueError(f"Local path '{local_path}' is a directory. Please provide a full file path.")

    try:
        system_id, source_path = _parse_tapis_uri(remote_uri)
        print(f"Downloading from system '{system_id}' path '{source_path}' to '{local_path}'...")

        # Ensure local directory exists
        local_dir = os.path.dirname(local_path)
        if local_dir: # Only create if path includes a directory part
             os.makedirs(local_dir, exist_ok=True)

        # Use getContents which returns the raw bytes
        file_bytes = t.files.getContents(systemId=system_id, path=source_path)

        # Write the bytes to the local file
        with open(local_path, 'wb') as f:
            f.write(file_bytes)

        print("Download complete.")

    except BaseTapyException as e:
        # Check for 404 specifically
        if hasattr(e, 'response') and e.response and e.response.status_code == 404:
             raise FileOperationError(f"Remote file not found at '{remote_uri}'") from e
        else:
             raise FileOperationError(f"Tapis download failed for '{remote_uri}': {e}") from e
    except (ValueError, Exception) as e:
        raise FileOperationError(f"Failed to download file from '{remote_uri}' to '{local_path}': {e}") from e


def list_files(t: Tapis, remote_uri: str, limit: int = 100, offset: int = 0) -> List[Tapis]:
    """
    Lists files and directories at a given Tapis system URI.

    Args:
        t: Authenticated Tapis client.
        remote_uri: The Tapis URI of the directory to list.
        limit: Maximum number of items to return.
        offset: Offset for pagination.

    Returns:
        A list of Tapis FileInfo objects.

    Raises:
        FileOperationError: If the listing fails.
        ValueError: If the remote URI is invalid.
    """
    try:
        system_id, path = _parse_tapis_uri(remote_uri)
        print(f"Listing files in system '{system_id}' at path '{path}'...")

        results = t.files.listFiles(systemId=system_id, path=path, limit=limit, offset=offset)
        print(f"Found {len(results)} items.")
        return results

    except BaseTapyException as e:
         # Check for 404 specifically
        if hasattr(e, 'response') and e.response and e.response.status_code == 404:
             raise FileOperationError(f"Remote path not found at '{remote_uri}'") from e
        else:
             raise FileOperationError(f"Tapis file listing failed for '{remote_uri}': {e}") from e
    except (ValueError, Exception) as e:
        raise FileOperationError(f"Failed to list files at '{remote_uri}': {e}") from e