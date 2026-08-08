import json
import logging
import os
import tempfile
import unittest

import dapi
from dapi.simcenter import prepare_inputs


def _make_input_dir(root):
    input_dir = os.path.join(root, "DS_input")
    templatedir = os.path.join(input_dir, "tmp.SimCenter", "templatedir")
    os.makedirs(templatedir)
    workflow = {
        "UQ": {"uqEngine": "SimCenterUQ", "uqType": "Sensitivity Analysis"},
        "randomVariables": [{"name": "Dr"}],
        "EDP": [{"name": "nCycles"}],
        "remoteAppDir": "C:/local",
        "remoteAppWorkingDir": "C:/local",
    }
    with open(os.path.join(templatedir, "scInput.json"), "w") as f:
        json.dump(workflow, f)
    return input_dir


class TestLogging(unittest.TestCase):
    def tearDown(self):
        dapi.set_log_level("INFO")

    def test_set_log_level_accepts_names_and_quiet(self):
        logger = logging.getLogger("dapi")
        dapi.set_log_level("DEBUG")
        self.assertEqual(logger.level, logging.DEBUG)
        dapi.set_log_level("QUIET")
        self.assertEqual(logger.level, logging.CRITICAL)
        dapi.set_log_level(logging.WARNING)
        self.assertEqual(logger.level, logging.WARNING)

    def test_prepare_inputs_logs_debug_detail_and_info_milestone(self):
        logger = logging.getLogger("dapi")
        with tempfile.TemporaryDirectory() as root:
            input_dir = _make_input_dir(root)
            records = []
            handler = logging.Handler()
            handler.emit = lambda record: records.append(record)
            logger.addHandler(handler)
            old_level = logger.level
            logger.setLevel(logging.DEBUG)
            try:
                prepare_inputs(input_dir)
            finally:
                logger.setLevel(old_level)
                logger.removeHandler(handler)

        by_level = {}
        for r in records:
            by_level.setdefault(r.levelname, []).append(r.getMessage())
        # Milestone at INFO
        self.assertTrue(
            any("Bundled" in m for m in by_level.get("INFO", [])),
            by_level,
        )
        # Chatty details demoted to DEBUG
        self.assertTrue(
            any("remoteAppDir" in m for m in by_level.get("DEBUG", [])),
            by_level,
        )
        # Nothing chatty left at INFO
        self.assertFalse(
            any("UQ engine" in m for m in by_level.get("INFO", [])),
            by_level,
        )


if __name__ == "__main__":
    unittest.main()
