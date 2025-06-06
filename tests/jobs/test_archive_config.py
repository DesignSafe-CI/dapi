import unittest
from unittest.mock import MagicMock, patch
from dapi.jobs import generate_job_request


class TestArchiveConfiguration(unittest.TestCase):
    """Test cases for archive system configuration in job generation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_tapis = MagicMock()
        self.mock_tapis.username = "testuser"

        # Mock app details
        self.mock_app = MagicMock()
        self.mock_app.id = "test-app"
        self.mock_app.version = "1.0"
        self.mock_app.description = "Test app"

        # Mock job attributes
        self.mock_job_attrs = MagicMock()
        self.mock_job_attrs.execSystemId = "test-system"
        self.mock_job_attrs.archiveSystemId = "default-archive"
        self.mock_job_attrs.archiveSystemDir = None
        self.mock_job_attrs.archiveOnAppError = True
        self.mock_job_attrs.execSystemLogicalQueue = "normal"
        self.mock_job_attrs.nodeCount = 1
        self.mock_job_attrs.coresPerNode = 1
        self.mock_job_attrs.maxMinutes = 60
        self.mock_job_attrs.memoryMB = 1000
        self.mock_job_attrs.isMpi = False

        # Mock parameter set
        self.mock_param_set = MagicMock()
        self.mock_param_set.appArgs = [MagicMock(name="Main Script")]
        self.mock_param_set.envVariables = []
        self.mock_param_set.schedulerOptions = []
        self.mock_job_attrs.parameterSet = self.mock_param_set

        self.mock_app.jobAttributes = self.mock_job_attrs

    @patch("dapi.jobs.get_app_details")
    def test_designsafe_archive_system_default_path(self, mock_get_app):
        """Test archive system configuration with DesignSafe and default path"""
        mock_get_app.return_value = self.mock_app

        job_request = generate_job_request(
            tapis_client=self.mock_tapis,
            app_id="test-app",
            input_dir_uri="tapis://test-system/input",
            script_filename="test.sh",
            archive_system="designsafe",
        )

        self.assertEqual(job_request["archiveSystemId"], "designsafe.storage.default")
        self.assertEqual(
            job_request["archiveSystemDir"],
            "${EffectiveUserId}/tapis-jobs-archive/${JobCreateDate}/${JobUUID}",
        )

    @patch("dapi.jobs.get_app_details")
    def test_designsafe_archive_system_custom_dir(self, mock_get_app):
        """Test archive system configuration with DesignSafe and custom directory name"""
        mock_get_app.return_value = self.mock_app

        job_request = generate_job_request(
            tapis_client=self.mock_tapis,
            app_id="test-app",
            input_dir_uri="tapis://test-system/input",
            script_filename="test.sh",
            archive_system="designsafe",
            archive_path="my-jobs",
        )

        self.assertEqual(job_request["archiveSystemId"], "designsafe.storage.default")
        self.assertEqual(
            job_request["archiveSystemDir"],
            "${EffectiveUserId}/my-jobs/${JobCreateDate}/${JobUUID}",
        )

    @patch("dapi.jobs.get_app_details")
    def test_designsafe_archive_system_full_path(self, mock_get_app):
        """Test archive system configuration with DesignSafe and full path"""
        mock_get_app.return_value = self.mock_app

        job_request = generate_job_request(
            tapis_client=self.mock_tapis,
            app_id="test-app",
            input_dir_uri="tapis://test-system/input",
            script_filename="test.sh",
            archive_system="designsafe",
            archive_path="${EffectiveUserId}/custom/path/${JobUUID}",
        )

        self.assertEqual(job_request["archiveSystemId"], "designsafe.storage.default")
        self.assertEqual(
            job_request["archiveSystemDir"], "${EffectiveUserId}/custom/path/${JobUUID}"
        )

    @patch("dapi.jobs.get_app_details")
    def test_custom_archive_system(self, mock_get_app):
        """Test archive system configuration with custom system"""
        mock_get_app.return_value = self.mock_app

        job_request = generate_job_request(
            tapis_client=self.mock_tapis,
            app_id="test-app",
            input_dir_uri="tapis://test-system/input",
            script_filename="test.sh",
            archive_system="custom.storage.system",
            archive_path="/custom/archive/path",
        )

        self.assertEqual(job_request["archiveSystemId"], "custom.storage.system")
        self.assertEqual(job_request["archiveSystemDir"], "/custom/archive/path")

    @patch("dapi.jobs.get_app_details")
    def test_no_archive_system_uses_app_default(self, mock_get_app):
        """Test that no archive system specification uses app defaults"""
        mock_get_app.return_value = self.mock_app

        job_request = generate_job_request(
            tapis_client=self.mock_tapis,
            app_id="test-app",
            input_dir_uri="tapis://test-system/input",
            script_filename="test.sh",
        )

        self.assertEqual(job_request["archiveSystemId"], "default-archive")
        self.assertNotIn("archiveSystemDir", job_request)


# This allows running the test from the command line
if __name__ == "__main__":
    unittest.main()
