import unittest
from dapi.files import _tapis_uri_to_local_path as tapis_uri_to_local_path


class TestTapisUriToLocalPath(unittest.TestCase):
    """Test cases for the tapis_uri_to_local_path function"""

    def test_designsafe_storage_default_with_path(self):
        """Test translation of designsafe.storage.default URIs with paths"""
        input_uri = "tapis://designsafe.storage.default/kks32/tapis-jobs-archive/2025-06-06Z/80986fb9-0d7e-440a-a4cf-ce54ec26226d-007"
        expected = "/home/jupyter/MyData/tapis-jobs-archive/2025-06-06Z/80986fb9-0d7e-440a-a4cf-ce54ec26226d-007"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_designsafe_storage_default_simple_path(self):
        """Test translation of simple designsafe.storage.default URI"""
        input_uri = "tapis://designsafe.storage.default/user/folder/file.txt"
        expected = "/home/jupyter/MyData/folder/file.txt"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_designsafe_storage_default_root(self):
        """Test translation of designsafe.storage.default root URI"""
        input_uri = "tapis://designsafe.storage.default/kks32/"
        expected = "/home/jupyter/MyData/"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_designsafe_storage_community(self):
        """Test translation of designsafe.storage.community URI"""
        input_uri = "tapis://designsafe.storage.community/datasets/earthquake.csv"
        expected = "/home/jupyter/CommunityData/datasets/earthquake.csv"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_project_system_keeps_uuid_without_client(self):
        """Without a client the project uuid is the directory name, so the
        project identity survives the round trip (the old behavior dropped
        it entirely, pointing every project URI at MyProjects/ itself),
        and a warning states how to get the PRJ directory instead."""
        input_uri = "tapis://project-1234-abcd/analysis/results.txt"
        expected = "/home/jupyter/MyProjects/1234-abcd/analysis/results.txt"
        with self.assertLogs("dapi.files", level="WARNING") as logs:
            result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)
        self.assertIn("ds.files.to_path", logs.output[0])

    def test_project_system_resolves_prj_with_client(self):
        """With a client the uuid resolves to the PRJ directory JupyterHub
        actually mounts under MyProjects."""
        from unittest.mock import patch

        with patch(
            "dapi.projects.resolve_project_id", return_value="PRJ-6379"
        ) as resolver:
            result = tapis_uri_to_local_path(
                "tapis://project-cb94947f-5d05-4df5-9587-ffe89ea427b6/inputs/model.tcl",
                t=object(),
            )
        self.assertEqual(result, "/home/jupyter/MyProjects/PRJ-6379/inputs/model.tcl")
        resolver.assert_called_once()

    def test_project_system_falls_back_when_resolution_fails(self):
        """A failed uuid->PRJ lookup degrades to the uuid directory instead
        of raising: path translation must not hard-fail when a usable
        fallback exists."""
        from unittest.mock import patch

        from dapi.exceptions import FileOperationError

        with patch(
            "dapi.projects.resolve_project_id",
            side_effect=FileOperationError("not found"),
        ):
            result = tapis_uri_to_local_path(
                "tapis://project-1234-abcd/analysis/results.txt", t=object()
            )
        self.assertEqual(
            result, "/home/jupyter/MyProjects/1234-abcd/analysis/results.txt"
        )

    def test_designsafe_storage_published(self):
        """Test translation of designsafe.storage.published URI"""
        input_uri = "tapis://designsafe.storage.published/PRJ-1271/data.csv"
        expected = "/home/jupyter/NHERI-Published/PRJ-1271/data.csv"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_designsafe_storage_published_root(self):
        """Test translation of designsafe.storage.published root URI"""
        input_uri = "tapis://designsafe.storage.published/"
        expected = "/home/jupyter/NHERI-Published/"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_nees_public(self):
        """Test translation of nees.public URI"""
        input_uri = "tapis://nees.public/NEES-2011-1050.groups/data.csv"
        expected = "/home/jupyter/NEES/NEES-2011-1050.groups/data.csv"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_nees_public_root(self):
        """Test translation of nees.public root URI"""
        input_uri = "tapis://nees.public/"
        expected = "/home/jupyter/NEES/"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_unknown_system(self):
        """Test that unknown systems return the original URI"""
        input_uri = "tapis://unknown-system/path/file.txt"
        expected = "tapis://unknown-system/path/file.txt"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_non_tapis_uri(self):
        """Test that non-Tapis URIs are returned unchanged"""
        input_uri = "/local/path/file.txt"
        expected = "/local/path/file.txt"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_empty_path(self):
        """Test handling of URIs with empty paths"""
        input_uri = "tapis://designsafe.storage.default/user"
        expected = "/home/jupyter/MyData/"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_path_with_spaces(self):
        """Test handling of paths with spaces"""
        input_uri = "tapis://designsafe.storage.default/kks32/DS input/file.txt"
        expected = "/home/jupyter/MyData/DS input/file.txt"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_community_path_with_spaces(self):
        """Test handling of community paths with spaces"""
        input_uri = "tapis://designsafe.storage.community/My Dataset/data.csv"
        expected = "/home/jupyter/CommunityData/My Dataset/data.csv"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)

    def test_project_path_with_spaces(self):
        """Test handling of project paths with spaces"""
        input_uri = "tapis://project-1234-abcd/simulation results/output.txt"
        expected = "/home/jupyter/MyProjects/1234-abcd/simulation results/output.txt"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)


# This allows running the test from the command line
if __name__ == "__main__":
    unittest.main()
