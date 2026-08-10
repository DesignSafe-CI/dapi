# dapi/workflows.py
"""DAG workflows over dapi jobs, with interchangeable execution backends.

A :class:`Workflow` is an explicit directed acyclic graph of Tapis jobs.
Dependencies are declared, never inferred from ordering; referencing
another task's output also declares the edge. ``validate()`` rejects
cycles, duplicate ids, and references to unknown tasks before anything
is submitted.

Every task runs as a real Tapis job on HPC. ``run()`` coordinates the
graph, submitting each job with the user's credentials when its
dependencies finish and running independent branches in parallel. Each
task receives a deterministic archive directory at compile time, which
lets ``OutputRef("archive_uri", suffix=...)`` resolve to a concrete
``tapis://`` path before submission: one recursive directory input per
edge.

How the coordination executes is an internal detail. The graph compiles
to the Tapis Workflows pipeline task format, and the module carries two
interchangeable executors over that same compiled pipeline: the current
default drives the DAG from the calling process via direct Jobs-API
submissions, and ``_run_tapis`` hands the pipeline to the Tapis
Workflows engine for server-side orchestration. The private ``_BACKEND``
switch flips to the engine once TACC authorizes the Workflows service in
the designsafe tenant; users never select this, and ``run()``'s API does
not change.

For a linear sequence of steps that should share one node and one queue
wait, see :func:`sequence_job`, which packs the steps into a single job
that can then be a node in a larger graph.

Example:
    >>> from dapi.workflows import Workflow, JobTask
    >>> wf = Workflow("opensees-ml")
    >>> sweep = wf.add(JobTask("sweep", job_dict=sweep_job))
    >>> train_job["fileInputs"][0]["sourceUrl"] = sweep.output(
    ...     "archive_uri", suffix="/inputDirectory"
    ... )
    >>> wf.add(JobTask("train", job_dict=train_job))
    >>> wf.validate()
    >>> results = wf.run(ds)
"""

import copy
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import DapiException

logger = logging.getLogger(__name__)

# Internal execution switch, never user-facing. Flips to "tapis" (the
# Tapis Workflows engine, via _run_tapis) once TACC authorizes the
# Workflows service for job submission in the designsafe tenant.
_BACKEND = "dapi"
_TAPIS_GROUP = "dapi-workflows"
# Base64 of the no-op the gate tasks run (see compile()).
_GATE_CODE = "cHJpbnQoImdhdGU6IHVwc3RyZWFtIGZpbmlzaGVkIik="

__all__ = [
    "Workflow",
    "JobTask",
    "OutputRef",
    "sequence_job",
    "WorkflowValidationError",
    "WorkflowExecutionError",
]


class WorkflowValidationError(DapiException):
    """The workflow graph is not a valid DAG."""


class WorkflowExecutionError(DapiException):
    """The pipeline failed during execution."""


