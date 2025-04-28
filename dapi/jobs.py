# dapi/jobs.py
import time
import json
import os
import urllib.parse
import logging  # Import logging for the timeout warning
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from dataclasses import dataclass, field, asdict
from tqdm.auto import tqdm
from .apps import get_app_details
from .exceptions import (
    JobSubmissionError,
    JobMonitorError,
    FileOperationError,
    AppDiscoveryError,
)

# --- Module-Level Status Constants ---
STATUS_TIMEOUT = "TIMEOUT"
STATUS_INTERRUPTED = "INTERRUPTED"
STATUS_MONITOR_ERROR = "MONITOR_ERROR"
STATUS_UNKNOWN = "UNKNOWN"
TAPIS_TERMINAL_STATES = [
    "FINISHED",
    "FAILED",
    "CANCELLED",
    "STOPPED",
    "ARCHIVING_FAILED",
]


# --- generate_job_request function (Production Ready) ---
def generate_job_request(
    tapis_client: Tapis,
    app_id: str,
    input_dir_uri: str,
    script_filename: str,
    app_version: Optional[str] = None,
    job_name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    max_minutes: Optional[int] = None,
    node_count: Optional[int] = None,
    cores_per_node: Optional[int] = None,
    memory_mb: Optional[int] = None,
    queue: Optional[str] = None,
    allocation: Optional[str] = None,
    extra_file_inputs: Optional[List[Dict[str, Any]]] = None,
    extra_app_args: Optional[List[Dict[str, Any]]] = None,
    extra_env_vars: Optional[List[Dict[str, Any]]] = None,
    extra_scheduler_options: Optional[List[Dict[str, Any]]] = None,
    script_param_names: List[str] = ["Input Script", "Main Script", "tclScript"],
    input_dir_param_name: str = "Input Directory",
    allocation_param_name: str = "TACC Allocation",
) -> Dict[str, Any]:
    """Generates a Tapis job request dictionary based on app definition and user inputs/overrides."""
    print(f"Generating job request for app '{app_id}'...")
    try:
        app_details = get_app_details(tapis_client, app_id, app_version, verbose=False)
        if not app_details:
            raise AppDiscoveryError(
                f"App '{app_id}' (Version: {app_version or 'latest'}) not found."
            )
        final_app_version = app_details.version
        print(f"Using App Details: {app_details.id} v{final_app_version}")
        job_attrs = app_details.jobAttributes
        param_set_def = getattr(job_attrs, "parameterSet", None)
        final_job_name = (
            job_name or f"{app_details.id}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        final_description = (
            description or app_details.description or f"dapi job for {app_details.id}"
        )
        job_req = {
            "name": final_job_name,
            "appId": app_details.id,
            "appVersion": final_app_version,
            "description": final_description,
            "execSystemId": getattr(job_attrs, "execSystemId", None),
            "archiveSystemId": getattr(job_attrs, "archiveSystemId", None),
            "archiveOnAppError": getattr(job_attrs, "archiveOnAppError", True),
            "execSystemLogicalQueue": queue
            if queue is not None
            else getattr(job_attrs, "execSystemLogicalQueue", None),
            "nodeCount": node_count
            if node_count is not None
            else getattr(job_attrs, "nodeCount", None),
            "coresPerNode": cores_per_node
            if cores_per_node is not None
            else getattr(job_attrs, "coresPerNode", None),
            "maxMinutes": max_minutes
            if max_minutes is not None
            else getattr(job_attrs, "maxMinutes", None),
            "memoryMB": memory_mb
            if memory_mb is not None
            else getattr(job_attrs, "memoryMB", None),
            **(
                {"isMpi": getattr(job_attrs, "isMpi", None)}
                if getattr(job_attrs, "isMpi", None) is not None
                else {}
            ),
            **(
                {"cmdPrefix": getattr(job_attrs, "cmdPrefix", None)}
                if getattr(job_attrs, "cmdPrefix", None) is not None
                else {}
            ),
            **({"tags": tags or []}),
            "fileInputs": [],
            "parameterSet": {"appArgs": [], "envVariables": [], "schedulerOptions": []},
        }
        main_input_target_path = None
        main_input_automount = True
        if hasattr(job_attrs, "fileInputs") and job_attrs.fileInputs:
            for fi_def in job_attrs.fileInputs:
                if getattr(fi_def, "name", "").lower() == input_dir_param_name.lower():
                    main_input_target_path = getattr(fi_def, "targetPath", None)
                    main_input_automount = getattr(fi_def, "autoMountLocal", True)
                    break
        main_input_dict = {
            "name": input_dir_param_name,
            "sourceUrl": input_dir_uri,
            "autoMountLocal": main_input_automount,
        }
        if main_input_target_path:
            main_input_dict["targetPath"] = main_input_target_path
        job_req["fileInputs"].append(main_input_dict)
        if extra_file_inputs:
            job_req["fileInputs"].extend(extra_file_inputs)
        script_param_added = False
        if hasattr(param_set_def, "appArgs") and param_set_def.appArgs:
            for arg_def in param_set_def.appArgs:
                arg_name = getattr(arg_def, "name", "")
                if arg_name in script_param_names:
                    print(
                        f"Placing script '{script_filename}' in appArgs: '{arg_name}'"
                    )
                    job_req["parameterSet"]["appArgs"].append(
                        {"name": arg_name, "arg": script_filename}
                    )
                    script_param_added = True
                    break
        if (
            not script_param_added
            and hasattr(param_set_def, "envVariables")
            and param_set_def.envVariables
        ):
            for var_def in param_set_def.envVariables:
                var_key = getattr(var_def, "key", "")
                if var_key in script_param_names:
                    print(
                        f"Placing script '{script_filename}' in envVariables: '{var_key}'"
                    )
                    job_req["parameterSet"]["envVariables"].append(
                        {"key": var_key, "value": script_filename}
                    )
                    script_param_added = True
                    break
        if not script_param_added:
            raise ValueError(f"Could not find where to place the script parameter...")
        if extra_app_args:
            job_req["parameterSet"]["appArgs"].extend(extra_app_args)
        if extra_env_vars:
            job_req["parameterSet"]["envVariables"].extend(extra_env_vars)
        fixed_sched_opt_names = []
        if (
            hasattr(param_set_def, "schedulerOptions")
            and param_set_def.schedulerOptions
        ):
            for sched_opt_def in param_set_def.schedulerOptions:
                if getattr(sched_opt_def, "inputMode", None) == "FIXED":
                    fixed_sched_opt_names.append(getattr(sched_opt_def, "name", ""))
        if allocation:
            if allocation_param_name in fixed_sched_opt_names:
                print(
                    f"Warning: App definition marks '{allocation_param_name}' as FIXED..."
                )
            else:
                print(f"Adding allocation: {allocation}")
                job_req["parameterSet"]["schedulerOptions"].append(
                    {"name": allocation_param_name, "arg": f"-A {allocation}"}
                )
        if extra_scheduler_options:
            for extra_opt in extra_scheduler_options:
                opt_name = extra_opt.get("name")
                if opt_name and opt_name in fixed_sched_opt_names:
                    print(
                        f"Warning: Skipping user-provided scheduler option '{opt_name}'..."
                    )
                else:
                    job_req["parameterSet"]["schedulerOptions"].append(extra_opt)
        if not job_req["parameterSet"]["appArgs"]:
            del job_req["parameterSet"]["appArgs"]
        if not job_req["parameterSet"]["envVariables"]:
            del job_req["parameterSet"]["envVariables"]
        if not job_req["parameterSet"]["schedulerOptions"]:
            del job_req["parameterSet"]["schedulerOptions"]
        if not job_req["parameterSet"]:
            del job_req["parameterSet"]
        final_job_req = {k: v for k, v in job_req.items() if v is not None}
        print("Job request dictionary generated successfully.")
        return final_job_req
    except (AppDiscoveryError, ValueError) as e:
        print(f"ERROR: Failed to generate job request: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Unexpected error generating job request: {e}")
        raise JobSubmissionError(f"Unexpected error generating job request: {e}") from e


