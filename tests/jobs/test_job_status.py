import unittest
from unittest.mock import Mock, patch
import dapi as ds


class TestGetStatus(unittest.TestCase):
    @patch("time.sleep", Mock())  # Mocks the sleep function
    def test_get_status(self):
        # Mock the Tapis client object
        mock_tapis = Mock()

        # Define behavior for getJobStatus method
        mock_tapis.jobs.getJobStatus.side_effect = [
            Mock(status="PENDING"),
            Mock(status="PENDING"),
            Mock(status="RUNNING"),
            Mock(status="RUNNING"),
            Mock(status="FINISHED"),
        ]

        # Define behavior for getJob method
        mock_tapis.jobs.getJob.return_value = Mock(maxMinutes=1)

        # Call get_status
        status = ds.jobs.get_status(mock_tapis, "some_job_uuid", tlapse=1)

        # Assert that the final status is "FINISHED"
        self.assertEqual(status, "FINISHED")

        # Assert the methods were called the expected number of times
        mock_tapis.jobs.getJobStatus.assert_called_with(jobUuid="some_job_uuid")
        self.assertEqual(mock_tapis.jobs.getJobStatus.call_count, 5)
        mock_tapis.jobs.getJob.assert_called_once_with(jobUuid="some_job_uuid")

    @patch("time.sleep", Mock())
    def test_get_status_timeout(self):
        # Mock the Tapis client object
        mock_tapis = Mock()

        # Define behavior for getJobStatus method to simulate a job that doesn't finish
        mock_tapis.jobs.getJobStatus.return_value = Mock(status="RUNNING")

        # Define behavior for getJob method
        mock_tapis.jobs.getJob.return_value = Mock(maxMinutes=1)

        # Call get_status
        status = ds.jobs.get_status(mock_tapis, "some_job_uuid", tlapse=1)

        # Assert that the final status is still "RUNNING" due to timeout
        self.assertEqual(status, "RUNNING")

        # Assert the methods were called the expected number of times
        expected_calls = 60  # 1 minute = 60 seconds, with tlapse=1
        self.assertGreaterEqual(mock_tapis.jobs.getJobStatus.call_count, expected_calls)
        mock_tapis.jobs.getJob.assert_called_once_with(jobUuid="some_job_uuid")


if __name__ == "__main__":
    unittest.main()
