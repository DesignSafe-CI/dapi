import unittest
from unittest.mock import Mock, patch
from dapi.jobs import generate_job_request
from datetime import datetime


class TestGenerateJobInfo(unittest.TestCase):
    def setUp(self):
        self.t_mock = Mock()
        self.app_name = "test-app"
        self.input_uri = "tapis://test-system/input/data"
        self.input_file = "input.txt"
        # Mock the getAppLatestVersion method
        self.app_info_mock = Mock()
        self.app_info_mock.id = self.app_name
        self.app_info_mock.version = "1.0"
        self.app_info_mock.jobAttributes.execSystemId = "test-exec-system"
        self.app_info_mock.jobAttributes.maxMinutes = 60
        self.app_info_mock.jobAttributes.archiveOnAppError = True
        self.app_info_mock.jobAttributes.execSystemLogicalQueue = "normal"
        self.t_mock.apps.getAppLatestVersion.return_value = self.app_info_mock

    @patch("dapi.jobs.datetime")
    def test_generate_job_info_default(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 5, 1, 12, 0, 0)
        result = generate_job_request(
            self.t_mock, self.app_name, self.input_uri, self.input_file
        )
        self.assertEqual(result["name"], f"{self.app_name}_20230501_120000")
        self.assertEqual(result["appId"], self.app_name)
        self.assertEqual(result["appVersion"], "1.0")
        self.assertEqual(result["execSystemId"], "test-exec-system")
        self.assertEqual(result["maxMinutes"], 60)
        self.assertTrue(result["archiveOnAppError"])
        self.assertEqual(
            result["fileInputs"],
            [{"name": "Input Directory", "sourceUrl": self.input_uri}],
        )
        self.assertEqual(result["execSystemLogicalQueue"], "normal")
        self.assertEqual(result["nodeCount"], 1)
        self.assertEqual(result["coresPerNode"], 1)
        self.assertEqual(
            result["parameterSet"]["appArgs"],
            [{"name": "Input Script", "arg": self.input_file}],
        )
        self.assertNotIn("schedulerOptions", result["parameterSet"])

    def test_generate_job_info_custom(self):
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

    def test_generate_job_info_invalid_app(self):
        self.t_mock.apps.getAppLatestVersion.side_effect = Exception("Invalid app")
        with self.assertRaises(Exception):
            generate_job_request(self.t_mock, "invalid-app", self.input_uri)

    def test_generate_job_info_opensees(self):
        opensees_app_name = "opensees-express"
        result = generate_job_request(self.t_mock, opensees_app_name, self.input_uri)
        self.assertIn("parameterSet", result)
        self.assertIn("envVariables", result["parameterSet"])
        self.assertEqual(
            result["parameterSet"]["envVariables"],
            [{"key": "tclScript", "value": self.input_file}],
        )
        self.assertNotIn("appArgs", result["parameterSet"])


if __name__ == "__main__":
    unittest.main()
