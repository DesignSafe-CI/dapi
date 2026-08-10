import unittest
from types import SimpleNamespace

from dapi.workflows import (
    JobTask,
    OutputRef,
    Workflow,
    WorkflowExecutionError,
    WorkflowValidationError,
)


def _job(name, **extra):
    d = {"name": name, "appId": "python-s3"}
    d.update(extra)
    return d


class TestValidation(unittest.TestCase):
    def test_duplicate_id_rejected(self):
        wf = Workflow("w")
        wf.add(JobTask("a", _job("a")))
        with self.assertRaises(WorkflowValidationError):
            wf.add(JobTask("a", _job("a")))

    def test_unknown_dependency_rejected(self):
        wf = Workflow("w")
        wf.add(JobTask("a", _job("a")), depends_on=["ghost"])
        with self.assertRaises(WorkflowValidationError):
            wf.validate()

    def test_cycle_rejected(self):
        wf = Workflow("w")
        wf.add(JobTask("a", _job("a")), depends_on=["b"])
        wf.add(JobTask("b", _job("b")), depends_on=["a"])
        with self.assertRaises(WorkflowValidationError):
            wf.validate()

    def test_output_ref_implies_dependency(self):
        wf = Workflow("w")
        a = wf.add(JobTask("a", _job("a")))
        wf.add(JobTask("b", _job("b", inputUri=a.output("archive_uri"))))
        self.assertIn("a", wf._deps["b"])
        wf.validate()

    def test_ref_to_unknown_task_caught_by_validate(self):
        wf = Workflow("w")
        wf.add(JobTask("b", _job("b", x=OutputRef("nope", "archive_uri"))))
        with self.assertRaises(WorkflowValidationError):
            wf.validate()

    def test_non_jobtask_rejected(self):
        wf = Workflow("w")
        with self.assertRaises(WorkflowValidationError):
            wf.add(lambda: None)


class TestCompile(unittest.TestCase):
    def _ml_graph(self):
        wf = Workflow("ml")
        sweep = wf.add(JobTask("sweep", _job("sweep")))
        train_job = _job("train")
        train_job["fileInputs"] = [
            {
                "name": "Input Directory",
                "sourceUrl": sweep.output("archive_uri", suffix="/inputDirectory"),
            }
        ]
        wf.add(JobTask("train", job_dict=train_job))
        return wf

    def test_deterministic_archives_and_ref_resolution(self):
        wf = self._ml_graph()
        tasks, archives = wf.compile("user1", "r1")
        by_id = {t["id"]: t for t in tasks}
        self.assertEqual(
            by_id["sweep"]["tapis_job_def"]["archiveSystemDir"],
            "user1/dapi-workflows/ml/r1/sweep",
        )
        self.assertEqual(
            by_id["train"]["tapis_job_def"]["fileInputs"][0]["sourceUrl"],
            "tapis://designsafe.storage.default/user1/dapi-workflows/ml/r1/sweep/inputDirectory",
        )
        self.assertEqual(by_id["train"]["depends_on"], [{"id": "sweep-gate"}])
        self.assertEqual(by_id["sweep-gate"]["type"], "function")
        self.assertEqual(by_id["sweep-gate"]["depends_on"], [{"id": "sweep"}])
        self.assertEqual(by_id["sweep"]["type"], "tapis_job")
        self.assertEqual(
            archives["train"],
            "tapis://designsafe.storage.default/user1/dapi-workflows/ml/r1/train",
        )

    def test_unresolvable_output_key_rejected(self):
        wf = Workflow("w")
        a = wf.add(JobTask("a", _job("a")))
        wf.add(JobTask("b", _job("b", x=a.output("uuid"))))
        with self.assertRaises(WorkflowValidationError):
            wf.compile("user1", "r1")

    def test_gate_only_for_parents_with_children(self):
        wf = Workflow("solo")
        wf.add(JobTask("only", _job("only")))
        tasks, _ = wf.compile("user1", "r1")
        self.assertEqual([t["id"] for t in tasks], ["only"])

    def test_gate_id_collision_rejected(self):
        wf = Workflow("w")
        wf.add(JobTask("a", _job("a")))
        wf.add(JobTask("a-gate", _job("g")), depends_on=["a"])
        with self.assertRaises(WorkflowValidationError):
            wf.compile("user1", "r1")

    def test_source_job_dicts_not_mutated(self):
        wf = self._ml_graph()
        wf.compile("user1", "r1")
        self.assertNotIn("archiveSystemDir", wf._tasks["sweep"].job_dict)


