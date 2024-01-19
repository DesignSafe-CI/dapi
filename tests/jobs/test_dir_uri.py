import unittest
from unittest.mock import MagicMock, patch

from dapi.jobs import get_ds_path_uri


class TestGetDsPathUri(unittest.TestCase):
    def setUp(self):
        # Mocking the ag object
        self.ag = MagicMock()

        # Mocking ag.profiles.get() to always return a dict with a specific username
        self.ag.profiles.get.return_value = {"username": "testuser"}

        # Mocking ag.meta.listMetadata to always return a list with a specific uuid
        self.ag.meta.listMetadata.return_value = [{"uuid": "12345"}]

    @patch("os.path.exists", return_value=True)
    def test_directory_patterns(self, mock_path_exists):
        test_cases = [
            (
                "jupyter/MyData/somepath",
                "agave://designsafe.storage.default/testuser/somepath",
            ),
            (
                "/mydata/anotherpath",
                "agave://designsafe.storage.default/testuser/anotherpath",
            ),
            (
                "jupyter/CommunityData/communitypath",
                "agave://designsafe.storage.community//communitypath",
            ),
        ]
        for path, expected in test_cases:
            with self.subTest(path=path):
                self.assertEqual(get_ds_path_uri(self.ag, path), expected)

    @patch("os.path.exists", return_value=True)
    def test_project_patterns(self, mock_path_exists):
        test_cases = [
            ("jupyter/MyProjects/ProjA/subdir", "agave://project-12345/subdir"),
            ("jupyter/projects/ProjB/anotherdir", "agave://project-12345/anotherdir"),
        ]
        for path, expected in test_cases:
            with self.subTest(path=path):
                self.assertEqual(get_ds_path_uri(self.ag, path), expected)

    @patch("os.path.exists", return_value=False)
    def test_no_matching_pattern(self, mock_path_exists):
        with self.assertRaises(ValueError):
            get_ds_path_uri(self.ag, "jupyter/unknownpath/subdir")


if __name__ == "__main__":
    unittest.main()
