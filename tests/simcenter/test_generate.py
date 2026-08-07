import unittest
from unittest.mock import MagicMock, Mock, patch

from dapi.jobs import generate_job_request


def _make_mock_app(app_id, declare_inputs=False):
    """Mock app details. With declare_inputs=False this mirrors the real
    simcenter-uq-stampede3 definition: empty parameterSet and fileInputs."""
    app = MagicMock()
    app.id = app_id
    app.version = "2.0.0"
    app.description = f"{app_id} test app"

    job_attrs = MagicMock()
    job_attrs.execSystemId = "stampede3"
    job_attrs.archiveSystemId = "designsafe.storage.default"
    job_attrs.archiveSystemDir = None
    job_attrs.archiveOnAppError = True
    job_attrs.execSystemLogicalQueue = "skx-dev"
    job_attrs.nodeCount = 2
    job_attrs.coresPerNode = 4
    job_attrs.maxMinutes = 120
    job_attrs.memoryMB = 192000
    job_attrs.isMpi = False
    param_set = Mock()
    param_set.appArgs = []
    param_set.envVariables = []
    param_set.schedulerOptions = []
    job_attrs.parameterSet = param_set
    if declare_inputs:
        fi = Mock()
        fi.name = "Input Directory"
        fi.targetPath = None
        fi.autoMountLocal = True
        job_attrs.fileInputs = [fi]
    else:
        job_attrs.fileInputs = []
    app.jobAttributes = job_attrs
    return app


class TestSimCenterProfileInGenerate(unittest.TestCase):
    """generate_job_request must apply the SimCenter app profile
    automatically when the app id matches simcenter-*."""

    def setUp(self):
        self.mock_tapis = MagicMock()
        self.mock_tapis.username = "testuser"
        self.input_uri = "tapis://designsafe.storage.default/testuser/DS_input"

    @patch("dapi.jobs.get_app_details")
    def test_simcenter_app_gets_wrapper_contract(self, mock_get_app):
        mock_get_app.return_value = _make_mock_app("simcenter-uq-stampede3")

        job_req = generate_job_request(
            tapis_client=self.mock_tapis,
            app_id="simcenter-uq-stampede3",
            input_dir_uri=self.input_uri,
            allocation="TEST-ALLOC",
            queue="skx-dev",
            node_count=1,
            cores_per_node=48,
            memory_mb=128000,
            max_minutes=120,
        )

        main_input = job_req["fileInputs"][0]
        self.assertEqual(main_input["envKey"], "inputDirectory")
        self.assertEqual(main_input["targetPath"], "*")
        self.assertEqual(main_input["sourceUrl"], self.input_uri)

        env_vars = {
            v["key"]: v["value"] for v in job_req["parameterSet"]["envVariables"]
        }
        self.assertEqual(env_vars["inputFile"], "scInput.json")
        self.assertEqual(env_vars["driverFile"], "driver")

        sched_args = [s["arg"] for s in job_req["parameterSet"]["schedulerOptions"]]
        self.assertIn("-A TEST-ALLOC", sched_args)

        self.assertEqual(job_req["nodeCount"], 1)
        self.assertEqual(job_req["coresPerNode"], 48)
        self.assertEqual(job_req["memoryMB"], 128000)

    @patch("dapi.jobs.get_app_details")
    def test_non_simcenter_app_untouched(self, mock_get_app):
        mock_get_app.return_value = _make_mock_app(
            "opensees-mp-s3", declare_inputs=True
        )

        job_req = generate_job_request(
            tapis_client=self.mock_tapis,
            app_id="opensees-mp-s3",
            input_dir_uri=self.input_uri,
        )

        main_input = job_req["fileInputs"][0]
        self.assertNotIn("envKey", main_input)
        env_vars = job_req.get("parameterSet", {}).get("envVariables", [])
        keys = {v["key"] for v in env_vars}
        self.assertNotIn("inputFile", keys)
        self.assertNotIn("driverFile", keys)

    @patch("dapi.jobs.get_app_details")
    def test_user_env_vars_override_profile_defaults(self, mock_get_app):
        mock_get_app.return_value = _make_mock_app("simcenter-uq-stampede3")

        job_req = generate_job_request(
            tapis_client=self.mock_tapis,
            app_id="simcenter-uq-stampede3",
            input_dir_uri=self.input_uri,
            extra_env_vars=[
                {"key": "inputFile", "value": "myInput.json"},
                {"key": "customVar", "value": "42"},
            ],
        )

        env_vars = job_req["parameterSet"]["envVariables"]
        keys = [v["key"] for v in env_vars]
        self.assertEqual(keys.count("inputFile"), 1)
        by_key = {v["key"]: v["value"] for v in env_vars}
        self.assertEqual(by_key["inputFile"], "myInput.json")
        self.assertEqual(by_key["customVar"], "42")
        self.assertEqual(by_key["driverFile"], "driver")


if __name__ == "__main__":
    unittest.main()
