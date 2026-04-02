import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from dapi.publications import (
    list_publications,
    search_publications,
    get_publication,
    list_publication_files,
)


_MOCK_LIST_RESPONSE = {
    "result": [
        {
            "projectId": "PRJ-1234",
            "title": "Earthquake Liquefaction Study",
            "description": "A study of lateral spreading",
            "type": "simulation",
            "pi": {"fname": "Jane", "lname": "Doe", "role": "pi", "username": "jdoe"},
            "keywords": ["liquefaction", "lateral spreading"],
            "created": "2025-06-01T00:00:00Z",
        },
        {
            "projectId": "PRJ-5678",
            "title": "Wind Tunnel Experiments",
            "description": "Low-rise building aerodynamics",
            "type": "experimental",
            "pi": {
                "fname": "John",
                "lname": "Smith",
                "role": "pi",
                "username": "jsmith",
            },
            "keywords": ["wind", "aerodynamics"],
            "created": "2025-03-01T00:00:00Z",
        },
    ],
    "total": 2,
}


class TestListPublications(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.publications.requests.get")
    def test_returns_dataframe_by_default(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = _MOCK_LIST_RESPONSE
        result = list_publications(self.t)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["projectId"], "PRJ-1234")
        self.assertEqual(result.iloc[0]["pi"], "Jane Doe")

    @patch("dapi.publications.requests.get")
    def test_returns_list(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = _MOCK_LIST_RESPONSE
        result = list_publications(self.t, output="list")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_invalid_output_raises(self):
        with self.assertRaises(ValueError):
            list_publications(self.t, output="csv")


class TestSearchPublications(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.publications.requests.get")
    def test_search_by_keyword(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = _MOCK_LIST_RESPONSE
        result = search_publications(self.t, "liquefaction")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["projectId"], "PRJ-1234")

    @patch("dapi.publications.requests.get")
    def test_search_by_pi_name(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = _MOCK_LIST_RESPONSE
        result = search_publications(self.t, "Smith", output="list")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["projectId"], "PRJ-5678")

    @patch("dapi.publications.requests.get")
    def test_search_no_matches(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = _MOCK_LIST_RESPONSE
        result = search_publications(self.t, "nonexistent")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    @patch("dapi.publications.requests.get")
    def test_search_case_insensitive(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = _MOCK_LIST_RESPONSE
        result = search_publications(self.t, "WIND", output="list")
        self.assertEqual(len(result), 1)


class TestGetPublication(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    @patch("dapi.publications.requests.get")
    def test_returns_metadata(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "tree": {
                "children": [
                    {
                        "value": {
                            "projectId": "PRJ-1234",
                            "title": "Test Publication",
                            "description": "A test",
                            "dois": ["10.1234/test"],
                            "keywords": ["earthquake"],
                            "dataTypes": ["Dataset"],
                            "projectType": "simulation",
                            "awardNumbers": [],
                            "users": [
                                {
                                    "role": "pi",
                                    "fname": "Jane",
                                    "lname": "Doe",
                                    "username": "jdoe",
                                }
                            ],
                        },
                        "publicationDate": "2025-01-01",
                    }
                ]
            },
            "baseProject": {},
            "fileTags": [],
        }
        result = get_publication(self.t, "PRJ-1234")
        self.assertEqual(result["projectId"], "PRJ-1234")
        self.assertEqual(result["pi"], "Jane Doe")
        self.assertEqual(result["dois"], ["10.1234/test"])


class TestListPublicationFiles(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.access_token.access_token = "mock-token"

    def test_returns_dataframe(self):
        mock_file = MagicMock()
        mock_file.name = "data.csv"
        mock_file.type = "file"
        mock_file.size = 2048
        mock_file.lastModified = "2025-01-01T00:00:00Z"
        mock_file.path = "/PRJ-1234/data.csv"
        self.t.files.listFiles.return_value = [mock_file]

        result = list_publication_files(self.t, "PRJ-1234")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["name"], "data.csv")
        self.t.files.listFiles.assert_called_once_with(
            systemId="designsafe.storage.published", path="/PRJ-1234/", limit=100
        )

    def test_returns_raw(self):
        mock_file = MagicMock()
        self.t.files.listFiles.return_value = [mock_file]
        result = list_publication_files(self.t, "PRJ-1234", output="raw")
        self.assertIsInstance(result, list)

    def test_invalid_output_raises(self):
        with self.assertRaises(ValueError):
            list_publication_files(self.t, "PRJ-1234", output="csv")


if __name__ == "__main__":
    unittest.main()
