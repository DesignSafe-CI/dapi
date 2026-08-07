import json
import os
import tempfile
import unittest
import zipfile

from dapi.jobs import prepare_job_inputs
from dapi.simcenter import BUNDLE_NAME, DEFAULT_BACKEND_DIRS, prepare_inputs


def _make_input_dir(root):
    """Create a minimal SimCenter input directory (root/DS_input) with a
    workflow JSON and a stray checkpoint file."""
    input_dir = os.path.join(root, "DS_input")
    templatedir = os.path.join(input_dir, "tmp.SimCenter", "templatedir")
    os.makedirs(templatedir)
    workflow = {
        "UQ": {"uqEngine": "SimCenterUQ", "uqType": "Sensitivity Analysis"},
        "randomVariables": [{"name": "Dr"}, {"name": "G0"}, {"name": "hpo"}],
        "EDP": [{"name": "nCycles010_1"}, {"name": "nCycles013"}],
        "remoteAppDir": "C:/Users/someone/Desktop/SimCenterBackendApplications",
        "remoteAppWorkingDir": "C:/Users/someone/Desktop/SimCenterBackendApplications",
    }
    workflow_path = os.path.join(templatedir, "scInput.json")
    with open(workflow_path, "w") as f:
        json.dump(workflow, f)
    with open(os.path.join(templatedir, "driver"), "w") as f:
        f.write("echo driver\n")
    checkpoints = os.path.join(templatedir, ".ipynb_checkpoints")
    os.makedirs(checkpoints)
    with open(os.path.join(checkpoints, "scInput-checkpoint.json"), "w") as f:
        f.write("{}")
    return input_dir, workflow_path


class TestBundling(unittest.TestCase):
    def test_bundle_default_creates_staged_zip(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir, workflow_path = _make_input_dir(root)

            summary = prepare_inputs(input_dir)

            staged = os.path.join(root, "DS_input_staged")
            self.assertEqual(summary["staged_dir"], staged)
            self.assertEqual(summary["bundle"], os.path.join(staged, BUNDLE_NAME))
            self.assertTrue(os.path.isfile(summary["bundle"]))

            with zipfile.ZipFile(summary["bundle"]) as zf:
                names = zf.namelist()
                # Layout the wrapper expects after "unzip tmpSimCenter.zip"
                self.assertTrue(all(n.startswith("tmp.SimCenter/") for n in names))
                self.assertIn("tmp.SimCenter/templatedir/scInput.json", names)
                self.assertIn("tmp.SimCenter/templatedir/driver", names)
                # Nothing is excluded from the bundle
                self.assertIn(
                    "tmp.SimCenter/templatedir/.ipynb_checkpoints/scInput-checkpoint.json",
                    names,
                )
                self.assertEqual(summary["bundled_files"], len(names))
                # The zipped workflow JSON carries the backend patch
                patched = json.loads(zf.read("tmp.SimCenter/templatedir/scInput.json"))
            expected_backend = DEFAULT_BACKEND_DIRS["simcenter-uq-stampede3"]
            self.assertEqual(patched["remoteAppDir"], expected_backend)

            # Original input tree is left in place
            self.assertTrue(os.path.isfile(workflow_path))

    def test_bundle_false_stages_input_dir(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir, _ = _make_input_dir(root)

            summary = prepare_inputs(input_dir, bundle=False)

            self.assertEqual(summary["staged_dir"], input_dir)
            self.assertNotIn("bundle", summary)
            self.assertFalse(os.path.exists(os.path.join(root, "DS_input_staged")))

    def test_sibling_files_copied_to_staged_dir(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir, _ = _make_input_dir(root)
            with open(os.path.join(input_dir, "README.txt"), "w") as f:
                f.write("about this run\n")

            summary = prepare_inputs(input_dir)

            self.assertTrue(
                os.path.isfile(os.path.join(summary["staged_dir"], "README.txt"))
            )

    def test_explicit_staged_dir(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir, _ = _make_input_dir(root)
            custom = os.path.join(root, "my_stage")

            summary = prepare_inputs(input_dir, staged_dir=custom)

            self.assertEqual(summary["staged_dir"], custom)
            self.assertTrue(os.path.isfile(os.path.join(custom, BUNDLE_NAME)))


class TestPrepareJobInputsDispatch(unittest.TestCase):
    """ds.jobs.prepare_inputs dispatches through the app-profile registry."""

    def test_simcenter_app_patches_and_bundles(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir, workflow_path = _make_input_dir(root)

            summary = prepare_job_inputs("simcenter-uq-stampede3", input_dir)

            expected_backend = DEFAULT_BACKEND_DIRS["simcenter-uq-stampede3"]
            with open(workflow_path) as f:
                patched = json.load(f)
            self.assertEqual(patched["remoteAppDir"], expected_backend)
            self.assertNotEqual(summary["staged_dir"], input_dir)
            self.assertTrue(os.path.isfile(summary["bundle"]))

    def test_app_without_profile_is_noop(self):
        with tempfile.TemporaryDirectory() as root:
            summary = prepare_job_inputs("opensees-mp-s3", root)

            self.assertEqual(summary["app_id"], "opensees-mp-s3")
            self.assertEqual(summary["input_dir"], root)
            self.assertEqual(summary["staged_dir"], root)
            self.assertFalse(summary["prepared"])

    def test_missing_input_dir_raises(self):
        with self.assertRaises(ValueError):
            prepare_job_inputs("opensees-mp-s3", "/nonexistent/dir/xyz")


class TestSimCenterPrepareInputs(unittest.TestCase):
    """The SimCenter implementation behind the dispatch."""

    def test_returns_workflow_summary(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir, workflow_path = _make_input_dir(root)

            summary = prepare_inputs(input_dir, bundle=False)

            self.assertEqual(summary["workflow_json"], workflow_path)
            self.assertEqual(summary["uq_engine"], "SimCenterUQ")
            self.assertEqual(summary["uq_type"], "Sensitivity Analysis")
            self.assertEqual(summary["random_variables"], ["Dr", "G0", "hpo"])
            self.assertEqual(summary["edps"], ["nCycles010_1", "nCycles013"])

    def test_explicit_backend_dir_overrides_registry(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir, workflow_path = _make_input_dir(root)

            prepare_inputs(
                input_dir, backend_dir="/custom/backend/v1.0.0", bundle=False
            )

            with open(workflow_path) as f:
                patched = json.load(f)
            self.assertEqual(patched["remoteAppDir"], "/custom/backend/v1.0.0")

    def test_unknown_app_without_backend_dir_raises(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir, _ = _make_input_dir(root)
            with self.assertRaises(ValueError):
                prepare_inputs(input_dir, app_id="simcenter-uq-unknown-system")

    def test_missing_workflow_json_raises(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FileNotFoundError):
                prepare_inputs(root)


if __name__ == "__main__":
    unittest.main()
