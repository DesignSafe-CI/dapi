# designsafe/components/files/__init__.py
from pathlib import Path
from typing import Optional, List, Union, Dict
from enum import Enum
from dataclasses import dataclass
import os

from ...core import BaseComponent


class StorageSystem(Enum):
    """Enumeration of DesignSafe storage systems."""

    MY_DATA = "designsafe.storage.default"
    COMMUNITY_DATA = "designsafe.storage.community"

    @property
    def base_path(self) -> str:
        """Get the base Jupyter path for this storage system."""
        return {
            StorageSystem.MY_DATA: "jupyter/MyData",
            StorageSystem.COMMUNITY_DATA: "jupyter/CommunityData",
        }[self]


@dataclass
class FileInfo:
    """Information about a file or directory in DesignSafe."""

    name: str
    path: str
    type: str  # 'file' or 'dir'
    size: Optional[int]
    last_modified: str
    uri: str
    permissions: Dict[str, bool]


class FilesComponent(BaseComponent):
    """Component for managing files and directories in DesignSafe."""

    def _get_project_uuid(self, project_id: str) -> str:
        """Get the UUID for a project given its ID.

        Args:
            project_id: The project ID

        Returns:
            The project UUID

        Raises:
            ValueError: If project not found
        """
        try:
            resp = self.tapis.get(
                f"https://designsafe-ci.org/api/projects/v2/{project_id}"
            )
            project_data = resp.json()
            return project_data["baseProject"]["uuid"]
        except Exception as e:
            raise ValueError(f"Error getting project UUID for {project_id}: {str(e)}")

    def get_uri(self, path: str) -> str:
        """Convert a local or Jupyter path to a Tapis URI.

        Args:
            path: Local filesystem or Jupyter path

        Returns:
            Tapis URI for the path

        Examples:
            >>> ds.files.get_uri("jupyter/MyData/test.txt")
            'tapis://designsafe.storage.default/username/test.txt'

            >>> ds.files.get_uri("jupyter/CommunityData/test.txt")
            'tapis://designsafe.storage.community/test.txt'

            >>> ds.files.get_uri("jupyter/MyProjects/PRJ-1234/test.txt")
            'tapis://project-uuid/test.txt'
        """
        path = str(path)  # Convert Path objects to string

        # Handle MyData paths
        if "MyData" in path or "mydata" in path:
            # Extract the relative path after MyData
            rel_path = path.split("MyData/")[-1]
            return f"tapis://{StorageSystem.MY_DATA.value}/{self.tapis.username}/{rel_path}"

        # Handle CommunityData paths
        if "CommunityData" in path:
            rel_path = path.split("CommunityData/")[-1]
            return f"tapis://{StorageSystem.COMMUNITY_DATA.value}/{rel_path}"

        # Handle Project paths
        if "MyProjects" in path or "projects" in path:
            # Extract project ID and relative path
            parts = path.split("/")
            for i, part in enumerate(parts):
                if part in ("MyProjects", "projects"):
                    project_id = parts[i + 1]
                    rel_path = "/".join(parts[i + 2 :])
                    break
            else:
                raise ValueError("Could not parse project path")

            project_uuid = self._get_project_uuid(project_id)
            return f"tapis://project-{project_uuid}/{rel_path}"

        raise ValueError(f"Could not determine storage system for path: {path}")

    def list(self, path: str, recursive: bool = False) -> List[FileInfo]:
        """List contents of a directory.

        Args:
            path: Path to list
            recursive: Whether to list contents recursively

        Returns:
            List of FileInfo objects

        Raises:
            Exception: If listing fails
        """
        uri = self.get_uri(path)

        try:
            system_id, path = uri.replace("tapis://", "").split("/", 1)

            listing = self.tapis.files.listFiles(
                systemId=system_id, path=path, recursive=recursive
            )

            return [
                FileInfo(
                    name=item.name,
                    path=item.path,
                    type="dir" if item.type == "dir" else "file",
                    size=item.size,
                    last_modified=item.lastModified,
                    uri=f"tapis://{system_id}/{item.path}",
                    permissions={
                        "read": item.permissions.read,
                        "write": item.permissions.write,
                        "execute": item.permissions.execute,
                    },
                )
                for item in listing
            ]
        except Exception as e:
            raise Exception(f"Error listing {path}: {str(e)}")

    def upload(
        self, local_path: Union[str, Path], remote_path: str, progress: bool = True
    ) -> FileInfo:
        """Upload a file or directory to DesignSafe.

        Args:
            local_path: Path to local file/directory to upload
            remote_path: Destination path on DesignSafe
            progress: Whether to show progress bar

        Returns:
            FileInfo object for the uploaded file

        Raises:
            FileNotFoundError: If local path doesn't exist
            Exception: If upload fails
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local path not found: {local_path}")

        uri = self.get_uri(remote_path)
        system_id, path = uri.replace("tapis://", "").split("/", 1)

        try:
            result = self.tapis.files.upload(
                systemId=system_id,
                sourcePath=str(local_path),
                targetPath=path,
                progress=progress,
            )

            # Return info about the uploaded file
            return FileInfo(
                name=local_path.name,
                path=path,
                type="dir" if local_path.is_dir() else "file",
                size=local_path.stat().st_size if local_path.is_file() else None,
                last_modified=result.lastModified,
                uri=uri,
                permissions={"read": True, "write": True, "execute": False},
            )
        except Exception as e:
            raise Exception(f"Error uploading {local_path} to {remote_path}: {str(e)}")

    def download(
        self,
        remote_path: str,
        local_path: Optional[Union[str, Path]] = None,
        progress: bool = True,
    ) -> Path:
        """Download a file or directory from DesignSafe.

        Args:
            remote_path: Path on DesignSafe to download
            local_path: Local destination path (default: current directory)
            progress: Whether to show progress bar

        Returns:
            Path to downloaded file/directory

        Raises:
            Exception: If download fails
        """
        uri = self.get_uri(remote_path)
        system_id, path = uri.replace("tapis://", "").split("/", 1)

        # Default to current directory with remote filename
        if local_path is None:
            local_path = Path.cwd() / Path(path).name
        local_path = Path(local_path)

        try:
            self.tapis.files.download(
                systemId=system_id,
                path=path,
                targetPath=str(local_path),
                progress=progress,
            )
            return local_path
        except Exception as e:
            raise Exception(
                f"Error downloading {remote_path} to {local_path}: {str(e)}"
            )

    def delete(self, path: str) -> None:
        """Delete a file or directory.

        Args:
            path: Path to delete

        Raises:
            Exception: If deletion fails
        """
        uri = self.get_uri(path)
        system_id, path = uri.replace("tapis://", "").split("/", 1)

        try:
            self.tapis.files.delete(systemId=system_id, path=path)
        except Exception as e:
            raise Exception(f"Error deleting {path}: {str(e)}")
