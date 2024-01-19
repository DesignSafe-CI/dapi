import unittest
from unittest.mock import Mock, patch
from dapi.jobs import jobs


class TestGenerateJobInfo(unittest.TestCase):
    def setUp(self):
        # Mock the ag object
        self.ag_mock = Mock()
        self.appid_valid = "valid-appid"
        self.appid_invalid = "invalid-appid"

        # Define the behavior of the mocked method
        def mock_get_method(appId):
            if appId == self.appid_valid:
                return True
            raise Exception("Invalid app ID")

        # Set the side_effect for the mock to the defined behavior
        self.ag_mock.apps.get.side_effect = mock_get_method

    def test_valid_appid(self):
        """Test with a valid app ID."""
        result = jobs.generate_job_info(self.ag_mock, self.appid_valid)
        self.assertEqual(result["appId"], self.appid_valid)

    def test_invalid_appid(self):
        """Test with an invalid app ID."""
        try:
            result = jobs.generate_job_info(self.ag_mock, self.appid_invalid)
            print("Result:", result)
        except Exception as e:
            print("Exception raised:", e)

        with self.assertRaises(ValueError):
            jobs.generate_job_info(self.ag_mock, self.appid_invalid)

    def test_default_values(self):
        """Test with default values."""
        result = jobs.generate_job_info(self.ag_mock, self.appid_valid)
        self.assertEqual(result["name"], "dsjob")
        self.assertEqual(result["batchQueue"], "development")
        self.assertEqual(result["nodeCount"], 1)
        self.assertEqual(result["processorsPerNode"], 1)
        self.assertEqual(result["maxRunTime"], "00:10:00")
        self.assertTrue(result["archive"])
        self.assertIsNone(result["inputs"])
        self.assertIsNone(result["parameters"])


if __name__ == "__main__":
    unittest.main()
