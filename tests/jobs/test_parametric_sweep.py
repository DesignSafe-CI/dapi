import unittest
import tempfile
from pathlib import Path

import pandas as pd

from dapi.launcher import generate_sweep


class TestGenerate(unittest.TestCase):
    """Tests for generate_sweep() writing mode."""

    def test_empty_sweep_returns_base_command(self):
        with tempfile.TemporaryDirectory() as d:
            cmds = generate_sweep("python run.py", {}, d)
            self.assertEqual(cmds, ["python run.py"])

    def test_single_param(self):
        with tempfile.TemporaryDirectory() as d:
            cmds = generate_sweep(
                "python run.py --alpha ALPHA", {"ALPHA": [1, 2, 3]}, d
            )
            self.assertEqual(len(cmds), 3)
            self.assertEqual(cmds[0], "python run.py --alpha 1")
            self.assertEqual(cmds[2], "python run.py --alpha 3")

    def test_multi_param_cartesian_product(self):
        with tempfile.TemporaryDirectory() as d:
            cmds = generate_sweep(
                "python run.py --a A --b B", {"A": [1, 2], "B": [10, 20]}, d
            )
            self.assertEqual(len(cmds), 4)
            self.assertIn("python run.py --a 1 --b 10", cmds)
            self.assertIn("python run.py --a 2 --b 20", cmds)

    def test_deterministic_order(self):
        with tempfile.TemporaryDirectory() as d:
            cmds = generate_sweep("X Y", {"X": [1, 2], "Y": ["a", "b"]}, d)
            self.assertEqual(cmds, ["1 a", "1 b", "2 a", "2 b"])

    def test_token_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            cmds = generate_sweep(
                "echo ALPHA", {"ALPHA": [1]}, d, placeholder_style="token"
            )
            self.assertEqual(cmds, ["echo 1"])

    def test_braces_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            cmds = generate_sweep(
                "echo {ALPHA}", {"ALPHA": [1]}, d, placeholder_style="braces"
            )
            self.assertEqual(cmds, ["echo 1"])

    def test_env_vars_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            cmds = generate_sweep(
                'run --out "$WORK/$SLURM_JOB_ID" --a A', {"A": [1]}, d
            )
            self.assertIn("$WORK", cmds[0])
            self.assertIn("$SLURM_JOB_ID", cmds[0])

    def test_float_values(self):
        with tempfile.TemporaryDirectory() as d:
            cmds = generate_sweep("run --mass MASS", {"MASS": [4.19, 4.39]}, d)
            self.assertEqual(cmds[0], "run --mass 4.19")

    def test_string_sweep_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(TypeError):
                generate_sweep("echo X", {"X": "bad"}, d)

    def test_empty_sequence_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                generate_sweep("echo X", {"X": []}, d)

    def test_invalid_placeholder_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                generate_sweep("echo X", {"X": [1]}, d, placeholder_style="bad")

    def test_missing_directory_raises(self):
        with self.assertRaises(ValueError):
            generate_sweep("echo X", {"X": [1]})

    def test_writes_both_files(self):
        with tempfile.TemporaryDirectory() as d:
            generate_sweep("cmd --a A", {"A": [1, 2]}, d)
            self.assertTrue((Path(d) / "runsList.txt").exists())
            self.assertTrue((Path(d) / "call_pylauncher.py").exists())

    def test_tasklist_format(self):
        with tempfile.TemporaryDirectory() as d:
            generate_sweep("cmd --a A", {"A": [1, 2, 3]}, d)
            content = (Path(d) / "runsList.txt").read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            self.assertEqual(lines, ["cmd --a 1", "cmd --a 2", "cmd --a 3"])
            self.assertTrue(content.endswith("\n"))

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            deep = Path(d) / "deep" / "nested"
            generate_sweep("cmd", {}, deep)
            self.assertTrue((deep / "runsList.txt").exists())

    def test_launcher_script_no_debug(self):
        with tempfile.TemporaryDirectory() as d:
            generate_sweep("cmd", {}, d)
            content = (Path(d) / "call_pylauncher.py").read_text(encoding="utf-8")
            self.assertIn("import pylauncher", content)
            self.assertIn('ClassicLauncher("runsList.txt")', content)
            self.assertNotIn("debug", content)

    def test_launcher_script_with_debug(self):
        with tempfile.TemporaryDirectory() as d:
            generate_sweep("cmd", {}, d, debug="host+job")
            content = (Path(d) / "call_pylauncher.py").read_text(encoding="utf-8")
            self.assertIn('debug="host+job"', content)


class TestPreview(unittest.TestCase):
    """Tests for generate_sweep(preview=True)."""

    def test_returns_dataframe(self):
        df = generate_sweep("cmd", {"A": [1, 2], "B": [10, 20]}, preview=True)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (4, 2))

    def test_empty_sweep(self):
        df = generate_sweep("cmd", {}, preview=True)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)

    def test_column_order(self):
        df = generate_sweep("cmd", {"BETA": [1], "ALPHA": [2]}, preview=True)
        self.assertEqual(list(df.columns), ["BETA", "ALPHA"])

    def test_values(self):
        df = generate_sweep("cmd", {"X": [1, 2], "Y": [10, 20]}, preview=True)
        self.assertEqual(df.iloc[0]["X"], 1)
        self.assertEqual(df.iloc[0]["Y"], 10)

    def test_no_files_written(self):
        with tempfile.TemporaryDirectory() as d:
            generate_sweep("cmd", {"A": [1]}, d, preview=True)
            self.assertFalse((Path(d) / "runsList.txt").exists())

    def test_directory_not_required(self):
        # Should not raise even without directory
        df = generate_sweep("cmd", {"A": [1]}, preview=True)
        self.assertEqual(len(df), 1)

    def test_validation_still_applies(self):
        with self.assertRaises(TypeError):
            generate_sweep("cmd", {"X": "bad"}, preview=True)


if __name__ == "__main__":
    unittest.main()
