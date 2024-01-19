import unittest
from unittest.mock import patch, Mock
from dapi.jobs import get_archive_path


class TestGetArchivePath(unittest.TestCase):
    def test_get_archive_path(self):
        # Create a mock Agave object and its method return value
        mock_ag = Mock()
        mock_job_info = Mock()
        mock_job_info.archivePath = "user123/jobdata/somefile"
        mock_ag.jobs.get.return_value = mock_job_info

        # Call the function
        result = get_archive_path(mock_ag, "dummy_job_id")

        # Check the result
        expected_path = "/home/jupyter/MyData/jobdata/somefile"
        self.assertEqual(result, expected_path)

    def test_get_archive_path_invalid_format(self):
        # Create a mock Agave object with an unexpected format return
        mock_ag = Mock()
        mock_job_info = Mock()
        mock_job_info.archivePath = "invalid_format_path"
        mock_ag.jobs.get.return_value = mock_job_info

        # Check if the function raises a ValueError as expected
        with self.assertRaises(ValueError):
            get_archive_path(mock_ag, "dummy_job_id")


if __name__ == "__main__":
    unittest.main()