def sequence_job(
    ds,
    steps: List[str],
    input_dir_uri: str,
    driver_name: str = "dapi_sequence.sh",
    app_id: str = "python-s3",
    **generate_kwargs,
) -> Dict[str, Any]:
    """Pack an ordered list of shell steps into ONE Tapis job on one node.

    A workflow's linear segments do not have to pay one queue wait per
    task. This builder writes a small driver script that runs *steps*
    sequentially (fail-fast), uploads it into *input_dir_uri*, and returns
    a job request whose main run executes the driver under ``bash``. All
    steps share the node, the working directory, and the job's Python
    environment, so a step reads the previous step's files directly, no
    archive hop in between.

    Use separate :class:`JobTask` nodes instead when stages need
    different resources (a 48-core sweep and a one-core training step),
    or when a stage fans out to several dependents.

    Args:
        ds: An authenticated ``DSClient``. Used to upload the driver and
            build the job request.
        steps: Shell commands, run in order; the job fails at the first
            failing step.
        input_dir_uri: The job's input directory (a writable DesignSafe
            location, e.g. under MyData); the driver is uploaded here.
        driver_name: Filename for the generated driver script.
        app_id: The generic execution app. Defaults to ``python-s3``.
        **generate_kwargs: Everything else ``ds.jobs.generate`` accepts
            (allocation, node_count, queue, extra_env_vars, ...).

    Returns:
        A job request dict, ready for :class:`JobTask`.

    Example:
        >>> fused = sequence_job(
        ...     ds,
        ...     steps=["python3 call_pylauncher.py", "bash ml_post.sh"],
        ...     input_dir_uri=staged_uri,
        ...     node_count=1,
        ...     cores_per_node=48,
        ...     allocation="MyAlloc",
        ...     queue="skx-dev",
        ... )
        >>> wf.add(JobTask("sweep-and-train", job_dict=fused))
    """
    lines = ["#!/bin/bash", "set -euo pipefail"]
    for i, step in enumerate(steps, 1):
        lines.append(f'echo "[dapi.workflows] step {i}/{len(steps)}: {step}"')
        lines.append(step)
    lines.append(f'echo "[dapi.workflows] all {len(steps)} steps finished"')

    tmp = tempfile.mkdtemp(prefix="dapi-sequence-")
    driver_path = os.path.join(tmp, driver_name)
    with open(driver_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    dest = f"{input_dir_uri.rstrip('/')}/{driver_name}"
    ds.files.upload(driver_path, dest)
    logger.info(f"Sequence driver ({len(steps)} steps) uploaded to {dest}")

    env = [
        e for e in generate_kwargs.pop("extra_env_vars", []) if e.get("key") != "BINARY"
    ]
    env.append({"key": "BINARY", "value": "bash"})
    return ds.jobs.generate(
        app_id=app_id,
        input_dir_uri=input_dir_uri,
        script_filename=driver_name,
        extra_env_vars=env,
        **generate_kwargs,
    )


@dataclass(frozen=True)
class OutputRef:
    """A reference to an output of another task, resolved at compile time.

    Embedding an :class:`OutputRef` in a task's inputs declares a
    dependency on ``task_id`` exactly as listing it in ``depends_on``
    does. ``suffix`` is appended to the resolved value, so a job can
    consume a subfolder of an upstream archive:
    ``sweep.output("archive_uri", suffix="/inputDirectory")``.

    Because archives are assigned deterministically per run, only
    ``archive_uri`` references are resolvable (``uuid`` and ``status``
    do not exist before the run).
    """

    task_id: str
    key: str
    suffix: str = ""

    def __repr__(self) -> str:
        return f"OutputRef({self.task_id}.{self.key}{self.suffix})"


class JobTask:
    """A Tapis job as a workflow node.

    Args:
        task_id: Unique id within the workflow.
        job_dict: A job request as produced by ``ds.jobs.generate()``.
            Values anywhere inside may be :class:`OutputRef` instances;
            they are resolved to concrete paths at compile time.

    Output available to downstream tasks: ``archive_uri`` (the
    deterministic archive directory assigned per run).
    """

    def __init__(self, task_id: str, job_dict: Dict[str, Any]):
        if not task_id or not isinstance(task_id, str):
            raise WorkflowValidationError("Task id must be a non-empty string.")
        if not isinstance(job_dict, dict):
            raise WorkflowValidationError(
                f"Task '{task_id}': job_dict must be a dict (use ds.jobs.generate())."
            )
        self.id = task_id
        self.job_dict = job_dict

    def output(self, key: str = "archive_uri", suffix: str = "") -> OutputRef:
        """Reference an output of this task for use in a downstream task.

        Args:
            key: Output name. Only ``archive_uri`` is resolvable at
                compile time.
            suffix: Appended to the resolved value (e.g.
                ``"/inputDirectory"`` to consume an archive subfolder).
        """
        return OutputRef(self.id, key, suffix)

    def _referenced_tasks(self) -> set:
        return _collect_refs(self.job_dict)


def _collect_refs(obj: Any) -> set:
    refs = set()
    if isinstance(obj, OutputRef):
        refs.add(obj.task_id)
    elif isinstance(obj, dict):
        for v in obj.values():
            refs |= _collect_refs(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            refs |= _collect_refs(v)
    return refs


def _collect_ref_pairs(obj: Any) -> set:
    """(task_id, output key) pairs for every OutputRef inside *obj*."""
    pairs = set()
    if isinstance(obj, OutputRef):
        pairs.add((obj.task_id, obj.key))
    elif isinstance(obj, dict):
        for v in obj.values():
            pairs |= _collect_ref_pairs(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            pairs |= _collect_ref_pairs(v)
    return pairs


def _resolve(obj: Any, outputs: Dict[str, Dict[str, Any]]) -> Any:
    if isinstance(obj, OutputRef):
        task_out = outputs.get(obj.task_id)
        if task_out is None or obj.key not in task_out:
            raise WorkflowValidationError(
                f"Output '{obj.key}' of task '{obj.task_id}' cannot be "
                f"resolved at compile time; only 'archive_uri' can."
            )
        return str(task_out[obj.key]) + obj.suffix if obj.suffix else task_out[obj.key]
    if isinstance(obj, dict):
        return {k: _resolve(v, outputs) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(_resolve(v, outputs) for v in obj)
    return obj


class Workflow:
    """An explicit DAG of Tapis jobs with interchangeable execution backends.

    Args:
        name: Workflow name; used for pipeline ids and archive paths.
    """

    def __init__(self, name: str):
        self.name = name
        self._tasks: Dict[str, JobTask] = {}
        self._deps: Dict[str, set] = {}

    def add(self, task: JobTask, depends_on: Optional[List[str]] = None) -> JobTask:
        """Add a task. Dependencies come from ``depends_on`` plus any
        :class:`OutputRef` embedded in the task's job request.

        Returns the task, so ``task.output(...)`` can be used fluently.
        """
        if not isinstance(task, JobTask):
            raise WorkflowValidationError(
                f"Only JobTask nodes are supported; got {type(task).__name__}. "
                f"Run local Python before building the graph or after run() "
                f"returns."
            )
        if task.id in self._tasks:
            raise WorkflowValidationError(f"Duplicate task id '{task.id}'.")
        self._tasks[task.id] = task
        self._deps[task.id] = set(depends_on or []) | task._referenced_tasks()
        return task

    def validate(self) -> None:
        """Check the graph. Raises WorkflowValidationError on problems.

        Graph mechanics are delegated to the standard library's
        :class:`graphlib.TopologicalSorter`; only dapi-specific checks
        (unknown task references) live here.
        """
        for tid, deps in self._deps.items():
            for d in deps:
                if d not in self._tasks:
                    raise WorkflowValidationError(
                        f"Task '{tid}' depends on unknown task '{d}'."
                    )
        try:
            TopologicalSorter(self._deps).prepare()
        except CycleError as e:
            raise WorkflowValidationError(f"Cycle detected: {e.args[1]}.") from e

    def compile(
        self, username: str, run_id: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Compile the graph to Tapis Workflows task definitions.

        Assigns each task a deterministic archive directory
        (``<username>/dapi-workflows/<name>/<run_id>/<task_id>`` in
        MyData) and resolves every :class:`OutputRef` to the concrete
        ``tapis://`` path it implies.

        Returns:
            (tapis_tasks, archive_uris): the task list for
            ``createPipeline`` and each task's archive URI.
        """
        self.validate()
        outputs: Dict[str, Dict[str, Any]] = {}
        compiled: Dict[str, Dict[str, Any]] = {}
        archives: Dict[str, str] = {}
        for tid, task in self._tasks.items():
            arch_dir = f"{username}/dapi-workflows/{self.name}/{run_id}/{tid}"
            job = copy.deepcopy(task.job_dict)
            job["archiveSystemId"] = "designsafe.storage.default"
            job["archiveSystemDir"] = arch_dir
            # The Workflows engine serializes absent job fields as null,
            # which the Jobs schema rejects; pin the input dir explicitly.
            job.setdefault("execSystemInputDir", "${JobWorkingDir}")
            compiled[tid] = job
            archives[tid] = f"tapis://designsafe.storage.default/{arch_dir}"
            outputs[tid] = {"archive_uri": archives[tid]}
        # The Workflows engine unconditionally injects a parent job's
        # outputs into its children as extra file inputs
        # ("owe-implicit-input-<parent>"), which strict apps reject. A
        # no-op function task between two jobs absorbs the injection
        # while keeping the ordering, so every job that has children
        # gets one gate, and its children depend on the gate instead.
        parents_with_children = {d for deps in self._deps.values() for d in deps}
        for parent in parents_with_children:
            gate_id = f"{parent}-gate"
            if gate_id in self._tasks:
                raise WorkflowValidationError(
                    f"Task id '{gate_id}' collides with an internal gate task."
                )

        tapis_tasks = []
        for tid in self._tasks:
            tapis_tasks.append(
                {
                    "id": tid,
                    "type": "tapis_job",
                    "tapis_job_def": _resolve(compiled[tid], outputs),
                    "poll": True,
                    "depends_on": [
                        {"id": f"{d}-gate"} for d in sorted(self._deps[tid])
                    ],
                }
            )
        for parent in sorted(parents_with_children):
            tapis_tasks.append(
                {
                    "id": f"{parent}-gate",
                    "type": "function",
                    "runtime": "python:3.11-slim",
                    "installer": "pip",
                    "packages": [],
                    "code": _GATE_CODE,
                    "depends_on": [{"id": parent}],
                }
            )
        return tapis_tasks, archives

    def run(
        self,
        ds,
        run_id: Optional[str] = None,
        poll_interval: int = 30,
        timeout_minutes: int = 240,
        progress: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """Execute the workflow. Every task runs as a real Tapis job.

        Each job is submitted with your credentials when its
        dependencies finish; independent branches run in parallel, and
        tasks whose upstream failed are never submitted (reported as
        ``blocked``). Already-submitted jobs keep running on Tapis even
        if this process dies; reattach with ``ds.jobs.job(uuid)``.

        Args:
            ds: An authenticated ``DSClient``.
            run_id: Distinguishes this run's archive paths. Defaults to
                a timestamp.
            poll_interval: Seconds between status polls.
            timeout_minutes: Stop waiting after this long.
            progress: Print timestamped per-task status transitions
                while polling, so a notebook shows each task advancing
                live. Defaults to True.

        Returns:
            Mapping of task id to ``status``, ``message``,
            ``archive_uri``, and ``uuid``.

        Raises:
            WorkflowExecutionError: If the run ends in a failed state,
                with per-task detail.
        """
        run_id = run_id or time.strftime("%Y%m%d-%H%M%S")
        if _BACKEND == "tapis":
            return self._run_tapis(
                ds, _TAPIS_GROUP, run_id, poll_interval, timeout_minutes, progress
            )
        return self._run_dapi(ds, run_id, poll_interval, timeout_minutes, progress)

    def _run_dapi(
        self,
        ds,
        run_id: str,
        poll_interval: int,
        timeout_minutes: int,
        progress: bool,
    ) -> Dict[str, Dict[str, Any]]:
        """Drive the DAG from this process, one direct job submission per task."""
        username = getattr(ds.tapis, "username", None)
        if not username:
            raise WorkflowExecutionError("Cannot determine Tapis username.")
        tapis_tasks, archives = self.compile(username, run_id)
        job_defs = {
            t["id"]: t["tapis_job_def"] for t in tapis_tasks if t["type"] == "tapis_job"
        }

        def _say(msg: str) -> None:
            if progress:
                print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

        results: Dict[str, Dict[str, Any]] = {
            tid: {
                "status": None,
                "message": None,
                "archive_uri": archives[tid],
                "uuid": None,
            }
            for tid in self._tasks
        }
        sorter = TopologicalSorter(self._deps)
        sorter.prepare()
        active: Dict[str, Any] = {}
        last_seen: Dict[str, str] = {}
        failed: set = set()
        _say(f"workflow '{self.name}-{run_id}': {len(job_defs)} tasks")
        deadline = time.time() + timeout_minutes * 60
        while sorter.is_active():
            advanced = False
            for tid in sorter.get_ready():
                upstream_failed = self._deps[tid] & failed
                if upstream_failed:
                    results[tid]["status"] = "blocked"
                    results[tid]["message"] = (
                        f"not submitted; upstream {sorted(upstream_failed)} failed"
                    )
                    failed.add(tid)
                    _say(f"  task {tid}: blocked ({results[tid]['message']})")
                    sorter.done(tid)
                    advanced = True
                    continue
                try:
                    job = ds.jobs.submit(job_defs[tid])
                except Exception as e:  # noqa: BLE001 - any submit failure fails the task
                    results[tid]["status"] = "failed"
                    results[tid]["message"] = str(e)
                    failed.add(tid)
                    _say(f"  task {tid}: submission failed ({str(e)[:100]})")
                    sorter.done(tid)
                    advanced = True
                    continue
                active[tid] = job
                results[tid]["uuid"] = job.uuid
                _say(f"  task {tid}: submitted (job {job.uuid})")

            for tid in list(active):
                job = active[tid]
                try:
                    status = job.get_status()
                except Exception as e:  # noqa: BLE001 - transient poll errors retry
                    logger.debug(f"Status poll for task {tid} failed: {e}")
                    continue
                if last_seen.get(tid) != status:
                    _say(f"  task {tid}: {last_seen.get(tid, 'SUBMITTED')} -> {status}")
                    last_seen[tid] = status
                if status in job.TERMINAL_STATES:
                    if status == "FINISHED":
                        results[tid]["status"] = "completed"
                    else:
                        results[tid]["status"] = "failed"
                        results[tid]["message"] = job.last_message
                        failed.add(tid)
                    sorter.done(tid)
                    del active[tid]
                    advanced = True

            if not sorter.is_active():
                break
            if advanced:
                continue  # newly ready dependents submit without waiting
            if time.time() > deadline:
                running = {t: j.uuid for t, j in active.items()}
                raise WorkflowExecutionError(
                    f"Workflow '{self.name}-{run_id}' still running after "
                    f"{timeout_minutes} minutes. Submitted jobs continue on "
                    f"Tapis (reattach with ds.jobs.job(uuid): {running}); "
                    f"tasks not yet submitted will not start."
                )
            time.sleep(poll_interval)

        if failed:
            raise WorkflowExecutionError(
                f"Workflow '{self.name}-{run_id}' ended failed: "
                + "; ".join(
                    f"{tid}={r['status']} ({str(r['message'])[:120]})"
                    for tid, r in results.items()
                )
            )
        _say(f"workflow '{self.name}-{run_id}': completed")
        logger.info(f"[{self.name}] workflow completed")
        return results

    def _run_tapis(
        self,
        ds,
        group_id: str,
        run_id: str,
        poll_interval: int,
        timeout_minutes: int,
        progress: bool,
    ) -> Dict[str, Dict[str, Any]]:
        """Hand the compiled pipeline to the Tapis Workflows engine."""
        username = getattr(ds.tapis, "username", None)
        if not username:
            raise WorkflowExecutionError("Cannot determine Tapis username.")
        tapis_tasks, archives = self.compile(username, run_id)

        wfapi = ds.tapis.workflows
        try:
            wfapi.getGroup(group_id=group_id)
        except Exception:
            wfapi.createGroup(id=group_id)
            logger.info(f"Created Tapis Workflows group '{group_id}'")

        pipeline_id = f"{self.name}-{run_id}".lower()
        wfapi.createPipeline(
            group_id=group_id, id=pipeline_id, type="workflow", tasks=tapis_tasks
        )
        wfapi.runPipeline(group_id=group_id, pipeline_id=pipeline_id)
        logger.info(
            f"[{self.name}] pipeline '{pipeline_id}' submitted to group "
            f"'{group_id}'; polling every {poll_interval}s"
        )

        def _say(msg: str) -> None:
            if progress:
                print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

        _say(f"pipeline '{pipeline_id}': submitted ({len(tapis_tasks)} tasks)")
        deadline = time.time() + timeout_minutes * 60
        run = None
        last_run_status = None
        last_task_status: Dict[str, Any] = {}
        while time.time() < deadline:
            runs = wfapi.listPipelineRuns(group_id=group_id, pipeline_id=pipeline_id)
            if runs:
                run = runs[0]
                if str(run.status) != last_run_status:
                    _say(f"pipeline '{pipeline_id}': {run.status}")
                    last_run_status = str(run.status)
                try:
                    for te in wfapi.listTaskExecutions(
                        group_id=group_id,
                        pipeline_id=pipeline_id,
                        pipeline_run_uuid=run.uuid,
                    ):
                        tid = getattr(te, "task_id", "?")
                        if tid not in self._tasks:
                            continue  # internal gate tasks stay invisible
                        status = getattr(te, "status", None)
                        if last_task_status.get(tid) != status:
                            msg = getattr(te, "last_message", None)
                            _say(
                                f"  task {tid}: "
                                f"{last_task_status.get(tid, 'created')} -> {status}"
                                + (f"  ({str(msg)[:100]})" if msg else "")
                            )
                            last_task_status[tid] = status
                except Exception:  # noqa: BLE001 - progress detail is best-effort
                    pass
                if str(run.status).lower() in ("completed", "failed", "terminated"):
                    break
            time.sleep(poll_interval)
        else:
            raise WorkflowExecutionError(
                f"Pipeline '{pipeline_id}' still running after "
                f"{timeout_minutes} minutes; it continues server-side. "
                f"Check runs for group '{group_id}'."
            )

        executions = {}
        try:
            for te in wfapi.listTaskExecutions(
                group_id=group_id,
                pipeline_id=pipeline_id,
                pipeline_run_uuid=run.uuid,
            ):
                executions[getattr(te, "task_id", "?")] = {
                    "status": getattr(te, "status", None),
                    "message": getattr(te, "last_message", None),
                }
        except Exception as e:  # noqa: BLE001 - execution detail is best-effort
            logger.debug(f"listTaskExecutions failed: {e}")

        results = {}
        for tid in self._tasks:
            ex = executions.get(tid, {})
            results[tid] = {
                "status": ex.get("status"),
                "message": ex.get("message"),
                "archive_uri": archives[tid],
                "uuid": None,  # the engine submits; job uuids stay server-side
            }
        if str(run.status).lower() != "completed":
            raise WorkflowExecutionError(
                f"Pipeline '{pipeline_id}' ended {run.status}: "
                + "; ".join(
                    f"{tid}={r['status']} ({str(r['message'])[:120]})"
                    for tid, r in results.items()
                )
            )
        logger.info(f"[{self.name}] pipeline completed")
        return results

    def visualize(self, figsize=None):
        """Draw the DAG with matplotlib and return the figure.

        Tasks are laid out left to right by dependency depth. Every edge
        produced by an :class:`OutputRef` is labeled with the output key
        that flows across it, so the data hand-off between tasks is
        visible, not just the ordering.
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.patches import FancyBboxPatch
        except ImportError as e:
            raise ImportError(
                "Workflow.visualize() needs matplotlib: pip install matplotlib"
            ) from e
        self.validate()

        depth: Dict[str, int] = {}

        def _depth(tid: str) -> int:
            if tid not in depth:
                deps = self._deps[tid]
                depth[tid] = 0 if not deps else 1 + max(_depth(d) for d in deps)
            return depth[tid]

        for tid in self._tasks:
            _depth(tid)
        layers: Dict[int, List[str]] = {}
        for tid, d in depth.items():
            layers.setdefault(d, []).append(tid)

        pos: Dict[str, tuple] = {}
        for d, tids in layers.items():
            for i, tid in enumerate(sorted(tids)):
                pos[tid] = (d * 2.6, -(i - (len(tids) - 1) / 2) * 1.4)

        edge_labels: Dict[tuple, str] = {}
        for tid, task in self._tasks.items():
            for dep_id, key in _collect_ref_pairs(task.job_dict):
                edge_labels[(dep_id, tid)] = key

        n_layers = len(layers)
        max_rows = max(len(v) for v in layers.values())
        fig, ax = plt.subplots(figsize=figsize or (2.6 * n_layers, 1.6 * max_rows))
        box_w, box_h = 1.7, 0.7
        for tid, (x, y) in pos.items():
            ax.add_patch(
                FancyBboxPatch(
                    (x - box_w / 2, y - box_h / 2),
                    box_w,
                    box_h,
                    boxstyle="round,pad=0.06",
                    facecolor="#1F3C73",
                    edgecolor="none",
                )
            )
            ax.text(
                x,
                y + 0.08,
                tid,
                ha="center",
                va="center",
                color="white",
                fontsize=11,
                fontweight="bold",
            )
            ax.text(
                x,
                y - 0.18,
                "job",
                ha="center",
                va="center",
                color="white",
                fontsize=8,
                alpha=0.8,
            )
        for tid, deps in self._deps.items():
            for dep in deps:
                x0, y0 = pos[dep]
                x1, y1 = pos[tid]
                ax.annotate(
                    "",
                    xy=(x1 - box_w / 2 - 0.08, y1),
                    xytext=(x0 + box_w / 2 + 0.08, y0),
                    arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.4),
                )
                label = edge_labels.get((dep, tid))
                if label:
                    ax.text(
                        (x0 + x1) / 2,
                        (y0 + y1) / 2 + 0.14,
                        label,
                        ha="center",
                        va="bottom",
                        fontsize=8.5,
                        color="#1F3C73",
                        style="italic",
                    )
        ax.set_xlim(-1.2, (n_layers - 1) * 2.6 + 1.2)
        ax.set_ylim(-max_rows * 0.8 - 0.4, max_rows * 0.8 + 0.4)
        ax.axis("off")
        ax.set_title(f"Workflow: {self.name}", fontsize=12, color="#1F3C73")
        fig.tight_layout()
        return fig
