import os
import tempfile
import unittest
from unittest import mock

from dapi.client import ParametricSweepMethods


class _StubFiles:
    def __init__(self):
        self.mkdirs = []

    def mkdir(self, systemId, path):
        self.mkdirs.append((systemId, path))


class _StubTapis:
    def __init__(self):
        self.files = _StubFiles()


class TestSweepLocalUpload(unittest.TestCase):
    """parametric_sweep.submit uploads local-only directories before submitting."""

    def _translate(self, tapis, path):
        if path.startswith("/MyData"):
            return "tapis://designsafe.storage.default/user1" + path[len("/MyData") :]
        raise ValueError(f"Unrecognized DesignSafe path format: '{path}'")

    def test_local_directory_is_uploaded_and_submitted_from_tapis_uri(self):
        sweep = ParametricSweepMethods(_StubTapis())
        with tempfile.TemporaryDirectory() as d:
            staged = os.path.join(d, "staged")
            os.makedirs(staged)
            for name in ("runsList.txt", "call_pylauncher.py"):
                with open(os.path.join(staged, name), "w") as f:
                    f.write("x\n")

            uploads = []
            with (
                mock.patch(
                    "dapi.client.files_module.get_ds_path_uri",
                    side_effect=self._translate,
                ),
                mock.patch(
                    "dapi.client.files_module.upload_file",
                    side_effect=lambda t, local, remote: uploads.append(remote),
                ),
                mock.patch(
                    "dapi.client.jobs_module.generate_job_request",
                    side_effect=lambda **kw: kw,
                ),
                mock.patch(
                    "dapi.client.jobs_module.submit_job_request",
                    side_effect=lambda t, req: req,
                ),
            ):
                req = sweep.submit(staged, app_id="python-s3", allocation="TEST")

            expected_uri = (
                "tapis://designsafe.storage.default/user1/dapi-staging/staged"
            )
            self.assertEqual(req["input_dir_uri"], expected_uri)
            self.assertEqual(len(uploads), 2)
            for remote in uploads:
                self.assertTrue(remote.startswith(expected_uri + "/"))

    def test_designsafe_path_is_translated_without_upload(self):
        sweep = ParametricSweepMethods(_StubTapis())
        with (
            mock.patch(
                "dapi.client.files_module.get_ds_path_uri",
                side_effect=self._translate,
            ),
            mock.patch("dapi.client.files_module.upload_file") as up,
            mock.patch(
                "dapi.client.jobs_module.generate_job_request",
                side_effect=lambda **kw: kw,
            ),
            mock.patch(
                "dapi.client.jobs_module.submit_job_request",
                side_effect=lambda t, req: req,
            ),
        ):
            req = sweep.submit("/MyData/sweep", app_id="python-s3", allocation="TEST")

        self.assertEqual(
            req["input_dir_uri"], "tapis://designsafe.storage.default/user1/sweep"
        )
        up.assert_not_called()

    def test_missing_local_directory_still_raises(self):
        sweep = ParametricSweepMethods(_StubTapis())
        with mock.patch(
            "dapi.client.files_module.get_ds_path_uri",
            side_effect=self._translate,
        ):
            with self.assertRaises(ValueError):
                sweep.submit("/no/such/dir", app_id="python-s3", allocation="TEST")


if __name__ == "__main__":
    unittest.main()
