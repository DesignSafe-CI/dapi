import time
import unittest
from unittest.mock import Mock, patch
import dapi as ds


class TestGetStatus(unittest.TestCase):
    @patch("time.sleep", Mock())  # Mocks the sleep function
    def test_get_status(self):
        # Mock the Agave job object
        mock_agave = Mock()

        # Define behavior for getStatus method
        mock_agave.jobs.getStatus.side_effect = [
            {"status": "PENDING"},
            {"status": "PENDING"},
            {"status": "RUNNING"},
            {"status": "RUNNING"},
            {"status": "FINISHED"},
        ]

        # Define behavior for get method
        # Equivalent to 36 seconds
        mock_agave.jobs.get.return_value = {"maxHours": 0.01}

        # Call get_status
        status = ds.jobs.get_status(mock_agave, "some_job_id", time_lapse=1)

        # Assert that the final status is "FINISHED"
        self.assertEqual(status, "FINISHED")

        # Assert the methods were called the expected number of times
        mock_agave.jobs.getStatus.assert_called_with(jobId="some_job_id")
        self.assertEqual(mock_agave.jobs.getStatus.call_count, 5)
        mock_agave.jobs.get.assert_called_once_with(jobId="some_job_id")


if __name__ == "__main__":
    unittest.main()
