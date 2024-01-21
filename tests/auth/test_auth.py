import unittest
from unittest.mock import patch, MagicMock
from dapi.auth.auth import init


class TestAuthInit(unittest.TestCase):
    @patch("dapi.auth.auth.Agave")
    def test_init_success(self, mock_agave):
        # Setup
        username = "test_user"
        password = "test_password"
        mock_agave_obj = MagicMock()
        mock_agave.return_value = mock_agave_obj
        mock_agave_obj.clients_create.return_value = {
            "api_key": "test_api_key",
            "api_secret": "test_api_secret",
        }

        # Execute
        result = init(username, password)

        # Verify
        mock_agave.assert_called_with(
            base_url="https://agave.designsafe-ci.org",
            username=username,
            password=password,
            api_key="test_api_key",
            api_secret="test_api_secret",
        )
        self.assertIsInstance(result, MagicMock)

    @patch("dapi.auth.auth.Agave")
    def test_init_invalid_credentials(self, mock_agave):
        # Setup
        username = "invalid_user"
        password = "invalid_password"
        mock_agave.side_effect = Exception("Invalid credentials")

        # Execute & Verify
        with self.assertRaises(Exception):
            init(username, password)


# This allows running the test from the command line
if __name__ == "__main__":
    unittest.main()
