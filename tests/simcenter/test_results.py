import io
import unittest
import zipfile
from unittest.mock import MagicMock

from dapi.exceptions import FileOperationError
from dapi.jobs import SubmittedJob
from dapi.simcenter import get_results, parse_sensitivity_indices

# Trimmed from a real SimCenterUQ sensitivity run (quoFEM on Stampede3).
DAKOTA_OUT = """\
* data generation
Monte Carlo
* number of input combinations
3
* input names
Dr
G0
hpo
* number of aggregated outputs
0
* number of outputs
2
* output names
nCycles010_1
nCycles013
* Sm(Dr) Sm(G0) Sm(hpo) St(Dr) St(G0) St(hpo)
0.70525205 0.02077442 0.20214571 0.74348871 0.02077442 0.20653809
0.73873876 0.04916962 0.15228061 0.77498626 0.04916962 0.15228061
* number of samples
500
"""

DAKOTA_TAB = """\
idx Dr G0 hpo nCycles010_1 nCycles013
1 0.208492 984.40269 2.750463 12.25 13.25
2 0.186365 796.35018 2.275522 8.50 9.50
3 0.322015 1201.11840 1.902611 15.75 16.75
"""


def _make_results_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("results/dakota.out", DAKOTA_OUT)
        zf.writestr("results/dakotaTab.out", DAKOTA_TAB)
        zf.writestr("results/dakota.err", "")
    return buffer.getvalue()


def _make_job(mock_tapis, app_id="simcenter-uq-stampede3"):
    """Build a SubmittedJob with pre-cached details, bypassing __init__'s
    isinstance check so a MagicMock Tapis client can be injected."""
    job = SubmittedJob.__new__(SubmittedJob)
    job._tapis = mock_tapis
    job.uuid = "test-uuid-007"
    job._last_status = "FINISHED"
    details = MagicMock()
    details.appId = app_id
    details.status = "FINISHED"
    details.archiveSystemId = "designsafe.storage.default"
    details.archiveSystemDir = "testuser/tapis-jobs-archive/2026-08-07Z/test-uuid-007"
    job._job_details = details
    return job


class TestParseSensitivityIndices(unittest.TestCase):
    def test_parses_real_format(self):
        indices = parse_sensitivity_indices(DAKOTA_OUT)

        self.assertIsNotNone(indices)
        self.assertEqual(list(indices.index), ["nCycles010_1", "nCycles013"])
        self.assertEqual(
            list(indices.columns),
            ["Sm(Dr)", "Sm(G0)", "Sm(hpo)", "St(Dr)", "St(G0)", "St(hpo)"],
        )
        self.assertAlmostEqual(indices.loc["nCycles010_1", "Sm(Dr)"], 0.70525205)
        self.assertAlmostEqual(indices.loc["nCycles013", "St(hpo)"], 0.15228061)

    def test_returns_none_without_sensitivity_block(self):
        self.assertIsNone(parse_sensitivity_indices("no indices here\n"))


class TestJobGetResultsDispatch(unittest.TestCase):
    """SubmittedJob.get_results() dispatches through the app-profile
    registry using the job's appId."""

    def test_simcenter_job_returns_parsed_results(self):
        mock_tapis = MagicMock()
        mock_tapis.files.getContents.return_value = _make_results_zip()
        job = _make_job(mock_tapis)

        results = job.get_results()

        self.assertEqual(len(results.samples), 3)
        self.assertIn("nCycles013", results.samples.columns)
        self.assertIsNotNone(results.sobol_indices)
        self.assertEqual(len(results.sobol_indices), 2)
        self.assertIn("results/dakotaTab.out", results.archive_files)

        _, called_kwargs = mock_tapis.files.getContents.call_args
        self.assertEqual(called_kwargs["systemId"], "designsafe.storage.default")
        self.assertEqual(
            called_kwargs["path"],
            "testuser/tapis-jobs-archive/2026-08-07Z/test-uuid-007/results.zip",
        )

    def test_app_without_parser_raises(self):
        job = _make_job(MagicMock(), app_id="opensees-mp-s3")

        with self.assertRaises(FileOperationError):
            job.get_results()


class TestGetResultsImplementation(unittest.TestCase):
    """The SimCenter implementation behind the dispatch."""

    def test_missing_dakota_tab_raises(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("results/dakota.err", "boom")
        mock_tapis = MagicMock()
        mock_tapis.files.getContents.return_value = buffer.getvalue()

        with self.assertRaises(FileOperationError):
            get_results(mock_tapis, _make_job(mock_tapis))

    def test_invalid_zip_raises(self):
        mock_tapis = MagicMock()
        mock_tapis.files.getContents.return_value = b"not a zip"

        with self.assertRaises(FileOperationError):
            get_results(mock_tapis, _make_job(mock_tapis))


if __name__ == "__main__":
    unittest.main()
