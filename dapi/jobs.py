# dapi/jobs.py
import time
import json
import os
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from .apps import get_app_details
from .exceptions import (
    JobSubmissionError,
    JobMonitorError,
    FileOperationError,
    AppDiscoveryError,
)


# --- Function to Generate Job Request Dictionary ---
def generate_job_request(
    tapis_client: Tapis,
    app_id: str,
    input_dir_uri: str,
    script_filename: str,
    # --- Optional Overrides ---
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
    # --- Optional Extra Parameters (User must know the correct structure) ---
    extra_file_inputs: Optional[List[Dict[str, Any]]] = None,
    extra_app_args: Optional[List[Dict[str, Any]]] = None,
    extra_env_vars: Optional[List[Dict[str, Any]]] = None,
    extra_scheduler_options: Optional[List[Dict[str, Any]]] = None,
    # --- Configuration ---
    script_param_names: List[str] = ["Input Script", "Main Script", "tclScript"],
    input_dir_param_name: str = "Input Directory",
    allocation_param_name: str = "TACC Allocation",
) -> Dict[str, Any]:
    """
    Generates a Tapis job request dictionary based on app definition and user inputs/overrides.

    Args:
        tapis_client: Authenticated Tapis client.
        app_id: The ID of the Tapis application.
        input_dir_uri: The tapis:// URI for the main input directory.
        script_filename: The name of the primary script file within the input directory.
        app_version: Specific app version to use (default: latest).
        job_name: Override job name (default: generated).
        description: Override job description.
        tags: Job tags.
        max_minutes: Override max runtime.
        node_count: Override node count.
        cores_per_node: Override cores per node.
        memory_mb: Override memory in MB.
        queue: Override execution queue.
        allocation: TACC allocation string (adds scheduler option).
        extra_file_inputs: List of additional file input dictionaries.
        extra_app_args: List of additional appArgs dictionaries.
        extra_env_vars: List of additional envVariables dictionaries.
        extra_scheduler_options: List of additional schedulerOptions dictionaries.
        script_param_names: List of possible names/keys for the script parameter.
        input_dir_param_name: The expected 'name' of the fileInput for the main directory.
        allocation_param_name: The name used for the TACC allocation scheduler option.

    Returns:
        A dictionary representing the Tapis job submission request body.

    Raises:
        AppDiscoveryError: If the app cannot be found.
        ValueError: If the script parameter cannot be placed in the app definition.
        JobSubmissionError: If preparation fails (should be rare here).
    """
    print(f"Generating job request for app '{app_id}'...")
    try:
        # 1. Fetch App Details
        app_details = get_app_details(tapis_client, app_id, app_version, verbose=False)
        if not app_details:
            raise AppDiscoveryError(
                f"App '{app_id}' (Version: {app_version or 'latest'}) not found."
            )
        final_app_version = app_details.version
        print(f"Using App Details: {app_details.id} v{final_app_version}")
        job_attrs = app_details.jobAttributes
        param_set_def = getattr(job_attrs, "parameterSet", None)

        # 2. Determine Final Job Name and Description
        final_job_name = (
            job_name or f"{app_details.id}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        final_description = (
            description or app_details.description or f"dapi job for {app_details.id}"
        )

        # 3. Initialize Job Request with Defaults & Overrides
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

        # Add main file input, finding targetPath from app def
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

        # Add any extra user-provided file inputs
        if extra_file_inputs:
            job_req["fileInputs"].extend(extra_file_inputs)

        # 4. Place Script Parameter Intelligently
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
            raise ValueError(
                f"Could not find where to place the script parameter in app '{app_details.id}' using names: {script_param_names}"
            )

        # Add any extra user-provided appArgs and envVars
        if extra_app_args:
            job_req["parameterSet"]["appArgs"].extend(extra_app_args)
        if extra_env_vars:
            job_req["parameterSet"]["envVariables"].extend(extra_env_vars)

        # 5. Handle Scheduler Options (Allocation and Extras, respecting FIXED)
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
                    f"Warning: App definition marks '{allocation_param_name}' as FIXED. Cannot override with job submission."
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
                        f"Warning: Skipping user-provided scheduler option '{opt_name}' because it is defined as FIXED in the app."
                    )
                else:
                    job_req["parameterSet"]["schedulerOptions"].append(extra_opt)

        # 6. Clean up empty parameterSet lists and parameterSet itself
        if not job_req["parameterSet"]["appArgs"]:
            del job_req["parameterSet"]["appArgs"]
        if not job_req["parameterSet"]["envVariables"]:
            del job_req["parameterSet"]["envVariables"]
        if not job_req["parameterSet"]["schedulerOptions"]:
            del job_req["parameterSet"]["schedulerOptions"]
        if not job_req["parameterSet"]:
            del job_req["parameterSet"]

        # 7. Remove top-level None values
        final_job_req = {k: v for k, v in job_req.items() if v is not None}

        print("Job request dictionary generated successfully.")
        return final_job_req

    except (AppDiscoveryError, ValueError) as e:
        print(f"ERROR: Failed to generate job request: {e}")
        raise  # Re-raise specific errors
    except Exception as e:
        print(f"ERROR: Unexpected error generating job request: {e}")
        # Wrap unexpected errors for clarity
        raise JobSubmissionError(f"Unexpected error generating job request: {e}") from e


