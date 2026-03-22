import unittest
from unittest.mock import Mock, MagicMock

import pandas as pd
from tapipy.errors import BaseTapyException

from dapi.jobs import list_jobs
from dapi.exceptions import JobMonitorError


def _make_job(
    uuid,
    name,
    status,
    app_id,
    app_version="1.0",
    created="2025-06-15T10:00:00.000Z",
    ended="2025-06-15T11:00:00.000Z",
    remote_started="2025-06-15T10:05:00.000Z",
    last_updated="2025-06-15T11:00:00.000Z",
):
    """Create a mock TapisResult job object."""
    job = Mock()
    job.__dict__ = {
        "uuid": uuid,
        "name": name,
        "status": status,
        "appId": app_id,
        "appVersion": app_version,
        "owner": "testuser",
        "created": created,
        "ended": ended,
        "remoteStarted": remote_started,
        "lastUpdated": last_updated,
        "execSystemId": "frontera",
        "archiveSystemId": "designsafe.storage.default",
        "tenant": "designsafe",
    }
    return job


MOCK_JOBS = [
    _make_job("uuid-001", "matlab-run-1", "FINISHED", "matlab-r2023a"),
    _make_job("uuid-002", "opensees-run-1", "FINISHED", "opensees-mp-s3"),
    _make_job("uuid-003", "matlab-run-2", "FAILED", "matlab-r2023a"),
    _make_job(
        "uuid-004",
        "mpm-run-1",
        "RUNNING",
        "mpm-s3",
        ended=None,
        remote_started="2025-06-15T10:10:00.000Z",
    ),
]


class TestListJobs(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.jobs.getJobList.return_value = MOCK_JOBS

    def test_returns_dataframe(self):
        df = list_jobs(self.t)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 4)

    def test_empty_result(self):
        self.t.jobs.getJobList.return_value = []
        df = list_jobs(self.t)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)

    def test_filter_by_app_id(self):
        df = list_jobs(self.t, app_id="matlab-r2023a")
        self.assertEqual(len(df), 2)
        self.assertTrue((df["appId"] == "matlab-r2023a").all())

    def test_filter_by_status(self):
        df = list_jobs(self.t, status="FINISHED")
        self.assertEqual(len(df), 2)
        self.assertTrue((df["status"] == "FINISHED").all())

    def test_filter_by_status_case_insensitive(self):
        df = list_jobs(self.t, status="finished")
        self.assertEqual(len(df), 2)

    def test_combined_filters(self):
        df = list_jobs(self.t, app_id="matlab-r2023a", status="FAILED")
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["uuid"], "uuid-003")

    def test_datetime_columns_exist(self):
        df = list_jobs(self.t)
        for col in [
            "created_dt",
            "created_date",
            "ended_dt",
            "ended_date",
            "remoteStarted_dt",
            "lastUpdated_dt",
        ]:
            self.assertIn(col, df.columns)

    def test_datetime_nat_for_missing(self):
        df = list_jobs(self.t)
        # uuid-004 has ended=None
        mpm_row = df[df["uuid"] == "uuid-004"].iloc[0]
        self.assertTrue(pd.isna(mpm_row["ended_dt"]))

    def test_priority_column_order(self):
        df = list_jobs(self.t)
        expected_first = [
            "name",
            "uuid",
            "status",
            "appId",
            "appVersion",
            "created_dt",
            "ended_dt",
        ]
        actual_first = list(df.columns[: len(expected_first)])
        self.assertEqual(actual_first, expected_first)

    def test_passes_limit_to_api(self):
        list_jobs(self.t, limit=50)
        self.t.jobs.getJobList.assert_called_once_with(
            limit=50, orderBy="created(desc)"
        )

    def test_raises_job_monitor_error_on_api_failure(self):
        self.t.jobs.getJobList.side_effect = BaseTapyException("server error")
        with self.assertRaises(JobMonitorError):
            list_jobs(self.t)

    def test_verbose_prints_count(self):
        # Should not raise
        df = list_jobs(self.t, verbose=True)
        self.assertEqual(len(df), 4)

    def test_index_is_reset(self):
        df = list_jobs(self.t, app_id="matlab-r2023a")
        self.assertEqual(list(df.index), [0, 1])

    def test_no_filter_returns_all(self):
        df = list_jobs(self.t)
        uuids = set(df["uuid"])
        self.assertEqual(uuids, {"uuid-001", "uuid-002", "uuid-003", "uuid-004"})

    # --- output format tests ---

    def test_output_list(self):
        result = list_jobs(self.t, output="list")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)
        self.assertIsInstance(result[0], dict)
        self.assertIn("uuid", result[0])

    def test_output_list_with_filter(self):
        result = list_jobs(self.t, app_id="matlab-r2023a", output="list")
        self.assertEqual(len(result), 2)
        self.assertTrue(all(j["appId"] == "matlab-r2023a" for j in result))

    def test_output_raw(self):
        result = list_jobs(self.t, output="raw")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)
        # Raw returns the original Mock objects
        self.assertNotIsInstance(result[0], dict)

    def test_output_raw_with_filter(self):
        result = list_jobs(self.t, status="RUNNING", output="raw")
        self.assertEqual(len(result), 1)

    def test_output_empty_list(self):
        self.t.jobs.getJobList.return_value = []
        self.assertEqual(list_jobs(self.t, output="list"), [])
        self.assertEqual(list_jobs(self.t, output="raw"), [])

    def test_invalid_output_raises(self):
        with self.assertRaises(ValueError):
            list_jobs(self.t, output="xml")


if __name__ == "__main__":
    unittest.main()
