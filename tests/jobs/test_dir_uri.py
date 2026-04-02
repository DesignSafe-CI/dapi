import unittest
from unittest.mock import MagicMock, Mock, patch
from dapi.files import get_ds_path_uri


class TestGetDsPathUri(unittest.TestCase):
    def setUp(self):
        # Use MagicMock without spec so dynamic attributes like .systems work
        self.t = MagicMock()
        self.t.username = "testuser"
        self.t.access_token.access_token = "mock-token"

    def test_directory_patterns(self):
        test_cases = [
            (
                "jupyter/MyData/somepath",
                "tapis://designsafe.storage.default/testuser/somepath",
            ),
            (
                "/mydata/anotherpath",
                "tapis://designsafe.storage.default/testuser/anotherpath",
            ),
            (
                "jupyter/CommunityData/communitypath",
                "tapis://designsafe.storage.community/communitypath",
            ),
            (
                "jupyter/CommunityData//communitypath",  # Test with double slash
                "tapis://designsafe.storage.community/communitypath",
            ),
        ]
        for path, expected in test_cases:
            with self.subTest(path=path):
                self.assertEqual(get_ds_path_uri(self.t, path), expected)

    def test_published_patterns(self):
        test_cases = [
            (
                "/NHERI-Published/PRJ-1271/data.csv",
                "tapis://designsafe.storage.published/PRJ-1271/data.csv",
            ),
            (
                "NHERI-Published/PRJ-1271/",
                "tapis://designsafe.storage.published/PRJ-1271/",
            ),
        ]
        for path, expected in test_cases:
            with self.subTest(path=path):
                self.assertEqual(get_ds_path_uri(self.t, path), expected)

    def test_nees_patterns(self):
        test_cases = [
            (
                "/NEES/NEES-2011-1050.groups/",
                "tapis://nees.public/NEES-2011-1050.groups/",
            ),
            (
                "NEES/somefolder",
                "tapis://nees.public/somefolder",
            ),
        ]
        for path, expected in test_cases:
            with self.subTest(path=path):
                self.assertEqual(get_ds_path_uri(self.t, path), expected)

    @patch("dapi.files._resolve_project_uuid")
    def test_project_patterns(self, mock_resolve):
        mock_resolve.return_value = "project-12345"
        test_cases = [
            ("jupyter/MyProjects/ProjA/subdir", "tapis://project-12345/subdir"),
            ("jupyter/projects/ProjB/anotherdir", "tapis://project-12345/anotherdir"),
        ]
        for path, expected in test_cases:
            with self.subTest(path=path):
                self.assertEqual(get_ds_path_uri(self.t, path), expected)

    def test_no_matching_pattern(self):
        with self.assertRaises(ValueError):
            get_ds_path_uri(self.t, "jupyter/unknownpath/subdir")

    def test_space_in_path(self):
        path = "jupyter/MyData/path with spaces"
        expected = "tapis://designsafe.storage.default/testuser/path with spaces"
        self.assertEqual(get_ds_path_uri(self.t, path), expected)


if __name__ == "__main__":
    unittest.main()