class TestRunTapisBackend(unittest.TestCase):
    """The internal server-side executor (_run_tapis), kept ready for the
    silent flip to the Tapis Workflows engine once the tenant allows it."""

    def _make_ds(self, run_statuses=("completed",), exec_statuses=None):
        calls = {}

        class _WF:
            def getGroup(self, group_id):
                return SimpleNamespace(id=group_id)

            def createGroup(self, id):
                calls["group_created"] = id

            def createPipeline(self, **kw):
                calls["pipeline"] = kw

            def runPipeline(self, **kw):
                calls["run"] = kw

            def listPipelineRuns(self, **kw):
                status = run_statuses[
                    min(calls.setdefault("polls", 0), len(run_statuses) - 1)
                ]
                calls["polls"] += 1
                return [SimpleNamespace(status=status, uuid="run-1")]

            def listTaskExecutions(self, **kw):
                return [
                    SimpleNamespace(task_id=t, status=s, last_message=None)
                    for t, s in (exec_statuses or {}).items()
                ]

        class _Tapis:
            username = "user1"
            workflows = _WF()

        class _DS:
            tapis = _Tapis()

        return _DS(), calls

    def test_completed_pipeline_returns_results(self):
        ds, calls = self._make_ds(
            exec_statuses={"sweep": "completed", "train": "completed"}
        )
        wf = Workflow("ml")
        sweep = wf.add(JobTask("sweep", _job("sweep")))
        train_job = _job(
            "train", src=sweep.output("archive_uri", suffix="/inputDirectory")
        )
        wf.add(JobTask("train", job_dict=train_job))
        results = wf._run_tapis(ds, "g", "r1", 0, 240, False)
        self.assertEqual(results["train"]["status"], "completed")
        self.assertEqual(
            results["sweep"]["archive_uri"],
            "tapis://designsafe.storage.default/user1/dapi-workflows/ml/r1/sweep",
        )
        self.assertEqual(calls["pipeline"]["id"], "ml-r1")

    def test_failed_run_raises_with_task_detail(self):
        ds, _ = self._make_ds(
            run_statuses=("submitted", "failed"), exec_statuses={"sweep": "failed"}
        )
        wf = Workflow("f")
        wf.add(JobTask("sweep", _job("sweep")))
        with self.assertRaises(WorkflowExecutionError) as ctx:
            wf._run_tapis(ds, "g", "r", 0, 240, False)
        self.assertIn("sweep=failed", str(ctx.exception))


class _StubJob:
    """A SubmittedJob stand-in that walks a scripted status sequence."""

    TERMINAL_STATES = ["FINISHED", "FAILED", "CANCELLED", "STOPPED"]

    def __init__(self, uuid, statuses, last_message=None):
        self.uuid = uuid
        self._seq = list(statuses)
        self.last_message = last_message

    def get_status(self, force_refresh=True):
        return self._seq.pop(0) if len(self._seq) > 1 else self._seq[0]


class _StubJobs:
    """Records submissions; hands each task its scripted status sequence."""

    def __init__(self, statuses_by_name, fail_submit=()):
        self.statuses = statuses_by_name
        self.fail_submit = set(fail_submit)
        self.submitted = []  # (name, job_def) in submission order

    def submit(self, job_def):
        name = job_def["name"]
        if name in self.fail_submit:
            raise RuntimeError("allocation not active")
        self.submitted.append((name, job_def))
        return _StubJob(
            f"uuid-{name}", self.statuses[name], last_message=f"{name} says boom"
        )


def _dapi_ds(statuses_by_name, fail_submit=()):
    ds = SimpleNamespace()
    ds.tapis = SimpleNamespace(username="user1")
    ds.jobs = _StubJobs(statuses_by_name, fail_submit)
    return ds


