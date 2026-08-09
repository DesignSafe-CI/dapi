import collections
import errno
import json
import os
import tempfile
import unittest
from unittest import mock

from dapi.simcenter import _require_free_space, prepare_inputs

_usage = collections.namedtuple("usage", "total used free")


def _make_input_dir(root):
    input_dir = os.path.join(root, "DS_input")
    templatedir = os.path.join(input_dir, "tmp.SimCenter", "templatedir")
    os.makedirs(templatedir)
    workflow = {
        "UQ": {"uqEngine": "SimCenterUQ", "uqType": "Sensitivity Analysis"},
        "randomVariables": [{"name": "Dr"}],
        "EDP": [{"name": "nCycles"}],
        "remoteAppDir": "C:/anywhere",
        "remoteAppWorkingDir": "C:/anywhere",
    }
    with open(os.path.join(templatedir, "scInput.json"), "w") as f:
        json.dump(workflow, f)
    with open(os.path.join(templatedir, "driver"), "w") as f:
        f.write("echo driver\n")
    return input_dir


class TestFreeSpaceGuard(unittest.TestCase):
    def test_insufficient_space_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir = _make_input_dir(root)
            with mock.patch(
                "dapi.simcenter.shutil.disk_usage",
                return_value=_usage(total=100, used=90, free=10),
            ):
                with self.assertRaises(OSError) as ctx:
                    prepare_inputs(input_dir)
            msg = str(ctx.exception)
            self.assertIn("GB is free", msg)
            self.assertIn("staged_dir", msg)

    def test_sufficient_space_stages_normally(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir = _make_input_dir(root)
            summary = prepare_inputs(input_dir)
            self.assertTrue(os.path.exists(summary["staged_dir"]))

    def test_probe_climbs_to_existing_parent(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "does", "not", "exist", "yet")
            # must not raise on a target whose directories are not created yet
            _require_free_space(target, needed=1)


class TestWriteTimeEnospc(unittest.TestCase):
    def test_mid_write_enospc_cleans_up_and_explains(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir = _make_input_dir(root)
            with mock.patch(
                "dapi.simcenter._bundle_inputs",
                side_effect=OSError(errno.ENOSPC, "No space left on device"),
            ):
                with self.assertRaises(OSError) as ctx:
                    prepare_inputs(input_dir)
            msg = str(ctx.exception)
            self.assertIn("Ran out of disk space", msg)
            self.assertIn("staged_dir", msg)
            self.assertFalse(os.path.exists(input_dir + "_staged"))

    def test_other_oserror_passes_through_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            input_dir = _make_input_dir(root)
            with mock.patch(
                "dapi.simcenter._bundle_inputs",
                side_effect=OSError(errno.EACCES, "Permission denied"),
            ):
                with self.assertRaises(OSError) as ctx:
                    prepare_inputs(input_dir)
            self.assertEqual(ctx.exception.errno, errno.EACCES)


if __name__ == "__main__":
    unittest.main()
