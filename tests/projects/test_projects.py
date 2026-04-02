import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from dapi.projects import (
    list_projects,
    get_project,
    list_project_files,
    resolve_project_uuid,
)
from dapi.exceptions import FileOperationError


_MOCK_API_RESPONSE = {
    "result": [
        {
            "uuid": "abc-123",
            "created": "2025-01-01T00:00:00Z",
            "lastUpdated": "2025-06-01T00:00:00Z",
            "value": {
                "projectId": "PRJ-1234",
                "title": "Test Project",
                "projectType": "experimental",
                "users": [
                    {"role": "pi", "username": "testpi", "fname": "Test", "lname": "PI"}
                ],
            },
        }
    ]
}


class TestListProjects(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.projects.requests.get")
    def test_returns_dataframe_by_default(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = _MOCK_API_RESPONSE
        result = list_projects(self.t)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["projectId"], "PRJ-1234")
        self.assertEqual(result.iloc[0]["pi"], "Test PI")

    @patch("dapi.projects.requests.get")
    def test_returns_list_of_dicts(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = _MOCK_API_RESPONSE
        result = list_projects(self.t, output="list")
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["projectId"], "PRJ-1234")
        self.assertEqual(result[0]["pi"], "Test PI")

    @patch("dapi.projects.requests.get")
    def test_no_pi_shows_empty_string(self, mock_get):
        resp = {
            "result": [
                {
                    "uuid": "abc-123",
                    "created": "2025-01-01",
                    "lastUpdated": "2025-06-01",
                    "value": {
                        "projectId": "PRJ-1234",
                        "title": "No PI",
                        "projectType": None,
                        "users": [],
                    },
                }
            ]
        }
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = resp
        result = list_projects(self.t, output="list")
        self.assertEqual(result[0]["pi"], "")

    def test_invalid_output_raises(self):
        with self.assertRaises(ValueError):
            list_projects(self.t, output="csv")

    @patch("dapi.projects.requests.get")
    def test_api_failure(self, mock_get):
        from requests.exceptions import ConnectionError

        mock_get.side_effect = ConnectionError("Connection refused")
        with self.assertRaises(FileOperationError):
            list_projects(self.t)


class TestGetProject(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.projects.requests.get")
    def test_returns_metadata_dict(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "baseProject": {
                "uuid": "abc-123",
                "created": "2025-01-01",
                "lastUpdated": "2025-06-01",
                "value": {
                    "projectId": "PRJ-1234",
                    "title": "Test Project",
                    "description": "A test",
                    "coPis": [],
                    "teamMembers": [],
                    "awardNumbers": [],
                    "keywords": ["earthquake"],
                    "dois": ["10.1234/test"],
                    "projectType": "experimental",
                    "users": [
                        {
                            "role": "pi",
                            "username": "testpi",
                            "fname": "Test",
                            "lname": "PI",
                        }
                    ],
                },
            },
            "entities": [],
            "tree": [],
        }
        result = get_project(self.t, "PRJ-1234")
        self.assertEqual(result["projectId"], "PRJ-1234")
        self.assertEqual(result["systemId"], "project-abc-123")
        self.assertEqual(result["pi"], "Test PI")
        self.assertEqual(result["dois"], ["10.1234/test"])


class TestListProjectFiles(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.projects.get_project")
    def test_returns_dataframe_by_default(self, mock_get_project):
        mock_get_project.return_value = {"systemId": "project-abc-123"}
        mock_file = MagicMock()
        mock_file.name = "data.csv"
        mock_file.type = "file"
        mock_file.size = 1024
        mock_file.lastModified = "2025-01-01T00:00:00Z"
        mock_file.path = "/data.csv"
        self.t.files.listFiles.return_value = [mock_file]

        result = list_project_files(self.t, "PRJ-1234")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["name"], "data.csv")

    @patch("dapi.projects.get_project")
    def test_returns_raw(self, mock_get_project):
        mock_get_project.return_value = {"systemId": "project-abc-123"}
        mock_file = MagicMock()
        self.t.files.listFiles.return_value = [mock_file]

        result = list_project_files(self.t, "PRJ-1234", output="raw")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    def test_invalid_output_raises(self):
        with self.assertRaises(ValueError):
            list_project_files(self.t, "PRJ-1234", output="csv")


class TestResolveProjectUuid(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.projects.requests.get")
    def test_resolves_prj_to_system_id(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "result": [
                {"uuid": "abc-123-def", "value": {"projectId": "PRJ-1234"}},
            ]
        }
        result = resolve_project_uuid(self.t, "PRJ-1234")
        self.assertEqual(result, "project-abc-123-def")

    @patch("dapi.projects.requests.get")
    def test_not_found_raises_error(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "result": [{"uuid": "abc", "value": {"projectId": "PRJ-9999"}}]
        }
        with self.assertRaises(FileOperationError):
            resolve_project_uuid(self.t, "PRJ-1234")


if __name__ == "__main__":
    unittest.main()
