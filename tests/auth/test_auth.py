import unittest
from unittest.mock import patch, MagicMock
from dapi.auth.auth import init


class TestAuthInit(unittest.TestCase):
    @patch("dapi.auth.auth.Tapis")
    @patch("dapi.auth.auth.os.environ")
    def test_init_with_env_variables(self, mock_environ, mock_tapis):
        # Setup
        mock_environ.get.side_effect = {
            "DESIGNSAFE_USERNAME": "test_user",
            "DESIGNSAFE_PASSWORD": "test_password",
        }.get
        mock_tapis_obj = MagicMock()
        mock_tapis.return_value = mock_tapis_obj

        # Execute
        result = init()

        # Verify
        mock_tapis.assert_called_with(
            base_url="https://designsafe.tapis.io",
            username="test_user",
            password="test_password",
        )
        mock_tapis_obj.get_tokens.assert_called_once()
        self.assertEqual(result, mock_tapis_obj)

    @patch("dapi.auth.auth.Tapis")
    @patch("dapi.auth.auth.os.environ")
    @patch("dapi.auth.auth.input")
    @patch("dapi.auth.auth.getpass")
    def test_init_with_user_input(
        self, mock_getpass, mock_input, mock_environ, mock_tapis
    ):
        # Setup
        mock_environ.get.return_value = None
        mock_input.return_value = "test_user"
        mock_getpass.return_value = "test_password"
        mock_tapis_obj = MagicMock()
        mock_tapis.return_value = mock_tapis_obj

        # Execute
        result = init()

        # Verify
        mock_tapis.assert_called_with(
            base_url="https://designsafe.tapis.io",
            username="test_user",
            password="test_password",
        )
        mock_tapis_obj.get_tokens.assert_called_once()
        self.assertEqual(result, mock_tapis_obj)

    @patch("dapi.auth.auth.Tapis")
    @patch("dapi.auth.auth.os.environ")
    def test_init_authentication_failure(self, mock_environ, mock_tapis):
        # Setup
        mock_environ.get.side_effect = {
            "DESIGNSAFE_USERNAME": "invalid_user",
            "DESIGNSAFE_PASSWORD": "invalid_password",
        }.get
        mock_tapis_obj = MagicMock()
        mock_tapis.return_value = mock_tapis_obj
        mock_tapis_obj.get_tokens.side_effect = Exception("Authentication failed")

        # Execute & Verify
        with self.assertRaises(Exception):
            init()


# This allows running the test from the command line
if __name__ == "__main__":
    unittest.main()