class TestRun(unittest.TestCase):
    """The public run() path: dapi coordinates, jobs submitted directly."""

    def _ml_graph(self):
        wf = Workflow("ml")
        sweep = wf.add(JobTask("sweep", _job("sweep")))
        train_job = _job("train")
        train_job["fileInputs"] = [
            {
                "name": "Input Directory",
                "sourceUrl": sweep.output("archive_uri", suffix="/inputDirectory"),
            }
        ]
        wf.add(JobTask("train", job_dict=train_job))
        return wf

    def test_dependent_submits_only_after_upstream_finishes(self):
        ds = _dapi_ds(
            {"sweep": ["QUEUED", "RUNNING", "FINISHED"], "train": ["FINISHED"]}
        )
        results = self._ml_graph().run(ds, run_id="r1", poll_interval=0)
        self.assertEqual([n for n, _ in ds.jobs.submitted], ["sweep", "train"])
        self.assertEqual(results["sweep"]["status"], "completed")
        self.assertEqual(results["train"]["uuid"], "uuid-train")

    def test_compiled_defs_submitted_with_resolved_refs(self):
        ds = _dapi_ds({"sweep": ["FINISHED"], "train": ["FINISHED"]})
        self._ml_graph().run(ds, run_id="r1", poll_interval=0)
        defs = dict(ds.jobs.submitted)
        self.assertEqual(
            defs["sweep"]["archiveSystemDir"], "user1/dapi-workflows/ml/r1/sweep"
        )
        self.assertEqual(
            defs["train"]["fileInputs"][0]["sourceUrl"],
            "tapis://designsafe.storage.default/user1/dapi-workflows/ml/r1/sweep/inputDirectory",
        )

    def test_failed_upstream_blocks_dependent(self):
        ds = _dapi_ds({"sweep": ["FAILED"], "train": ["FINISHED"]})
        with self.assertRaises(WorkflowExecutionError) as ctx:
            self._ml_graph().run(ds, run_id="r1", poll_interval=0)
        self.assertEqual([n for n, _ in ds.jobs.submitted], ["sweep"])
        self.assertIn("sweep=failed", str(ctx.exception))
        self.assertIn("sweep says boom", str(ctx.exception))
        self.assertIn("train=blocked", str(ctx.exception))

    def test_submission_failure_fails_task_and_blocks_dependent(self):
        ds = _dapi_ds({"train": ["FINISHED"]}, fail_submit={"sweep"})
        with self.assertRaises(WorkflowExecutionError) as ctx:
            self._ml_graph().run(ds, run_id="r1", poll_interval=0)
        self.assertEqual(ds.jobs.submitted, [])
        self.assertIn("allocation not active", str(ctx.exception))
        self.assertIn("train=blocked", str(ctx.exception))

    def test_independent_tasks_run_concurrently(self):
        # both roots must be submitted before either finishes
        wf = Workflow("par")
        wf.add(JobTask("a", _job("a")))
        wf.add(JobTask("b", _job("b")))
        ds = _dapi_ds({"a": ["RUNNING", "FINISHED"], "b": ["RUNNING", "FINISHED"]})
        wf.run(ds, run_id="r1", poll_interval=0)
        self.assertEqual({n for n, _ in ds.jobs.submitted}, {"a", "b"})

    def test_results_shape_matches_tapis_backend(self):
        ds = _dapi_ds({"sweep": ["FINISHED"], "train": ["FINISHED"]})
        results = self._ml_graph().run(ds, run_id="r1", poll_interval=0)
        self.assertEqual(
            set(results["sweep"]), {"status", "message", "archive_uri", "uuid"}
        )
        self.assertEqual(
            results["sweep"]["archive_uri"],
            "tapis://designsafe.storage.default/user1/dapi-workflows/ml/r1/sweep",
        )


class TestVisualize(unittest.TestCase):
    def test_visualize_returns_figure_with_edge_labels(self):
        try:
            import matplotlib
        except ImportError:
            self.skipTest("matplotlib not installed")
        matplotlib.use("Agg")
        wf = Workflow("viz")
        a = wf.add(JobTask("a", _job("a")))
        wf.add(JobTask("b", _job("b", src=a.output("archive_uri"))))
        fig = wf.visualize()
        texts = [t.get_text() for ax in fig.axes for t in ax.texts]
        self.assertIn("a", texts)
        self.assertIn("b", texts)
        self.assertIn("archive_uri", texts)  # the edge label


class TestSequenceJob(unittest.TestCase):
    def test_driver_uploaded_and_job_uses_bash(self):
        from dapi.workflows import sequence_job

        class _Files:
            def __init__(self):
                self.uploads = []

            def upload(self, local, remote):
                with open(local) as f:
                    self.uploads.append((remote, f.read()))

        class _Jobs:
            def generate(self, **kw):
                return kw

        class _DS:
            files = _Files()
            jobs = _Jobs()

        ds = _DS()
        job = sequence_job(
            ds,
            steps=["python3 run.py", "bash post.sh"],
            input_dir_uri="tapis://designsafe.storage.default/u/inputs/",
            allocation="TEST",
            extra_env_vars=[{"key": "BINARY", "value": "python3"}],
        )
        remote, body = ds.files.uploads[0]
        self.assertEqual(
            remote, "tapis://designsafe.storage.default/u/inputs/dapi_sequence.sh"
        )
        self.assertIn("set -euo pipefail", body)
        self.assertLess(body.index("python3 run.py"), body.index("bash post.sh"))
        self.assertEqual(job["script_filename"], "dapi_sequence.sh")
        binaries = [e for e in job["extra_env_vars"] if e["key"] == "BINARY"]
        self.assertEqual(binaries, [{"key": "BINARY", "value": "bash"}])


if __name__ == "__main__":
    unittest.main()
