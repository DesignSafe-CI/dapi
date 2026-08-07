import os
import tempfile
import unittest
from unittest.mock import MagicMock

from dapi.files import download_file


class TestDownloadContentTypes(unittest.TestCase):
    """tapipy returns raw bytes for non-JSON responses; some code paths
    return a streaming response object. download_file must handle both."""

    def test_download_bytes_payload(self):
        mock_tapis = MagicMock()
        mock_tapis.files.getContents.return_value = b"binary \x00 payload"

        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "out.zip")
            download_file(mock_tapis, "tapis://test-system/data/out.zip", target)

            with open(target, "rb") as f:
                self.assertEqual(f.read(), b"binary \x00 payload")

    def test_download_streaming_response(self):
        response = MagicMock(spec=["iter_content"])
        response.iter_content.return_value = iter([b"chunk1", b"chunk2"])
        mock_tapis = MagicMock()
        mock_tapis.files.getContents.return_value = response

        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "out.txt")
            download_file(mock_tapis, "tapis://test-system/data/out.txt", target)

            with open(target, "rb") as f:
                self.assertEqual(f.read(), b"chunk1chunk2")


if __name__ == "__main__":
    unittest.main()
