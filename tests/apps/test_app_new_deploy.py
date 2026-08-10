import json
import os
import tempfile
import unittest
import zipfile

from dapi.apps import deploy_app, list_app_templates, new_app
from dapi.exceptions import AppDiscoveryError


class TestNew(unittest.TestCase):
    def test_container_and_zip_templates_ship(self):
        self.assertIn("container", list_app_templates())
        self.assertIn("zip", list_app_templates())

    def test_new_zip_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = new_app("my-app", target_dir=tmp, template="zip")
            spec = json.load(open(os.path.join(path, "app.json")))
            self.assertEqual(spec["id"], "my-app")
            body = open(os.path.join(path, "tapisjob_app.sh")).read()
            self.assertIn("my-app: EDIT THIS WRAPPER", body)
            self.assertIn("COMMAND", body)

    def test_new_substitutes_app_id_and_is_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = new_app("my-container", target_dir=tmp)
            spec = json.load(open(os.path.join(path, "app.json")))
            self.assertEqual(spec["id"], "my-container")
            wrapper = os.path.join(path, "tapisjob_app.sh")
            self.assertTrue(os.access(wrapper, os.X_OK))
            body = open(wrapper).read()
            self.assertIn("set +u", body)  # module load guarded against nounset
            self.assertIn("CONTAINER_IMAGE", body)

    def test_unknown_template_rejected(self):
        with self.assertRaises(AppDiscoveryError):
            new_app("x", template="elyra")

    def test_existing_files_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            new_app("my-app", target_dir=tmp)
            with self.assertRaises(AppDiscoveryError):
                new_app("my-app", target_dir=tmp)


class _StubApps:
    def __init__(self, exists=False):
        self.exists = exists
        self.created = None
        self.updated = None

    def createAppVersion(self, **spec):
        if self.exists:
            from tapipy.errors import BaseTapyException

            raise BaseTapyException("APPAPI_APP_EXISTS: already exists")
        self.created = spec

    def putApp(self, **spec):
        self.updated = spec


class _StubTapis:
    def __init__(self, exists=False):
        self.username = "user1"
        self.apps = _StubApps(exists)
        self.uploads = []

    def upload(self, system_id, source_file_path, dest_file_path):
        self.uploads.append((system_id, source_file_path, dest_file_path))


class TestDeploy(unittest.TestCase):
    def _app_dir(self, tmp):
        return new_app("my-container", target_dir=tmp)

    def test_deploy_zips_uploads_and_registers(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = _StubTapis()
            result = deploy_app(t, self._app_dir(tmp))
            system, zip_path, dest = t.uploads[0]
            self.assertEqual(system, "designsafe.storage.default")
            self.assertEqual(dest, "user1/apps/my-container/0.1.0/my-container.zip")
            names = zipfile.ZipFile(zip_path).namelist()
            self.assertIn("tapisjob_app.sh", names)
            self.assertNotIn("app.json", names)
            spec = t.apps.created
            self.assertEqual(spec["id"], "my-container")
            self.assertEqual(
                spec["containerImage"],
                "tapis://designsafe.storage.default/user1/apps/my-container/0.1.0/my-container.zip",
            )
            self.assertNotIn("owner", spec)
            self.assertEqual(result["app_id"], "my-container")

    def test_existing_version_is_updated_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = _StubTapis(exists=True)
            deploy_app(t, self._app_dir(tmp))
            self.assertIsNone(t.apps.created)
            self.assertEqual(t.apps.updated["appId"], "my-container")
            self.assertEqual(t.apps.updated["appVersion"], "0.1.0")

    def test_version_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = _StubTapis()
            result = deploy_app(t, self._app_dir(tmp), version="0.2.0")
            self.assertEqual(result["version"], "0.2.0")
            self.assertIn("/0.2.0/", t.uploads[0][2])


if __name__ == "__main__":
    unittest.main()
