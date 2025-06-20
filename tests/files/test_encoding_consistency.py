import unittest
from unittest.mock import MagicMock, Mock
from dapi.files import _safe_quote, _parse_tapis_uri, get_ds_path_uri
from tapipy.tapis import Tapis
import urllib.parse


class TestEncodingConsistency(unittest.TestCase):
    """Test encoding consistency and double-encoding prevention."""

    def test_safe_quote_prevents_double_encoding(self):
        """Test that _safe_quote prevents double encoding."""
        # Test with unencoded path
        unencoded = "folder with spaces"
        encoded_once = _safe_quote(unencoded)
        encoded_twice = _safe_quote(encoded_once)

        self.assertEqual(encoded_once, "folder%20with%20spaces")
        self.assertEqual(encoded_twice, encoded_once)  # Should not double encode

    def test_safe_quote_with_multiple_spaces(self):
        """Test _safe_quote with multiple spaces."""
        test_cases = [
            ("folder with spaces", "folder%20with%20spaces"),
            ("folder%20with%20spaces", "folder%20with%20spaces"),  # Already encoded
            ("normal_folder", "normal_folder"),
            ("path/with spaces/here", "path/with%20spaces/here"),
            (
                "path%2Fwith%20spaces%2Fhere",
                "path%2Fwith%20spaces%2Fhere",
            ),  # Already encoded
        ]

        for input_path, expected in test_cases:
            with self.subTest(input_path=input_path):
                result = _safe_quote(input_path)
                self.assertEqual(result, expected)

    def test_uri_generation_uses_spaces(self):
        """Test that URI generation creates URIs with spaces, not %20."""
        mock_tapis = MagicMock(spec=Tapis)
        mock_tapis.username = "testuser"

        path = "jupyter/MyData/folder with spaces/file.txt"
        uri = get_ds_path_uri(mock_tapis, path)

        # URI should contain actual spaces
        self.assertIn("folder with spaces", uri)
        self.assertNotIn("folder%20with%20spaces", uri)
        self.assertEqual(
            uri,
            "tapis://designsafe.storage.default/testuser/folder with spaces/file.txt",
        )

    def test_uri_parsing_handles_spaces(self):
        """Test that URI parsing correctly handles URIs with spaces."""
        uri_with_spaces = (
            "tapis://designsafe.storage.default/testuser/folder with spaces/file.txt"
        )
        system_id, path = _parse_tapis_uri(uri_with_spaces)

        self.assertEqual(system_id, "designsafe.storage.default")
        self.assertEqual(path, "testuser/folder with spaces/file.txt")

    def test_uri_parsing_handles_encoded_uris(self):
        """Test that URI parsing correctly handles pre-encoded URIs."""
        uri_with_encoding = "tapis://designsafe.storage.default/testuser/folder%20with%20spaces/file.txt"
        system_id, path = _parse_tapis_uri(uri_with_encoding)

        self.assertEqual(system_id, "designsafe.storage.default")
        # Should return the path as-is (with %20) since we no longer decode
        self.assertEqual(path, "testuser/folder%20with%20spaces/file.txt")

    def test_round_trip_consistency(self):
        """Test that URI generation and parsing are consistent."""
        mock_tapis = MagicMock(spec=Tapis)
        mock_tapis.username = "testuser"

        original_path = "jupyter/MyData/folder with spaces/file.txt"

        # Generate URI
        uri = get_ds_path_uri(mock_tapis, original_path)

        # Parse URI back
        system_id, parsed_path = _parse_tapis_uri(uri)

        # The parsed path should match the expected Tapis path
        expected_tapis_path = "testuser/folder with spaces/file.txt"
        self.assertEqual(parsed_path, expected_tapis_path)

        # Safe quote should properly encode for API calls
        api_path = _safe_quote(parsed_path)
        self.assertEqual(api_path, "testuser/folder%20with%20spaces/file.txt")


if __name__ == "__main__":
    unittest.main()
