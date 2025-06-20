import unittest
from dapi.files import tapis_uri_to_local_path


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

    def test_project_system(self):
        """Test translation of project system URI"""
        input_uri = "tapis://project-1234-abcd/analysis/results.txt"
        expected = "/home/jupyter/MyProjects/analysis/results.txt"
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
        expected = "/home/jupyter/MyProjects/simulation results/output.txt"
        result = tapis_uri_to_local_path(input_uri)
        self.assertEqual(result, expected)


# This allows running the test from the command line
if __name__ == "__main__":
    unittest.main()
