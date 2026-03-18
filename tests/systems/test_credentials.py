import unittest
from unittest.mock import Mock, MagicMock

from tapipy.errors import UnauthorizedError, NotFoundError, BaseTapyException

from dapi.systems import (
    check_credentials,
    establish_credentials,
    revoke_credentials,
    _resolve_username,
)
from dapi.exceptions import CredentialError


class TestResolveUsername(unittest.TestCase):
    def test_uses_explicit_username(self):
        t = MagicMock()
        t.username = "tapis_user"
        self.assertEqual(_resolve_username(t, "explicit_user"), "explicit_user")

    def test_falls_back_to_tapis_username(self):
        t = MagicMock()
        t.username = "tapis_user"
        self.assertEqual(_resolve_username(t, None), "tapis_user")

    def test_raises_when_no_username_available(self):
        t = MagicMock(spec=[])  # no username attr
        with self.assertRaises(ValueError):
            _resolve_username(t, None)

    def test_raises_when_username_is_empty_string(self):
        t = MagicMock()
        t.username = ""
        with self.assertRaises(ValueError):
            _resolve_username(t, "")


class TestCheckCredentials(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.username = "testuser"

    def test_returns_true_when_credentials_exist(self):
        self.t.systems.checkUserCredential.return_value = Mock()
        self.assertTrue(check_credentials(self.t, "frontera"))
        self.t.systems.checkUserCredential.assert_called_once_with(
            systemId="frontera", userName="testuser"
        )

    def test_returns_false_on_unauthorized(self):
        self.t.systems.checkUserCredential.side_effect = UnauthorizedError()
        self.assertFalse(check_credentials(self.t, "frontera"))

    def test_returns_false_on_not_found(self):
        self.t.systems.checkUserCredential.side_effect = NotFoundError()
        self.assertFalse(check_credentials(self.t, "frontera"))

    def test_uses_explicit_username(self):
        self.t.systems.checkUserCredential.return_value = Mock()
        check_credentials(self.t, "frontera", username="otheruser")
        self.t.systems.checkUserCredential.assert_called_once_with(
            systemId="frontera", userName="otheruser"
        )

    def test_raises_value_error_for_empty_system_id(self):
        with self.assertRaises(ValueError):
            check_credentials(self.t, "")

    def test_raises_value_error_when_no_username(self):
        self.t.username = None
        with self.assertRaises(ValueError):
            check_credentials(self.t, "frontera")

    def test_raises_credential_error_on_unexpected_api_error(self):
        self.t.systems.checkUserCredential.side_effect = BaseTapyException(
            "server error"
        )
        with self.assertRaises(CredentialError):
            check_credentials(self.t, "frontera")

    def test_raises_credential_error_on_generic_exception(self):
        self.t.systems.checkUserCredential.side_effect = RuntimeError("boom")
        with self.assertRaises(CredentialError):
            check_credentials(self.t, "frontera")


class TestEstablishCredentials(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.username = "testuser"
        # Default: system uses TMS_KEYS
        self.mock_system = Mock()
        self.mock_system.defaultAuthnMethod = "TMS_KEYS"
        self.t.systems.getSystem.return_value = self.mock_system

    def test_creates_credentials_when_missing(self):
        self.t.systems.checkUserCredential.side_effect = UnauthorizedError()
        establish_credentials(self.t, "frontera", verbose=False)
        self.t.systems.createUserCredential.assert_called_once_with(
            systemId="frontera", userName="testuser", createTmsKeys=True
        )

    def test_skips_when_credentials_exist(self):
        self.t.systems.checkUserCredential.return_value = Mock()
        establish_credentials(self.t, "frontera", verbose=False)
        self.t.systems.createUserCredential.assert_not_called()

    def test_force_creates_even_when_credentials_exist(self):
        establish_credentials(self.t, "frontera", force=True, verbose=False)
        self.t.systems.createUserCredential.assert_called_once_with(
            systemId="frontera", userName="testuser", createTmsKeys=True
        )
        # Should NOT call checkUserCredential when force=True
        self.t.systems.checkUserCredential.assert_not_called()

    def test_raises_credential_error_for_non_tms_system(self):
        self.mock_system.defaultAuthnMethod = "PASSWORD"
        with self.assertRaises(CredentialError) as ctx:
            establish_credentials(self.t, "frontera", verbose=False)
        self.assertIn("PASSWORD", str(ctx.exception))
        self.assertIn("TMS_KEYS", str(ctx.exception))

    def test_raises_credential_error_when_system_not_found(self):
        error = BaseTapyException("not found")
        mock_response = Mock()
        mock_response.status_code = 404
        error.response = mock_response
        self.t.systems.getSystem.side_effect = error
        with self.assertRaises(CredentialError) as ctx:
            establish_credentials(self.t, "nonexistent", verbose=False)
        self.assertIn("not found", str(ctx.exception).lower())

    def test_raises_credential_error_on_get_system_api_error(self):
        error = BaseTapyException("server error")
        error.response = None
        self.t.systems.getSystem.side_effect = error
        with self.assertRaises(CredentialError):
            establish_credentials(self.t, "frontera", verbose=False)

    def test_raises_value_error_for_empty_system_id(self):
        with self.assertRaises(ValueError):
            establish_credentials(self.t, "")

    def test_uses_explicit_username(self):
        self.t.systems.checkUserCredential.side_effect = UnauthorizedError()
        establish_credentials(
            self.t, "frontera", username="otheruser", verbose=False
        )
        self.t.systems.createUserCredential.assert_called_once_with(
            systemId="frontera", userName="otheruser", createTmsKeys=True
        )

    def test_raises_credential_error_on_create_failure(self):
        self.t.systems.checkUserCredential.side_effect = UnauthorizedError()
        self.t.systems.createUserCredential.side_effect = BaseTapyException(
            "create failed"
        )
        with self.assertRaises(CredentialError):
            establish_credentials(self.t, "frontera", verbose=False)

    def test_verbose_prints_skip_message(self, ):
        self.t.systems.checkUserCredential.return_value = Mock()
        # Should not raise; just prints a message
        establish_credentials(self.t, "frontera", verbose=True)
        self.t.systems.createUserCredential.assert_not_called()

    def test_verbose_prints_creation_message(self):
        self.t.systems.checkUserCredential.side_effect = UnauthorizedError()
        establish_credentials(self.t, "frontera", verbose=True)
        self.t.systems.createUserCredential.assert_called_once()

    def test_handles_none_authn_method(self):
        self.mock_system.defaultAuthnMethod = None
        with self.assertRaises(CredentialError) as ctx:
            establish_credentials(self.t, "frontera", verbose=False)
        self.assertIn("None", str(ctx.exception))


class TestRevokeCredentials(unittest.TestCase):
    def setUp(self):
        self.t = MagicMock()
        self.t.username = "testuser"

    def test_revokes_existing_credentials(self):
        revoke_credentials(self.t, "frontera", verbose=False)
        self.t.systems.removeUserCredential.assert_called_once_with(
            systemId="frontera", userName="testuser"
        )

    def test_idempotent_when_not_found(self):
        self.t.systems.removeUserCredential.side_effect = NotFoundError()
        # Should not raise
        revoke_credentials(self.t, "frontera", verbose=False)

    def test_idempotent_when_unauthorized(self):
        self.t.systems.removeUserCredential.side_effect = UnauthorizedError()
        revoke_credentials(self.t, "frontera", verbose=False)

    def test_raises_credential_error_on_api_error(self):
        self.t.systems.removeUserCredential.side_effect = BaseTapyException(
            "server error"
        )
        with self.assertRaises(CredentialError):
            revoke_credentials(self.t, "frontera", verbose=False)

    def test_raises_value_error_for_empty_system_id(self):
        with self.assertRaises(ValueError):
            revoke_credentials(self.t, "")

    def test_uses_explicit_username(self):
        revoke_credentials(self.t, "frontera", username="otheruser", verbose=False)
        self.t.systems.removeUserCredential.assert_called_once_with(
            systemId="frontera", userName="otheruser"
        )

    def test_raises_credential_error_on_generic_exception(self):
        self.t.systems.removeUserCredential.side_effect = RuntimeError("boom")
        with self.assertRaises(CredentialError):
            revoke_credentials(self.t, "frontera", verbose=False)


if __name__ == "__main__":
    unittest.main()
