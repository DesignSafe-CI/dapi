# designsafe/components/files/__init__.py
from pathlib import Path
from typing import Optional, List, Union, Dict
from enum import Enum
from dataclasses import dataclass
import os

from ...core import BaseComponent


class StorageSystem(Enum):
    """Enumeration of available storage systems."""

    MY_DATA = "designsafe.storage.default"
    COMMUNITY = "designsafe.storage.community"
    PUBLISHED = "designsafe.storage.published"
    FRONTERA = "frontera.storage.default"
    LS6 = "ls6.storage.default"


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

    def get_storage_info(self, path: str) -> tuple[str, str]:
        """
        Determine storage system and processed path based on path patterns.

        Args:
            path (str): Input path

        Returns:
            tuple: (storage_id, processed_path)

        Raises:
            ValueError: If no matching pattern is found
        """
        # Define directory patterns and their corresponding storage systems
        directory_patterns = [
            ("jupyter/MyData", "designsafe.storage.default", True),
            ("jupyter/mydata", "designsafe.storage.default", True),
            ("jupyter/CommunityData", "designsafe.storage.community", False),
            ("/MyData", "designsafe.storage.default", True),
            ("/mydata", "designsafe.storage.default", True),
        ]

        # Check standard directory patterns
        for pattern, storage, use_username in directory_patterns:
            if pattern in path:
                processed_path = path.split(pattern, 1)[1].lstrip("/")
                if use_username and not processed_path.startswith(self.tapis.username):
                    processed_path = f"{self.tapis.username}/{processed_path}"
                return storage, processed_path

        # Check project patterns
        project_patterns = [
            ("jupyter/MyProjects", "project-"),
            ("jupyter/projects", "project-"),
        ]

        for pattern, prefix in project_patterns:
            if pattern in path:
                path = path.split(pattern, 1)[1].lstrip("/")
                project_id, *rest = path.split("/", 1)
                remaining_path = rest[0] if rest else ""

                # Get project UUID
                try:
                    resp = self.tapis.get(
                        f"https://designsafe-ci.org/api/projects/v2/{project_id}"
                    )
                    project_uuid = resp.json()["baseProject"]["uuid"]
                    return f"{prefix}{project_uuid}", remaining_path
                except Exception as e:
                    raise ValueError(f"Could not resolve project UUID: {str(e)}")

        raise ValueError(f"No matching directory pattern found for: {path}")

    def get_uri(self, path: str, system: Optional[str] = None) -> str:
        """
        Convert a path to a Tapis URI.

        Args:
            path (str): Path to convert
            system (str, optional): Storage system to use (ignored as system is determined by path)

        Returns:
            str: Tapis URI for the given path

        Raises:
            ValueError: If path pattern is not recognized
        """
        storage_id, processed_path = self.get_storage_info(path)
        return f"tapis://{storage_id}/{processed_path}".replace(" ", "%20")

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