# --- Job Submission Function (Simplified: Takes Dictionary) ---


def submit_job_request(
    tapis_client: Tapis, job_request: Dict[str, Any]
) -> "SubmittedJob":
    """
    Submits a pre-generated job request dictionary to Tapis.

    Args:
        tapis_client: Authenticated Tapis client.
        job_request: The job request dictionary (e.g., generated by generate_job_request).

    Returns:
        A SubmittedJob object representing the running job.

    Raises:
        JobSubmissionError: If the submission API call fails.
        ValueError: If job_request is not a dictionary.
    """
    if not isinstance(job_request, dict):
        raise ValueError("Input 'job_request' must be a dictionary.")

    print("\n--- Submitting Tapis Job Request ---")
    # Use default=str just in case something non-serializable slipped through
    print(json.dumps(job_request, indent=2, default=str))
    print("------------------------------------")
    try:
        # Directly pass the dictionary using **kwargs expansion
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


class SubmittedJob:
    TERMINAL_STATES = ["FINISHED", "FAILED", "CANCELLED", "STOPPED", "ARCHIVING_FAILED"]

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
        return self._get_details()

    @property
    def status(self) -> str:
        if self._last_status and self._last_status not in self.TERMINAL_STATES:
            return self.get_status(force_refresh=False)
        elif self._last_status:
            return self._last_status
        else:
            return self.get_status(force_refresh=True)

    def get_status(self, force_refresh: bool = True) -> str:
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

    def monitor(
        self,
        interval: int = 30,
        timeout_minutes: Optional[int] = None,
        verbose: bool = True,
    ) -> str:
        start_time = time.time()
        try:
            details = self._get_details(force_refresh=True)
            effective_timeout_minutes = (
                timeout_minutes if timeout_minutes is not None else details.maxMinutes
            )
            if effective_timeout_minutes <= 0:
                timeout_seconds = float("inf")
            else:
                timeout_seconds = effective_timeout_minutes * 60
            last_printed_status = None
            if verbose:
                print(
                    f"Monitoring job {self.uuid} (Initial Status: {self.status}, Timeout: {effective_timeout_minutes} mins, Interval: {interval}s)"
                )
                last_printed_status = self.status
            while True:
                current_status = self.get_status(force_refresh=True)
                if verbose and current_status != last_printed_status:
                    print(
                        f"\tJob {self.uuid} Status: {current_status} ({datetime.now().isoformat()})"
                    )
                    last_printed_status = current_status
                if current_status in self.TERMINAL_STATES:
                    if verbose:
                        print(
                            f"Job {self.uuid} reached terminal state: {current_status}"
                        )
                    return current_status
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout_seconds:
                    raise JobMonitorError(
                        f"Monitoring timeout after {effective_timeout_minutes} minutes for job {self.uuid}. Last status: {current_status}"
                    )
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\nMonitoring interrupted by user for job {self.uuid}.")
            raise JobMonitorError(
                f"Monitoring interrupted for job {self.uuid}. Last status: {self._last_status or 'Unknown'}"
            )
        except Exception as e:
            print(f"\nError during monitoring for job {self.uuid}: {e}")
            raise JobMonitorError(f"Error monitoring job {self.uuid}: {e}") from e

    def get_history(self) -> List[Tapis]:
        try:
            return self._tapis.jobs.getJobHistory(jobUuid=self.uuid)
        except BaseTapyException as e:
            raise JobMonitorError(
                f"Failed to get history for job {self.uuid}: {e}"
            ) from e

    def print_runtime_summary(self, verbose: bool = False):
        print("\nRuntime Summary")
        print("---------------")
        try:
            hist = self.get_history()
            if not hist:
                print("No history found.")
                print("---------------")
                return

            def format_timedelta(td):
                if not isinstance(td, timedelta):
                    return "N/A"
                td_seconds = int(td.total_seconds())
                hours, remainder = divmod(td_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                return f"{hours:02d}:{int(minutes):02d}:{int(seconds):02d}"

            time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
            alt_time_format = "%Y-%m-%dT%H:%M:%SZ"

            def parse_time(time_str):
                try:
                    return datetime.strptime(time_str, time_format).replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    try:
                        return datetime.strptime(time_str, alt_time_format).replace(
                            tzinfo=timezone.utc
                        )
                    except ValueError:
                        print(f"Warning: Could not parse timestamp '{time_str}'")
                        return None

            if len(hist) < 1:
                print("Insufficient history data.")
                print("---------------")
                return
            first_event_time = parse_time(hist[0].created)
            last_event_time = parse_time(hist[-1].created)
            if not first_event_time or not last_event_time:
                print("Could not parse start or end times from history.")
                total_time = timedelta(0)
            else:
                total_time = last_event_time - first_event_time
            if verbose:
                print("\nDetailed Job History:")
                for event in hist:
                    print(
                        f"  Event: {getattr(event, 'event', 'N/A')}, Detail: {getattr(event, 'eventDetail', getattr(event, 'status', 'N/A'))}, Time: {getattr(event, 'created', 'N/A')}"
                    )
                print("\nSummary:")
            stage_times = {}
            valid_events = sorted(
                [e for e in hist if parse_time(e.created)],
                key=lambda x: parse_time(x.created),
            )
            for i in range(len(valid_events) - 1):
                status = getattr(valid_events[i], "status", None)
                if not status:
                    continue
                t0 = parse_time(valid_events[i].created)
                t1 = parse_time(valid_events[i + 1].created)
                if t0 and t1:
                    duration = t1 - t0
                    stage_times[status] = (
                        stage_times.get(status, timedelta(0)) + duration
                    )
            for stage, duration in sorted(stage_times.items()):
                print(f"{stage:<15} time: {format_timedelta(duration)}")
            print(f"{'TOTAL':<15} time: {format_timedelta(total_time)}")
            print("---------------")
        except Exception as e:
            print(f"Error calculating runtime summary: {e}")
            print("---------------")

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


# --- Standalone Helper Functions ---
def get_job_status(t: Tapis, job_uuid: str) -> str:
    """Standalone function to get job status."""
    job = SubmittedJob(t, job_uuid)
    return job.get_status(force_refresh=True)


def get_runtime_summary(t: Tapis, job_uuid: str, verbose: bool = False):
    """Standalone function to print runtime summary."""
    job = SubmittedJob(t, job_uuid)
    job.print_runtime_summary(verbose=verbose)
