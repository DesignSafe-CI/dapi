import unittest
from unittest.mock import MagicMock, patch
from dapi.projects import (
    list_projects,
    get_project,
    list_project_files,
    resolve_project_uuid,
)
from dapi.exceptions import FileOperationError


class TestListProjects(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.projects.requests.get")
    def test_list_projects_returns_formatted_list(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "result": [
                {
                    "uuid": "abc-123",
                    "created": "2025-01-01",
                    "lastUpdated": "2025-06-01",
                    "value": {
                        "projectId": "PRJ-1234",
                        "title": "Test Project",
                        "users": [
                            {
                                "role": "pi",
                                "username": "testpi",
                                "fname": "Test",
                                "lname": "PI",
                            }
                        ],
                    },
                }
            ]
        }
        result = list_projects(self.t)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["projectId"], "PRJ-1234")
        self.assertEqual(result[0]["title"], "Test Project")
        self.assertEqual(result[0]["uuid"], "abc-123")
        self.assertEqual(result[0]["pi"]["username"], "testpi")

    @patch("dapi.projects.requests.get")
    def test_list_projects_no_pi(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "result": [
                {
                    "uuid": "abc-123",
                    "created": "2025-01-01",
                    "lastUpdated": "2025-06-01",
                    "value": {
                        "projectId": "PRJ-1234",
                        "title": "No PI Project",
                        "users": [],
                    },
                }
            ]
        }
        result = list_projects(self.t)
        self.assertIsNone(result[0]["pi"])

    @patch("dapi.projects.requests.get")
    def test_list_projects_api_failure(self, mock_get):
        from requests.exceptions import ConnectionError

        mock_get.side_effect = ConnectionError("Connection refused")
        with self.assertRaises(FileOperationError):
            list_projects(self.t)


class TestGetProject(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.projects.requests.get")
    def test_get_project_returns_metadata(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "baseProject": {
                "uuid": "abc-123",
                "created": "2025-01-01",
                "lastUpdated": "2025-06-01",
                "value": {
                    "projectId": "PRJ-1234",
                    "title": "Test Project",
                    "description": "A test project",
                    "coPis": ["copi1"],
                    "teamMembers": ["member1"],
                    "awardNumbers": [{"number": "NSF-123"}],
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
        self.assertEqual(result["title"], "Test Project")
        self.assertEqual(result["description"], "A test project")
        self.assertEqual(result["systemId"], "project-abc-123")
        self.assertEqual(result["pi"]["username"], "testpi")
        self.assertEqual(result["dois"], ["10.1234/test"])

    @patch("dapi.projects.requests.get")
    def test_get_project_not_found(self, mock_get):
        from requests.exceptions import HTTPError

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = HTTPError(
            "Not found", response=mock_resp
        )
        mock_get.return_value = mock_resp
        with self.assertRaises(FileOperationError):
            get_project(self.t, "PRJ-9999")


class TestListProjectFiles(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.projects.get_project")
    def test_list_project_files(self, mock_get_project):
        mock_get_project.return_value = {
            "systemId": "project-abc-123",
            "projectId": "PRJ-1234",
        }
        mock_file = MagicMock()
        mock_file.name = "data.csv"
        mock_file.type = "file"
        self.t.files.listFiles.return_value = [mock_file]

        result = list_project_files(self.t, "PRJ-1234")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "data.csv")
        self.t.files.listFiles.assert_called_once_with(
            systemId="project-abc-123", path="/", limit=100
        )

    @patch("dapi.projects.get_project")
    def test_list_project_files_with_path(self, mock_get_project):
        mock_get_project.return_value = {
            "systemId": "project-abc-123",
            "projectId": "PRJ-1234",
        }
        self.t.files.listFiles.return_value = []

        list_project_files(self.t, "PRJ-1234", path="/subfolder/")
        self.t.files.listFiles.assert_called_once_with(
            systemId="project-abc-123", path="/subfolder/", limit=100
        )


class TestResolveProjectUuid(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.projects.requests.get")
    def test_resolves_prj_to_system_id(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "result": [
                {
                    "uuid": "abc-123-def-456",
                    "value": {"projectId": "PRJ-1234"},
                },
                {
                    "uuid": "xyz-789",
                    "value": {"projectId": "PRJ-5678"},
                },
            ]
        }
        result = resolve_project_uuid(self.t, "PRJ-1234")
        self.assertEqual(result, "project-abc-123-def-456")

    @patch("dapi.projects.requests.get")
    def test_not_found_raises_error(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "result": [{"uuid": "abc", "value": {"projectId": "PRJ-9999"}}]
        }
        with self.assertRaises(FileOperationError):
            resolve_project_uuid(self.t, "PRJ-1234")


if __name__ == "__main__":
    unittest.main()
