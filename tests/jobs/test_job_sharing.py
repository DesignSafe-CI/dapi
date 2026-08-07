import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tapipy.errors import BaseTapyException

from dapi.jobs import (
    JOB_SHARE_RESOURCES,
    SubmittedJob,
    list_jobs,
)


def _make_job(mock_tapis):
    """Build a SubmittedJob with an injected MagicMock Tapis client,
    bypassing __init__'s isinstance check."""
    job = SubmittedJob.__new__(SubmittedJob)
    job._tapis = mock_tapis
    job.uuid = "share-test-uuid-007"
    job._last_status = "FINISHED"
    job._job_details = MagicMock()
    return job


def _mock_tapis(username="testowner"):
    t = MagicMock()
    t.username = username
    return t


class TestShare(unittest.TestCase):
    def test_share_single_user_validates_then_grants(self):
        t = _mock_tapis()
        job = _make_job(t)

        summary = job.share(user_id="parduino")

        t.authenticator.get_profile.assert_called_once_with(username="parduino")
        t.jobs.shareJob.assert_called_once_with(
            jobUuid=job.uuid,
            grantee="parduino",
            jobResource=JOB_SHARE_RESOURCES,
            jobPermission="READ",
        )
        self.assertEqual(summary["grantees"], ["parduino"])
        self.assertEqual(summary["permission"], "READ")

    def test_share_unknown_user_grants_nothing(self):
        t = _mock_tapis()
        t.authenticator.get_profile.side_effect = BaseTapyException("no such user")
        job = _make_job(t)

        with self.assertRaises(ValueError):
            job.share(user_id="no-such-user")
        t.jobs.shareJob.assert_not_called()

    def test_share_user_list_validates_all_before_granting(self):
        t = _mock_tapis()
        # second user is invalid -> nothing at all is granted
        t.authenticator.get_profile.side_effect = [
            MagicMock(),
            BaseTapyException("nope"),
        ]
        job = _make_job(t)

        with self.assertRaises(ValueError):
            job.share(user_id=["parduino", "typo-user"])
        t.jobs.shareJob.assert_not_called()

    @patch("dapi.projects.get_project_users")
    def test_share_project_resolves_members_and_skips_owner(self, mock_users):
        mock_users.return_value = [
            {"username": "parduino", "role": "pi"},
            {"username": "testowner", "role": "co_pi"},  # the job owner
            {"username": "bonusj", "role": "team_member"},
        ]
        t = _mock_tapis(username="testowner")
        job = _make_job(t)

        summary = job.share(project_id="PRJ-1234")

        mock_users.assert_called_once_with(t, "PRJ-1234")
        self.assertEqual(summary["grantees"], ["parduino", "bonusj"])
        self.assertEqual(t.jobs.shareJob.call_count, 2)

    @patch("dapi.projects.get_project_users")
    def test_share_user_and_project_deduplicates(self, mock_users):
        mock_users.return_value = [{"username": "parduino", "role": "pi"}]
        t = _mock_tapis()
        job = _make_job(t)

        summary = job.share(user_id="parduino", project_id="PRJ-1234")

        self.assertEqual(summary["grantees"], ["parduino"])
        self.assertEqual(t.jobs.shareJob.call_count, 1)

    def test_share_requires_user_or_project(self):
        job = _make_job(_mock_tapis())
        with self.assertRaises(ValueError):
            job.share()

    def test_share_rejects_invalid_resource(self):
        t = _mock_tapis()
        job = _make_job(t)
        with self.assertRaises(ValueError):
            job.share(user_id="parduino", resources=["JOB_OUTPUT", "NOT_A_RESOURCE"])
        t.jobs.shareJob.assert_not_called()

    def test_share_only_owner_raises(self):
        t = _mock_tapis(username="testowner")
        job = _make_job(t)
        with self.assertRaises(ValueError):
            job.share(user_id="testowner")
        t.jobs.shareJob.assert_not_called()


class TestUnshareAndShares(unittest.TestCase):
    def test_unshare_revokes_each_user(self):
        t = _mock_tapis()
        job = _make_job(t)

        summary = job.unshare(user_id=["parduino", "bonusj"])

        self.assertEqual(summary["revoked"], ["parduino", "bonusj"])
        self.assertEqual(t.jobs.deleteJobShare.call_count, 2)
        t.jobs.deleteJobShare.assert_any_call(jobUuid=job.uuid, user="parduino")

    def test_shares_returns_dataframe(self):
        t = _mock_tapis()
        t.jobs.getJobShare.return_value = [
            SimpleNamespace(
                grantee="parduino",
                jobResource="JOB_OUTPUT",
                jobPermission="READ",
                created="2026-08-07T12:00:00Z",
                createdby="testowner",
            )
        ]
        job = _make_job(t)

        df = job.shares

        self.assertEqual(list(df["grantee"]), ["parduino"])
        self.assertEqual(list(df["resource"]), ["JOB_OUTPUT"])

    def test_shares_empty(self):
        t = _mock_tapis()
        t.jobs.getJobShare.return_value = []
        job = _make_job(t)
        self.assertTrue(job.shares.empty)


class TestListType(unittest.TestCase):
    def test_list_type_passed_to_tapis(self):
        t = _mock_tapis()
        t.jobs.getJobList.return_value = []

        list_jobs(t, list_type="SHARED_JOBS", output="raw")

        _, kwargs = t.jobs.getJobList.call_args
        self.assertEqual(kwargs["listType"], "SHARED_JOBS")

    def test_list_type_default_and_case_insensitive(self):
        t = _mock_tapis()
        t.jobs.getJobList.return_value = []

        list_jobs(t, output="raw")
        self.assertEqual(t.jobs.getJobList.call_args[1]["listType"], "MY_JOBS")

        list_jobs(t, list_type="shared_jobs", output="raw")
        self.assertEqual(t.jobs.getJobList.call_args[1]["listType"], "SHARED_JOBS")

    def test_invalid_list_type_raises(self):
        with self.assertRaises(ValueError):
            list_jobs(_mock_tapis(), list_type="EVERYTHING")


if __name__ == "__main__":
    unittest.main()
