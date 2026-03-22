import unittest
from unittest.mock import MagicMock, Mock
from dapi.files import get_ds_path_uri


class TestGetDsPathUri(unittest.TestCase):
    def setUp(self):
        # Use MagicMock without spec so dynamic attributes like .systems work
        self.t = MagicMock()
        self.t.username = "testuser"

        # Mock the systems.getSystems call for project path lookups
        # Return a single matching system for any project query
        mock_system = Mock()
        mock_system.id = "project-12345"
        mock_system.description = "ProjA ProjB project"
        self.t.systems.getSystems.return_value = [mock_system]

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
        expected = "tapis://designsafe.storage.default/testuser/path with spaces"
        self.assertEqual(get_ds_path_uri(self.t, path), expected)


if __name__ == "__main__":
    unittest.main()
