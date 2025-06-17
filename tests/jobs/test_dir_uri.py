import unittest
from unittest.mock import MagicMock, patch
from dapi.files import get_ds_path_uri
from tapipy.tapis import Tapis


class TestGetDsPathUri(unittest.TestCase):
    def setUp(self):
        # Mocking the Tapis object
        self.t = MagicMock(spec=Tapis)
        self.t.username = "testuser"

        # Correctly mocking the get method
        self.t.get = MagicMock()
        self.t.get.return_value.json.return_value = {"baseProject": {"uuid": "12345"}}

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

    def test_project_patterns(self):
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
        expected = "tapis://designsafe.storage.default/testuser/path%20with%20spaces"
        self.assertEqual(get_ds_path_uri(self.t, path), expected)


if __name__ == "__main__":
    unittest.main()
