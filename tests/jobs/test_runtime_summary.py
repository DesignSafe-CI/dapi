import unittest
from unittest.mock import Mock
from io import StringIO
import sys
from datetime import datetime, timedelta
import re

import dapi as ds


class TestRuntimeSummary(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.t_mock = Mock()
        start_time = datetime(2024, 9, 30, 14, 0, 0)  # Use a fixed start time
        self.job_history = [
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="PENDING",
                created=start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="PROCESSING_INPUTS",
                created=(start_time + timedelta(seconds=3)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="STAGING_INPUTS",
                created=(start_time + timedelta(seconds=7)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="STAGED",
                created=(start_time + timedelta(seconds=11)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="STAGING_JOB",
                created=(start_time + timedelta(seconds=18)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="SUBMITTING",
                created=(start_time + timedelta(seconds=30)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="QUEUED",
                created=(start_time + timedelta(seconds=48)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="RUNNING",
                created=(start_time + timedelta(minutes=1, seconds=12)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="CLEANING_UP",
                created=(start_time + timedelta(minutes=2, seconds=36)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="ARCHIVING",
                created=(start_time + timedelta(minutes=2, seconds=36)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
            Mock(
                event="JOB_NEW_STATUS",
                eventDetail="FINISHED",
                created=(start_time + timedelta(minutes=2, seconds=48)).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            ),
        ]

    def capture_output(self, t_mock, job_id, verbose):
        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            ds.jobs.runtime_summary(t_mock, job_id, verbose)
            return out.getvalue().strip()
        finally:
            sys.stdout = saved_stdout

    def test_runtime_summary_verbose_true(self):
        self.t_mock.jobs.getJobHistory.return_value = self.job_history
        output = self.capture_output(self.t_mock, "mock_id", True)

        # Check the structure of the output without relying on exact timestamps
        self.assertIn("Runtime Summary", output)
        self.assertIn("---------------", output)
        self.assertIn("Detailed Job History:", output)

        # Check that all event details are present
        for event in self.job_history:
            self.assertIn(f"Event: {event.event}, Detail: {event.eventDetail}", output)

        # Check the summary section
        self.assertIn("Summary:", output)
        self.assertRegex(output, r"QUEUED\s+time: 00:00:24")
        self.assertRegex(output, r"RUNNING\s+time: 00:01:24")
        self.assertRegex(output, r"TOTAL\s+time: 00:02:48")

    def test_runtime_summary_verbose_false(self):
        self.t_mock.jobs.getJobHistory.return_value = self.job_history
        output = self.capture_output(self.t_mock, "mock_id", False)

        # Check the overall structure
        self.assertIn("Runtime Summary", output)
        self.assertIn("---------------", output)

        # Check for the presence of each status and its time
        self.assertRegex(output, r"QUEUED\s+time:\s+00:00:24")
        self.assertRegex(output, r"RUNNING\s+time:\s+00:01:24")
        self.assertRegex(output, r"TOTAL\s+time:\s+00:02:48")

        # Check the order of the statuses
        status_order = ["QUEUED", "RUNNING", "TOTAL"]
        status_indices = [output.index(status) for status in status_order]
        self.assertEqual(
            status_indices,
            sorted(status_indices),
            "Statuses are not in the expected order",
        )


if __name__ == "__main__":
    unittest.main()
