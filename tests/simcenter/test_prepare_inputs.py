import json
import os
import tempfile
import unittest

from dapi.jobs import prepare_job_inputs
from dapi.simcenter import DEFAULT_BACKEND_DIRS, prepare_inputs


def _make_input_dir(root):
    """Create a minimal SimCenter input directory with a workflow JSON."""
    templatedir = os.path.join(root, "tmp.SimCenter", "templatedir")
    os.makedirs(templatedir)
    workflow = {
        "UQ": {"uqEngine": "SimCenterUQ", "uqType": "Sensitivity Analysis"},
        "randomVariables": [{"name": "Dr"}, {"name": "G0"}, {"name": "hpo"}],
        "EDP": [{"name": "nCycles010_1"}, {"name": "nCycles013"}],
        "remoteAppDir": "C:/Users/someone/Desktop/SimCenterBackendApplications",
        "remoteAppWorkingDir": "C:/Users/someone/Desktop/SimCenterBackendApplications",
    }
    path = os.path.join(templatedir, "scInput.json")
    with open(path, "w") as f:
        json.dump(workflow, f)
    return path


class TestPrepareJobInputsDispatch(unittest.TestCase):
    """ds.jobs.prepare_inputs dispatches through the app-profile registry."""

    def test_simcenter_app_patches_workflow_json(self):
        with tempfile.TemporaryDirectory() as root:
            workflow_path = _make_input_dir(root)

            summary = prepare_job_inputs("simcenter-uq-stampede3", root)

            expected_backend = DEFAULT_BACKEND_DIRS["simcenter-uq-stampede3"]
            with open(workflow_path) as f:
                patched = json.load(f)
            self.assertEqual(patched["remoteAppDir"], expected_backend)
            self.assertEqual(patched["remoteAppWorkingDir"], expected_backend)
            self.assertEqual(summary["backend_dir"], expected_backend)

    def test_app_without_profile_is_noop(self):
        with tempfile.TemporaryDirectory() as root:
            summary = prepare_job_inputs("opensees-mp-s3", root)

            self.assertEqual(summary["app_id"], "opensees-mp-s3")
            self.assertEqual(summary["input_dir"], root)
            self.assertFalse(summary["prepared"])

    def test_missing_input_dir_raises(self):
        with self.assertRaises(ValueError):
            prepare_job_inputs("opensees-mp-s3", "/nonexistent/dir/xyz")


class TestSimCenterPrepareInputs(unittest.TestCase):
    """The SimCenter implementation behind the dispatch."""

    def test_returns_workflow_summary(self):
        with tempfile.TemporaryDirectory() as root:
            workflow_path = _make_input_dir(root)

            summary = prepare_inputs(root)

            self.assertEqual(summary["workflow_json"], workflow_path)
            self.assertEqual(summary["uq_engine"], "SimCenterUQ")
            self.assertEqual(summary["uq_type"], "Sensitivity Analysis")
            self.assertEqual(summary["random_variables"], ["Dr", "G0", "hpo"])
            self.assertEqual(summary["edps"], ["nCycles010_1", "nCycles013"])

    def test_explicit_backend_dir_overrides_registry(self):
        with tempfile.TemporaryDirectory() as root:
            workflow_path = _make_input_dir(root)

            prepare_inputs(root, backend_dir="/custom/backend/v1.0.0")

            with open(workflow_path) as f:
                patched = json.load(f)
            self.assertEqual(patched["remoteAppDir"], "/custom/backend/v1.0.0")

    def test_unknown_app_without_backend_dir_raises(self):
        with tempfile.TemporaryDirectory() as root:
            _make_input_dir(root)
            with self.assertRaises(ValueError):
                prepare_inputs(root, app_id="simcenter-uq-unknown-system")

    def test_missing_workflow_json_raises(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FileNotFoundError):
                prepare_inputs(root)


if __name__ == "__main__":
    unittest.main()