# --- submit_job_request function (Production Ready) ---
def submit_job_request(
    tapis_client: Tapis, job_request: Dict[str, Any]
) -> "SubmittedJob":
    """Submits a pre-generated job request dictionary to Tapis."""
    if not isinstance(job_request, dict):
        raise ValueError("Input 'job_request' must be a dictionary.")
    print("\n--- Submitting Tapis Job Request ---")
    print(json.dumps(job_request, indent=2, default=str))
    print("------------------------------------")
    try:
        submitted = tapis_client.jobs.submitJob(**job_request)
        print(f"Job submitted successfully. UUID: {submitted.uuid}")
        return SubmittedJob(tapis_client, submitted.uuid)
    except BaseTapyException as e:
        print(f"ERROR: Tapis job submission API call failed: {e}")
        raise JobSubmissionError(
            f"Tapis job submission failed: {e}",
            request=getattr(e, "request", None),
            response=getattr(e, "response", None),
        ) from e
    except Exception as e:
        print(f"ERROR: Unexpected error during job submission: {e}")
        raise JobSubmissionError(f"Unexpected error during job submission: {e}") from e


# --- SubmittedJob Class (Production Ready) ---
class SubmittedJob:
    """Represents a submitted Tapis job, providing methods for interaction."""

    TERMINAL_STATES = TAPIS_TERMINAL_STATES  # Use module-level constant

    def __init__(self, tapis_client: Tapis, job_uuid: str):
        if not isinstance(tapis_client, Tapis):
            raise TypeError("tapis_client must be an instance of tapipy.Tapis")
        if not job_uuid or not isinstance(job_uuid, str):
            raise ValueError("job_uuid must be a non-empty string.")
        self._tapis = tapis_client
        self.uuid = job_uuid
        self._last_status: Optional[str] = None
        self._job_details: Optional[Tapis] = None

    def _get_details(self, force_refresh: bool = False) -> Tapis:
        """Fetches and caches job details from Tapis."""
        if not self._job_details or force_refresh:
            try:
                self._job_details = self._tapis.jobs.getJob(jobUuid=self.uuid)
                self._last_status = self._job_details.status
            except BaseTapyException as e:
                raise JobMonitorError(
                    f"Failed to get details for job {self.uuid}: {e}"
                ) from e
        return self._job_details

    @property
    def details(self) -> Tapis:
        """Returns the cached job details (fetches if not cached)."""
        return self._get_details()

    @property
    def status(self) -> str:
        """Gets the current status of the job (potentially cached)."""
        try:
            if self._last_status and self._last_status not in self.TERMINAL_STATES:
                return self.get_status(force_refresh=False)
            elif self._last_status:
                return self._last_status
            else:
                return self.get_status(force_refresh=True)
        except JobMonitorError:
            return STATUS_UNKNOWN

    def get_status(self, force_refresh: bool = True) -> str:
        """Gets the current status of the job from Tapis."""
        if not force_refresh and self._last_status:
            return self._last_status
        try:
            status_obj = self._tapis.jobs.getJobStatus(jobUuid=self.uuid)
            new_status = status_obj.status
            if new_status != self._last_status:
                self._last_status = new_status
            if self._job_details and self._job_details.status != self._last_status:
                self._job_details = None
            return self._last_status
        except BaseTapyException as e:
            raise JobMonitorError(
                f"Failed to get status for job {self.uuid}: {e}"
            ) from e

    def monitor(self, interval: int = 15, timeout_minutes: Optional[int] = None) -> str:
        """
        Monitors the job status with tqdm progress bars until completion,
        failure, timeout, or interruption. Handles common exceptions internally.

        Args:
            interval: Check interval in seconds.
            timeout_minutes: Optional timeout. If None, uses job's maxMinutes.

        Returns:
            The final job status string (e.g., "FINISHED", "FAILED", "TIMEOUT", etc.).
        """
        previous_status = None
        current_status = STATUS_UNKNOWN
        start_time = time.time()
        effective_timeout_minutes = -1
        timeout_seconds = float("inf")
        max_iterations = float("inf")
        pbar_waiting = None
        pbar_monitoring = None

        print(f"\nMonitoring Job: {self.uuid}")  # Print Job ID once at the start

        try:
            # Fetch initial details
            details = self._get_details(force_refresh=True)
            current_status = details.status
            previous_status = current_status
            effective_timeout_minutes = (
                timeout_minutes if timeout_minutes is not None else details.maxMinutes
            )

            if effective_timeout_minutes <= 0:
                print(
                    f"Job has maxMinutes <= 0 ({details.maxMinutes}). Monitoring indefinitely or until terminal state."
                )
                timeout_seconds = float("inf")
                max_iterations = float("inf")
            else:
                timeout_seconds = effective_timeout_minutes * 60
                max_iterations = (
                    int(timeout_seconds // interval) if interval > 0 else float("inf")
                )

            waiting_states = [
                "PENDING",
                "PROCESSING_INPUTS",
                "STAGING_INPUTS",
                "STAGING_JOB",
                "SUBMITTING_JOB",
                "QUEUED",
            ]
            running_states = [
                "RUNNING",
                "ARCHIVING",
            ]  # Treat ARCHIVING as part of the active monitoring phase

            # --- Waiting Phase ---
            if current_status in waiting_states:
                pbar_waiting = tqdm(
                    desc="Waiting for job to start",
                    dynamic_ncols=True,
                    unit=" checks",
                    leave=False,
                )  # leave=False hides bar on completion
                while current_status in waiting_states:
                    pbar_waiting.set_postfix_str(
                        f"Status: {current_status}", refresh=True
                    )
                    time.sleep(interval)
                    current_status = self.get_status(force_refresh=True)
                    pbar_waiting.update(1)
                    if time.time() - start_time > timeout_seconds:
                        tqdm.write(
                            f"\nWarning: Monitoring timeout ({effective_timeout_minutes} mins) reached while waiting."
                        )
                        return STATUS_TIMEOUT
                    if current_status in self.TERMINAL_STATES:
                        pbar_waiting.set_postfix_str(
                            f"Status: {current_status}", refresh=True
                        )
                        tqdm.write(
                            f"\nJob reached terminal state while waiting: {current_status}"
                        )
                        return current_status  # Return actual terminal status
                pbar_waiting.close()
                pbar_waiting = None

            # --- Monitoring Phase ---
            if current_status in running_states:
                total_iterations = (
                    max_iterations if max_iterations != float("inf") else None
                )
                pbar_monitoring = tqdm(
                    total=total_iterations,
                    desc="Monitoring job",
                    ncols=100,
                    unit=" checks",
                    leave=True,
                )  # leave=True keeps bar after completion
                iteration_count = 0
                # Initial status print for this phase
                tqdm.write(f"\tStatus: {current_status}")
                previous_status = current_status

                while current_status in running_states:
                    # Update description only if status changes within this phase (less noisy)
                    if current_status != previous_status:
                        pbar_monitoring.set_description(
                            f"Monitoring job (Status: {current_status})"
                        )
                        tqdm.write(f"\tStatus: {current_status}")
                        previous_status = current_status

                    pbar_monitoring.update(1)
                    iteration_count += 1

                    if (
                        max_iterations != float("inf")
                        and iteration_count >= max_iterations
                    ):
                        tqdm.write(
                            f"\nWarning: Monitoring timeout ({effective_timeout_minutes} mins) reached."
                        )
                        return STATUS_TIMEOUT

                    time.sleep(interval)
                    current_status = self.get_status(force_refresh=True)

                    if current_status in self.TERMINAL_STATES:
                        tqdm.write(f"\tStatus: {current_status}")  # Write final status
                        if total_iterations:
                            pbar_monitoring.n = total_iterations
                            pbar_monitoring.refresh()
                        return current_status  # Return actual terminal status
                pbar_monitoring.close()
                pbar_monitoring = None

            # --- Handle Other Cases ---
            elif current_status in self.TERMINAL_STATES:
                print(f"Job already in terminal state: {current_status}")
                return current_status
            else:
                print(
                    f"Job in unexpected initial state '{current_status}'. Monitoring stopped."
                )
                return current_status

            return current_status  # Should be a terminal state if loops finished

        except KeyboardInterrupt:
            print(f"\nMonitoring interrupted by user.")
            return STATUS_INTERRUPTED
        except JobMonitorError as e:
            print(f"\nError during monitoring: {e}")
            return STATUS_MONITOR_ERROR
        except Exception as e:
            print(f"\nUnexpected error during monitoring: {e}")
            return STATUS_MONITOR_ERROR
        finally:
            # Safely close progress bars
            if pbar_waiting is not None:
                try:
                    pbar_waiting.close()
                except:
                    pass
            if pbar_monitoring is not None:
                try:
                    pbar_monitoring.close()
                except:
                    pass

    def print_runtime_summary(self, verbose: bool = False):
        """Get the runtime of a job.
        Args:
        t (object): The Tapis v3 client object.
        job_uuid (str): The UUID of the job for which the runtime needs to be determined.
        verbose (bool): If True, prints all history events. Otherwise, prints only specific statuses.
        Returns:
        None: This function doesn't return a value, but it prints the runtime details.
        """
        from datetime import datetime, timedelta

        t = self._tapis

        print("\nRuntime Summary")
        print("---------------")
        hist = t.jobs.getJobHistory(jobUuid=self.uuid)

        def format_timedelta(td):
            hours, remainder = divmod(td.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

        time1 = datetime.strptime(hist[-1].created, "%Y-%m-%dT%H:%M:%S.%fZ")
        time0 = datetime.strptime(hist[0].created, "%Y-%m-%dT%H:%M:%S.%fZ")
        total_time = time1 - time0

        if verbose:
            print("\nDetailed Job History:")
            for event in hist:
                print(
                    f"Event: {event.event}, Detail: {event.eventDetail}, Time: {event.created}"
                )
            print("\nSummary:")

        for i in range(len(hist) - 1):
            if hist[i].eventDetail == "RUNNING":
                time1 = datetime.strptime(hist[i + 1].created, "%Y-%m-%dT%H:%M:%S.%fZ")
                time0 = datetime.strptime(hist[i].created, "%Y-%m-%dT%H:%M:%S.%fZ")
                print("RUNNING time:", format_timedelta(time1 - time0))
            elif hist[i].eventDetail == "QUEUED":
                time1 = datetime.strptime(hist[i + 1].created, "%Y-%m-%dT%H:%M:%S.%fZ")
                time0 = datetime.strptime(hist[i].created, "%Y-%m-%dT%H:%M:%S.%fZ")
                print("QUEUED  time:", format_timedelta(time1 - time0))

        print("TOTAL   time:", format_timedelta(total_time))
        print("---------------")

    # --- Other SubmittedJob methods (archive_uri, list_outputs, etc.) ---
    # (No changes needed in these methods from the previous correct version)
    @property
    def archive_uri(self) -> Optional[str]:
        details = self._get_details()
        if details.archiveSystemId and details.archiveSystemDir:
            archive_path = details.archiveSystemDir.lstrip("/")
            return (
                f"tapis://{details.archiveSystemId}/{urllib.parse.quote(archive_path)}"
            )
        return None

    def list_outputs(
        self, path: str = "/", limit: int = 100, offset: int = 0
    ) -> List[Tapis]:
        details = self._get_details()
        if not details.archiveSystemId or not details.archiveSystemDir:
            raise FileOperationError(
                f"Job {self.uuid} archive system ID or directory not available."
            )
        full_archive_path = os.path.join(details.archiveSystemDir, path.lstrip("/"))
        full_archive_path = os.path.normpath(full_archive_path).lstrip("/")
        try:
            archive_base_uri = f"tapis://{details.archiveSystemId}/{urllib.parse.quote(full_archive_path)}"
            from .files import list_files

            return list_files(self._tapis, archive_base_uri, limit=limit, offset=offset)
        except BaseTapyException as e:
            raise FileOperationError(
                f"Failed list job outputs for {self.uuid} at path '{path}': {e}"
            ) from e
        except Exception as e:
            raise FileOperationError(
                f"Unexpected error listing job outputs for {self.uuid}: {e}"
            ) from e

    def download_output(self, remote_path: str, local_target: str):
        details = self._get_details()
        if not details.archiveSystemId or not details.archiveSystemDir:
            raise FileOperationError(
                f"Job {self.uuid} archive system ID or directory not available."
            )
        full_archive_path = os.path.join(
            details.archiveSystemDir, remote_path.lstrip("/")
        )
        full_archive_path = os.path.normpath(full_archive_path).lstrip("/")
        remote_uri = (
            f"tapis://{details.archiveSystemId}/{urllib.parse.quote(full_archive_path)}"
        )
        try:
            from .files import download_file

            download_file(self._tapis, remote_uri, local_target)
        except Exception as e:
            raise FileOperationError(
                f"Failed to download output '{remote_path}' for job {self.uuid}: {e}"
            ) from e

    def cancel(self):
        print(f"Attempting to cancel job {self.uuid}...")
        try:
            self._tapis.jobs.cancelJob(jobUuid=self.uuid)
            print(
                f"Cancel request sent for job {self.uuid}. Status may take time to update."
            )
            self._last_status = "CANCELLED"
            self._job_details = None
        except BaseTapyException as e:
            if hasattr(e, "response") and e.response and e.response.status_code == 400:
                print(
                    f"Could not cancel job {self.uuid}. It might already be in a terminal state. Fetching status..."
                )
                self.get_status(force_refresh=True)
                print(f"Current status: {self.status}")
            else:
                raise JobMonitorError(
                    f"Failed to send cancel request for job {self.uuid}: {e}"
                ) from e
        except Exception as e:
            raise JobMonitorError(
                f"Unexpected error cancelling job {self.uuid}: {e}"
            ) from e


# --- Standalone Helper Functions (Production Ready) ---
def get_job_status(t: Tapis, job_uuid: str) -> str:
    """Standalone function to get job status."""
    job = SubmittedJob(t, job_uuid)
    return job.get_status(force_refresh=True)


def get_runtime_summary(t: Tapis, job_uuid: str, verbose: bool = False):
    """Standalone function to print runtime summary."""
    job = SubmittedJob(t, job_uuid)
    job.print_runtime_summary(verbose=verbose)


def interpret_job_status(final_status: str, job_uuid: Optional[str] = None):
    """Prints a user-friendly interpretation of the final job status."""
    job_id_str = f"Job {job_uuid}" if job_uuid else "Job"
    if final_status == "FINISHED":
        print(f"{job_id_str} completed successfully.")
    elif final_status == "FAILED":
        print(f"{job_id_str} failed. Check logs or job details.")
    elif final_status == STATUS_TIMEOUT:
        print(f"{job_id_str} monitoring timed out.")
    elif final_status == STATUS_INTERRUPTED:
        print(f"{job_id_str} monitoring was interrupted.")
    elif final_status == STATUS_MONITOR_ERROR:
        print(f"An error occurred while monitoring {job_id_str}.")
    elif final_status == STATUS_UNKNOWN:
        print(f"Could not determine final status of {job_id_str}.")
    elif final_status in TAPIS_TERMINAL_STATES:
        print(f"{job_id_str} ended with status: {final_status}")
    else:
        print(f"{job_id_str} ended with an unexpected status: {final_status}")
