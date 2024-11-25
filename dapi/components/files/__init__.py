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

    def list(
        self, path: str = None, recursive: bool = False, system: str = None
    ) -> List[FileInfo]:
        """List contents of a directory."""
        if system is None:
            system = StorageSystem.MY_DATA.value

        if path is None:
            # Only set default path with username for default storage
            if system == StorageSystem.MY_DATA.value:
                path = f"/{self.tapis.username}"
            else:
                path = "/"
        else:
            path = f"/{path.strip('/')}"
            # Only prepend username for default storage
            if system == StorageSystem.MY_DATA.value and not path.startswith(
                f"/{self.tapis.username}"
            ):
                path = f"/{self.tapis.username}/{path.strip('/')}"

        try:
            listing = self.tapis.files.listFiles(
                systemId=system, path=path, recursive=recursive
            )

            files = [
                FileInfo(
                    name=item.name,
                    path=item.path,
                    type="dir" if getattr(item, "type", None) == "dir" else "file",
                    size=getattr(item, "size", None),
                    last_modified=getattr(item, "lastModified", None),
                    uri=f"tapis://{system}/{item.path}",
                    permissions={"read": True, "write": True, "execute": True},
                )
                for item in listing
            ]

            def format_size(size):
                if size is None:
                    return "N/A"
                for unit in ["B", "KB", "MB", "GB"]:
                    if size < 1024:
                        return f"{size:.1f} {unit}"
                    size /= 1024
                return f"{size:.1f} GB"

            # Format the output as a table
            if files:
                name_width = max(len(f.name) for f in files) + 2
                type_width = 6
                size_width = 10
                date_width = 20

                print(
                    f"{'Name':<{name_width}} {'Type':<{type_width}} {'Size':<{size_width}} {'Last Modified':<{date_width}}"
                )
                print("-" * (name_width + type_width + size_width + date_width + 3))

                for f in sorted(
                    files, key=lambda x: (x.type == "file", x.name.lower())
                ):
                    print(
                        f"{f.name:<{name_width}} "
                        f"{f.type:<{type_width}} "
                        f"{format_size(f.size):<{size_width}} "
                        f"{f.last_modified[:19]}"
                    )

            return files
        except Exception as e:
            raise Exception(f"Error listing {path}: {str(e)}")
