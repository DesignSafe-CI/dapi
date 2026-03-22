import unittest
from unittest.mock import Mock, patch, MagicMock
import dapi as ds


class TestGetStatus(unittest.TestCase):
    @patch("dapi.jobs.SubmittedJob")
    def test_get_status(self, mock_submitted_job_cls):
        mock_tapis = Mock()

        # Set up the mock SubmittedJob instance
        mock_job_instance = MagicMock()
        mock_job_instance.get_status.return_value = "FINISHED"
        mock_submitted_job_cls.return_value = mock_job_instance

        # Call get_job_status (no tlapse parameter)
        status = ds.jobs.get_job_status(mock_tapis, "some_job_uuid")

        # Assert that the final status is "FINISHED"
        self.assertEqual(status, "FINISHED")

        # Assert SubmittedJob was created with the right arguments
        mock_submitted_job_cls.assert_called_once_with(mock_tapis, "some_job_uuid")
        mock_job_instance.get_status.assert_called_once_with(force_refresh=True)

    @patch("dapi.jobs.SubmittedJob")
    def test_get_status_running(self, mock_submitted_job_cls):
        mock_tapis = Mock()

        # Set up the mock SubmittedJob instance to return RUNNING
        mock_job_instance = MagicMock()
        mock_job_instance.get_status.return_value = "RUNNING"
        mock_submitted_job_cls.return_value = mock_job_instance

        # Call get_job_status
        status = ds.jobs.get_job_status(mock_tapis, "some_job_uuid")

        # Assert that the status is "RUNNING"
        self.assertEqual(status, "RUNNING")

        # Assert the SubmittedJob was created correctly
        mock_submitted_job_cls.assert_called_once_with(mock_tapis, "some_job_uuid")
        mock_job_instance.get_status.assert_called_once_with(force_refresh=True)


if __name__ == "__main__":
    unittest.main()
