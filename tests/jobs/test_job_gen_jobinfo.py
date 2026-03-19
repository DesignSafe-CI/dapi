import unittest
from unittest.mock import Mock, patch
from dapi.jobs import generate_job_request
from datetime import datetime


def _make_app_arg(name, arg="", input_mode="INCLUDE_ON_DEMAND"):
    """Create a mock app arg with a real .name attribute."""
    m = Mock()
    m.name = name
    m.arg = arg
    m.inputMode = input_mode
    return m


def _make_env_var(key, value="", input_mode="INCLUDE_ON_DEMAND"):
    """Create a mock env var with a real .key attribute."""
    m = Mock()
    m.key = key
    m.value = value
    m.inputMode = input_mode
    return m


def _make_file_input(name, target_path=None, auto_mount=True):
    """Create a mock file input definition."""
    m = Mock()
    m.name = name
    m.targetPath = target_path
    m.autoMountLocal = auto_mount
    return m


class TestGenerateJobInfo(unittest.TestCase):
    def setUp(self):
        self.t_mock = Mock()
        self.app_name = "test-app"
        self.input_uri = "tapis://test-system/input/data"
        self.input_file = "input.txt"

        # Mock app details (returned by get_app_details)
        self.app_info_mock = Mock()
        self.app_info_mock.id = self.app_name
        self.app_info_mock.version = "1.0"
        self.app_info_mock.description = "Test app"

        # Job attributes
        self.app_info_mock.jobAttributes.execSystemId = "test-exec-system"
        self.app_info_mock.jobAttributes.maxMinutes = 60
        self.app_info_mock.jobAttributes.archiveOnAppError = True
        self.app_info_mock.jobAttributes.execSystemLogicalQueue = "normal"
        self.app_info_mock.jobAttributes.nodeCount = 1
        self.app_info_mock.jobAttributes.coresPerNode = 1
        self.app_info_mock.jobAttributes.memoryMB = None
        self.app_info_mock.jobAttributes.isMpi = None
        self.app_info_mock.jobAttributes.cmdPrefix = None
        self.app_info_mock.jobAttributes.archiveSystemId = None
        self.app_info_mock.jobAttributes.archiveSystemDir = None

        # Parameter set with proper mock objects
        param_set = Mock()
        param_set.appArgs = [_make_app_arg("Input Script")]
        param_set.envVariables = []
        param_set.schedulerOptions = []
        self.app_info_mock.jobAttributes.parameterSet = param_set

        # File inputs
        self.app_info_mock.jobAttributes.fileInputs = [
            _make_file_input("Input Directory")
        ]

    @patch("dapi.jobs.get_app_details")
    @patch("dapi.jobs.datetime")
    def test_generate_job_info_default(self, mock_datetime, mock_get_app):
        mock_datetime.now.return_value = datetime(2023, 5, 1, 12, 0, 0)
        mock_get_app.return_value = self.app_info_mock

        result = generate_job_request(
            self.t_mock, self.app_name, self.input_uri, self.input_file
        )
        self.assertEqual(result["name"], f"{self.app_name}-20230501_120000")
        self.assertEqual(result["appId"], self.app_name)
        self.assertEqual(result["appVersion"], "1.0")
        self.assertEqual(result["execSystemId"], "test-exec-system")
        self.assertEqual(result["maxMinutes"], 60)
        self.assertTrue(result["archiveOnAppError"])
        self.assertEqual(result["execSystemLogicalQueue"], "normal")
        self.assertEqual(result["nodeCount"], 1)
        self.assertEqual(result["coresPerNode"], 1)
        self.assertEqual(
            result["parameterSet"]["appArgs"],
            [{"name": "Input Script", "arg": self.input_file}],
        )
        self.assertNotIn("schedulerOptions", result["parameterSet"])

    @patch("dapi.jobs.get_app_details")
    def test_generate_job_info_custom(self, mock_get_app):
        mock_get_app.return_value = self.app_info_mock

        custom_job_name = "custom-job"
        custom_max_minutes = 120
        custom_node_count = 2
        custom_cores_per_node = 4
        custom_queue = "high-priority"
        custom_allocation = "project123"
        result = generate_job_request(
            self.t_mock,
            self.app_name,
            self.input_uri,
            job_name=custom_job_name,
            max_minutes=custom_max_minutes,
            node_count=custom_node_count,
            cores_per_node=custom_cores_per_node,
            queue=custom_queue,
            allocation=custom_allocation,
        )
        self.assertEqual(result["name"], custom_job_name)
        self.assertEqual(result["maxMinutes"], custom_max_minutes)
        self.assertEqual(result["nodeCount"], custom_node_count)
        self.assertEqual(result["coresPerNode"], custom_cores_per_node)
        self.assertEqual(result["execSystemLogicalQueue"], custom_queue)
        self.assertEqual(
            result["parameterSet"]["schedulerOptions"],
            [{"name": "TACC Allocation", "arg": f"-A {custom_allocation}"}],
        )

    @patch("dapi.jobs.get_app_details")
    def test_generate_job_info_invalid_app(self, mock_get_app):
        mock_get_app.side_effect = Exception("Invalid app")
        with self.assertRaises(Exception):
            generate_job_request(self.t_mock, "invalid-app", self.input_uri)

    @patch("dapi.jobs.get_app_details")
    def test_generate_job_info_opensees(self, mock_get_app):
        opensees_app_name = "opensees-express"

        # Create a separate app mock for opensees with envVariables containing tclScript
        opensees_app = Mock()
        opensees_app.id = opensees_app_name
        opensees_app.version = "1.0"
        opensees_app.description = "OpenSees app"
        opensees_app.jobAttributes.execSystemId = "test-exec-system"
        opensees_app.jobAttributes.maxMinutes = 60
        opensees_app.jobAttributes.archiveOnAppError = True
        opensees_app.jobAttributes.execSystemLogicalQueue = "normal"
        opensees_app.jobAttributes.nodeCount = 1
        opensees_app.jobAttributes.coresPerNode = 1
        opensees_app.jobAttributes.memoryMB = None
        opensees_app.jobAttributes.isMpi = None
        opensees_app.jobAttributes.cmdPrefix = None
        opensees_app.jobAttributes.archiveSystemId = None
        opensees_app.jobAttributes.archiveSystemDir = None

        # OpenSees uses envVariables for the script, not appArgs
        param_set = Mock()
        param_set.appArgs = []
        param_set.envVariables = [_make_env_var("tclScript")]
        param_set.schedulerOptions = []
        opensees_app.jobAttributes.parameterSet = param_set
        opensees_app.jobAttributes.fileInputs = [_make_file_input("Input Directory")]

        mock_get_app.return_value = opensees_app

        result = generate_job_request(
            self.t_mock,
            opensees_app_name,
            self.input_uri,
            script_filename=self.input_file,
        )
        self.assertIn("parameterSet", result)
        self.assertIn("envVariables", result["parameterSet"])
        self.assertEqual(
            result["parameterSet"]["envVariables"],
            [{"key": "tclScript", "value": self.input_file}],
        )
        self.assertNotIn("appArgs", result["parameterSet"])


if __name__ == "__main__":
    unittest.main()
