import time
import json
import os
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from dataclasses import dataclass, field, asdict
from .exceptions import JobSubmissionError, JobMonitorError, FileOperationError

# --- Job Definition ---

@dataclass
class FileInput:
    """Represents a Tapis job file input."""
    name: str # Logical name matching app definition (e.g., "Input Directory")
    sourceUrl: str # The tapis:// URI
    targetPath: Optional[str] = None # Optional target path within job dir
    description: Optional[str] = None # Optional description from app def
    notes: Optional[dict] = field(default_factory=dict) # Optional notes from app def
    autoMountLocal: bool = True # Common default for DesignSafe apps

    def to_dict(self):
        # Return dict suitable for Tapis API, excluding None values if needed
        d = asdict(self)
        # Tapis might not want None for targetPath if not specified
        if d.get('targetPath') is None:
            del d['targetPath']
        # Remove fields not directly part of Tapis fileInput schema if added
        d.pop('description', None)
        # d.pop('notes', None) # Notes might be part of schema in some contexts
        return d


@dataclass
class AppArgument:
    """Represents a Tapis job application argument."""
    name: str # Logical name matching app definition (e.g., "Input Script")
    arg: str  # The actual argument value
    description: Optional[str] = None # Optional description from app def
    notes: Optional[dict] = field(default_factory=dict) # Optional notes from app def

    def to_dict(self):
         # Return dict suitable for Tapis API
        d = asdict(self)
        # Remove fields not directly part of Tapis appArg schema if added
        d.pop('description', None)
        # d.pop('notes', None)
        return d

@dataclass
class EnvVariable:
    """Represents a Tapis job environment variable."""
    key: str
    value: str
    description: Optional[str] = None # Optional description from app def
    notes: Optional[dict] = field(default_factory=dict) # Optional notes from app def

    def to_dict(self):
        d = asdict(self)
        d.pop('description', None)
        # d.pop('notes', None)
        return d

@dataclass
class SchedulerOption:
     """Represents a Tapis job scheduler option."""
     name: str # Logical name (e.g., "TACC Allocation")
     arg: str # The scheduler argument (e.g., "-A MYALLOCATION")
     description: Optional[str] = None # Optional description from app def
     notes: Optional[dict] = field(default_factory=dict) # Optional notes from app def

     def to_dict(self):
        d = asdict(self)
        d.pop('description', None)
        # d.pop('notes', None)
        return d


@dataclass
class JobDefinition:
    """
    Defines the parameters for a Tapis job submission, independent of
    specific app logic. Use helper methods to add inputs/parameters.
    """
    app_id: str
    app_version: Optional[str] = None # If None, latest will be used by submit_job
    job_name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Inputs and Parameters (structured)
    file_inputs: List[FileInput] = field(default_factory=list)
    parameter_set_app_args: List[AppArgument] = field(default_factory=list)
    parameter_set_env_vars: List[EnvVariable] = field(default_factory=list)
    parameter_set_scheduler_options: List[SchedulerOption] = field(default_factory=list)
    # Add containerArgs, archiveFilter if needed

    # Resource requirements (optional, defaults taken from app by submit_job)
    node_count: Optional[int] = None
    cores_per_node: Optional[int] = None
    max_minutes: Optional[int] = None
    exec_system_logical_queue: Optional[str] = None

    # Other Tapis job fields (optional, defaults taken from app by submit_job)
    archive_on_app_error: Optional[bool] = None
    exec_system_id: Optional[str] = None # Allow overriding exec system
    archive_system_id: Optional[str] = None # Allow overriding archive system
    # ... add other relevant fields from Tapis job submission schema ...

    def add_file_input(self, name: str, source_url: str, target_path: Optional[str] = None, **kwargs):
        """Adds a file input to the definition."""
        # TODO: Validate source_url format?
        self.file_inputs.append(FileInput(name=name, sourceUrl=source_url, targetPath=target_path, **kwargs))

    def add_app_arg(self, name: str, arg: str, **kwargs):
        """Adds an application argument to the parameter set."""
        self.parameter_set_app_args.append(AppArgument(name=name, arg=arg, **kwargs))

    def add_env_variable(self, key: str, value: str, **kwargs):
        """Adds an environment variable to the parameter set."""
        self.parameter_set_env_vars.append(EnvVariable(key=key, value=value, **kwargs))

    def add_scheduler_option(self, name: str, arg: str, **kwargs):
        """Adds a scheduler option to the parameter set."""
        # Avoid duplicates by name if needed, or let Tapis handle it
        self.parameter_set_scheduler_options.append(SchedulerOption(name=name, arg=arg, **kwargs))

    def set_allocation(self, allocation: str, allocation_arg_name: str = "TACC Allocation"):
        """
        Convenience method to add/update a TACC allocation scheduler option.
        Removes any existing option with the same name before adding.
        """
        # Remove existing allocation first
        self.parameter_set_scheduler_options = [
            opt for opt in self.parameter_set_scheduler_options
            if opt.name != allocation_arg_name
        ]
        # Add the new one
        self.add_scheduler_option(name=allocation_arg_name, arg=f"-A {allocation}")

    def build_parameter_set_dict(self) -> Dict[str, Any]:
        """Constructs the parameterSet dictionary for the Tapis API request."""
        param_set = {}
        if self.parameter_set_app_args:
            param_set["appArgs"] = [arg.to_dict() for arg in self.parameter_set_app_args]
        if self.parameter_set_env_vars:
            param_set["envVariables"] = [var.to_dict() for var in self.parameter_set_env_vars]
        if self.parameter_set_scheduler_options:
            param_set["schedulerOptions"] = [opt.to_dict() for opt in self.parameter_set_scheduler_options]
        # Add containerArgs, archiveFilter here if implemented
        return param_set


# --- Job Submission ---

def submit_job(t: Tapis, definition: JobDefinition, allocation: Optional[str] = None) -> 'SubmittedJob':
    """
    Submits a job based on a JobDefinition.

    Args:
        t: Authenticated Tapis client.
        definition: A JobDefinition object describing the job.
        allocation: Optional TACC allocation string (convenience shortcut to call definition.set_allocation).

    Returns:
        A SubmittedJob object representing the running job.

    Raises:
        JobSubmissionError: If app lookup or submission fails.
        ValueError: If definition is invalid.
    """
    if not isinstance(definition, JobDefinition):
        raise ValueError("Input 'definition' must be a dapi.jobs.JobDefinition object.")

    # Apply convenience allocation if provided
    if allocation:
        definition.set_allocation(allocation) # Uses the definition's method

    try:
        # 1. Get App Details (use latest if version not specified)
        print(f"Fetching app details for {definition.app_id} (Version: {definition.app_version or 'latest'})...")
        if definition.app_version:
            app = t.apps.getApp(appId=definition.app_id, appVersion=definition.app_version)
        else:
            # Fetch latest and store the version used
            app = t.apps.getAppLatestVersion(appId=definition.app_id)
            if not app: # Handle case where latest version fetch fails
                 raise JobSubmissionError(f"Could not find latest version for app '{definition.app_id}'.")
            definition.app_version = app.version
        print(f"Using App: {app.id} v{app.version}")

        # Basic validation: Check if required file inputs/params are present? (Could be complex)
        # Tapis server will do the ultimate validation.

        # 2. Construct Job Request Dictionary
        job_req = {
            "name": definition.job_name or f"{app.id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "appId": app.id,
            "appVersion": app.version,
            "description": definition.description or f"dapi submitted job for {app.id} v{app.version}",
            "tags": definition.tags or [], # Ensure it's a list

            # --- Get defaults from App Definition ---
            "execSystemId": definition.exec_system_id or app.jobAttributes.execSystemId,
            "archiveSystemId": definition.archive_system_id or app.jobAttributes.archiveSystemId, # Added archive system override
            "archiveOnAppError": definition.archive_on_app_error if definition.archive_on_app_error is not None else app.jobAttributes.archiveOnAppError,

            # --- Use definition overrides or app defaults for resources ---
            "nodeCount": definition.node_count if definition.node_count is not None else app.jobAttributes.nodeCount,
            "coresPerNode": definition.cores_per_node if definition.cores_per_node is not None else app.jobAttributes.coresPerNode,
            "maxMinutes": definition.max_minutes if definition.max_minutes is not None else app.jobAttributes.maxMinutes,
            "execSystemLogicalQueue": definition.exec_system_logical_queue or app.jobAttributes.execSystemLogicalQueue,
            # Add memoryMB if needed: "memoryMB": definition.memory_mb or app.jobAttributes.memoryMB,

            # --- File Inputs ---
            "fileInputs": [fi.to_dict() for fi in definition.file_inputs],

            # --- Parameter Set ---
            "parameterSet": definition.build_parameter_set_dict(),

             # --- Other attributes ---
             # Copy relevant attributes from app.jobAttributes if not overridden and present
             "isMpi": getattr(app.jobAttributes, 'isMpi', False), # Example
             "cmdPrefix": getattr(app.jobAttributes, 'cmdPrefix', None), # Example
        }

        # Remove None values from top level if Tapis API requires it (usually not necessary)
        # job_req = {k: v for k, v in job_req.items() if v is not None}

        print("\n--- Submitting Tapis Job Request ---")
        print(json.dumps(job_req, indent=2))
        print("------------------------------------")

        # 3. Submit Job
        submitted = t.jobs.submitJob(**job_req)
        print(f"Job submitted successfully. UUID: {submitted.uuid}")

        # 4. Return SubmittedJob object
        return SubmittedJob(t, submitted.uuid)

    except BaseTapyException as e:
        print(f"ERROR: Tapis job submission failed: {e}")
        # Use the custom exception for better error reporting
        raise JobSubmissionError(f"Tapis job submission failed: {e}", request=getattr(e, 'request', None), response=getattr(e, 'response', None)) from e
    except Exception as e:
        print(f"ERROR: Failed to prepare or submit job: {e}")
        raise JobSubmissionError(f"Failed to prepare or submit job: {e}") from e


# --- Job Management ---

class SubmittedJob:
    """
    Represents a job that has been submitted to Tapis.
    Provides methods for monitoring and managing the job.
    """
    TERMINAL_STATES = ["FINISHED", "FAILED", "CANCELLED", "STOPPED", "ARCHIVING_FAILED"] # STOPPED added based on notebook

    def __init__(self, tapis_client: Tapis, job_uuid: str):
        if not isinstance(tapis_client, Tapis):
            raise TypeError("tapis_client must be an instance of tapipy.Tapis")
        if not job_uuid or not isinstance(job_uuid, str):
             raise ValueError("job_uuid must be a non-empty string.")

        self._tapis = tapis_client
        self.uuid = job_uuid
        self._last_status: Optional[str] = None
        self._job_details: Optional[Tapis] = None # Cache for job details

    def _get_details(self, force_refresh: bool = False) -> Tapis:
        """Fetches and caches job details from Tapis."""
        if not self._job_details or force_refresh:
            try:
                print(f"Fetching details for job {self.uuid}...")
                self._job_details = self._tapis.jobs.getJob(jobUuid=self.uuid)
                self._last_status = self._job_details.status # Update status from details
            except BaseTapyException as e:
                raise JobMonitorError(f"Failed to get details for job {self.uuid}: {e}") from e
        return self._job_details

    @property
    def details(self) -> Tapis:
        """Returns the cached job details (fetches if not cached)."""
        return self._get_details()

    @property
    def status(self) -> str:
        """Gets the current status of the job (potentially cached)."""
        # Use cached status if available and not terminal, otherwise fetch
        if self._last_status and self._last_status not in self.TERMINAL_STATES:
             # Could add a time check here to force refresh after a while
             return self.get_status(force_refresh=False) # Use the method to handle fetching
        elif self._last_status:
             return self._last_status # Return cached terminal status
        else:
             return self.get_status(force_refresh=True) # Fetch if no status known

    def get_status(self, force_refresh: bool = True) -> str:
        """
        Gets the current status of the job from Tapis.

        Args:
            force_refresh: If False, might return cached status. If True, always queries Tapis.

        Returns:
            The current job status string.
        """
        if not force_refresh and self._last_status:
            # Return cached status immediately if not forcing refresh
            # Especially useful for terminal states
            return self._last_status

        try:
            # print(f"Fetching status for job {self.uuid}...") # Can be noisy
            status_obj = self._tapis.jobs.getJobStatus(jobUuid=self.uuid)
            if status_obj.status != self._last_status:
                 print(f"Job {self.uuid} Status Change: {self._last_status} -> {status_obj.status}")
                 self._last_status = status_obj.status
                 # If status changed, details might be outdated
                 if self._job_details and self._job_details.status != self._last_status:
                      self._job_details = None # Clear details cache
            return self._last_status
        except BaseTapyException as e:
            raise JobMonitorError(f"Failed to get status for job {self.uuid}: {e}") from e

    def monitor(self, interval: int = 30, timeout_minutes: Optional[int] = None, verbose: bool = True) -> str:
        """
        Monitors the job until completion, failure, or timeout.

        Args:
            interval: Check interval in seconds.
            timeout_minutes: Optional timeout. If None, uses job's maxMinutes from details.
            verbose: Print status updates.

        Returns:
            The final job status string.

        Raises:
            JobMonitorError: If monitoring fails or times out.
        """
        start_time = time.time()
        try:
            # Get initial details to determine timeout if not provided
            details = self._get_details(force_refresh=True)
            effective_timeout_minutes = timeout_minutes if timeout_minutes is not None else details.maxMinutes
            if effective_timeout_minutes <= 0:
                 print(f"Warning: Job {self.uuid} has maxMinutes <= 0 ({details.maxMinutes}). Monitoring indefinitely or until terminal state.")
                 timeout_seconds = float('inf')
            else:
                 timeout_seconds = effective_timeout_minutes * 60

            if verbose:
                print(f"Monitoring job {self.uuid} (Status: {self.status}, Timeout: {effective_timeout_minutes} mins, Interval: {interval}s)")

            while True:
                current_status = self.get_status(force_refresh=True) # Always refresh during monitor loop

                # Verbose printing handled within get_status on change

                if current_status in self.TERMINAL_STATES:
                    if verbose: print(f"Job {self.uuid} reached terminal state: {current_status}")
                    return current_status

                elapsed_time = time.time() - start_time
                if elapsed_time > timeout_seconds:
                    print(f"Warning: Monitoring timeout ({effective_timeout_minutes} mins) reached for job {self.uuid}.")
                    raise JobMonitorError(f"Monitoring timeout after {effective_timeout_minutes} minutes for job {self.uuid}. Last status: {current_status}")

                # Wait for the next interval
                time.sleep(interval)

        except KeyboardInterrupt:
             print(f"\nMonitoring interrupted by user for job {self.uuid}.")
             raise JobMonitorError(f"Monitoring interrupted for job {self.uuid}. Last status: {self._last_status or 'Unknown'}")
        except Exception as e:
             # Catch potential errors during monitoring loop
             print(f"\nError during monitoring for job {self.uuid}: {e}")
             raise JobMonitorError(f"Error monitoring job {self.uuid}: {e}") from e


    def get_history(self) -> List[Tapis]:
        """Gets the job history events from Tapis."""
        try:
            print(f"Fetching history for job {self.uuid}...")
            return self._tapis.jobs.getJobHistory(jobUuid=self.uuid)
        except BaseTapyException as e:
             raise JobMonitorError(f"Failed to get history for job {self.uuid}: {e}") from e

    def print_runtime_summary(self, verbose: bool = False):
         """Prints a summary of the job's runtime based on history."""
         print("\nRuntime Summary")
         print("---------------")
         try:
             hist = self.get_history()
             if not hist:
                 print("No history found.")
                 print("---------------")
                 return

             def format_timedelta(td):
                 if not isinstance(td, timedelta): return "N/A"
                 td_seconds = int(td.total_seconds())
                 hours, remainder = divmod(td_seconds, 3600)
                 minutes, seconds = divmod(remainder, 60)
                 return f"{hours:02d}:{int(minutes):02d}:{int(seconds):02d}"

             # Tapis v3 uses ISO format with Zulu timezone indicator
             time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
             alt_time_format = "%Y-%m-%dT%H:%M:%SZ" # Sometimes microseconds are omitted

             def parse_time(time_str):
                 try:
                     return datetime.strptime(time_str, time_format).replace(tzinfo=timezone.utc)
                 except ValueError:
                     try:
                         # Try format without microseconds
                         return datetime.strptime(time_str, alt_time_format).replace(tzinfo=timezone.utc)
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
                  total_time = timedelta(0) # Or None?
             else:
                  total_time = last_event_time - first_event_time

             if verbose:
                 print("\nDetailed Job History:")
                 for event in hist:
                     # Access attributes directly if they exist
                     event_desc = getattr(event, 'event', 'N/A')
                     detail = getattr(event, 'eventDetail', getattr(event, 'status', 'N/A')) # Use status as fallback
                     created_time = getattr(event, 'created', 'N/A')
                     print(f"  Event: {event_desc}, Detail: {detail}, Time: {created_time}")
                 print("\nSummary:")

             # Calculate stage times (adjust details based on actual Tapis v3 events)
             stage_times = {}
             valid_events = sorted([e for e in hist if parse_time(e.created)], key=lambda x: parse_time(x.created))

             for i in range(len(valid_events) - 1):
                 # Use status field which is more consistent in history
                 status = getattr(valid_events[i], 'status', None)
                 if not status: continue # Skip if no status

                 t0 = parse_time(valid_events[i].created)
                 t1 = parse_time(valid_events[i+1].created)

                 if t0 and t1:
                     duration = t1 - t0
                     stage_times[status] = stage_times.get(status, timedelta(0)) + duration

             # Print calculated stage times
             for stage, duration in sorted(stage_times.items()): # Sort for consistent order
                  print(f"{stage:<15} time: {format_timedelta(duration)}")

             # Print total time
             print(f"{'TOTAL':<15} time: {format_timedelta(total_time)}")
             print("---------------")

         except Exception as e:
             print(f"Error calculating runtime summary: {e}")
             print("---------------")

    @property
    def archive_uri(self) -> Optional[str]:
         """Returns the Tapis URI for the job's archive directory."""
         details = self._get_details()
         if details.archiveSystemId and details.archiveSystemDir:
              # Ensure path doesn't have leading slash for URI construction if needed
              archive_path = details.archiveSystemDir.lstrip('/')
              return f"tapis://{details.archiveSystemId}/{urllib.parse.quote(archive_path)}"
         return None


    def list_outputs(self, path: str = '/', limit: int = 100, offset: int = 0) -> List[Tapis]:
        """
        Lists files in the job's output archive directory.

        Args:
            path: Path relative to the job's archive directory root.
            limit: Max items.
            offset: Pagination offset.

        Returns:
            List of Tapis FileInfo objects.

        Raises:
            FileOperationError: If listing fails or archive info is missing.
        """
        details = self._get_details()
        if not details.archiveSystemId or not details.archiveSystemDir:
            raise FileOperationError(f"Job {self.uuid} archive system ID or directory not available.")

        # Construct the full path within the archive system
        # archiveSystemDir usually contains the full path already
        full_archive_path = os.path.join(details.archiveSystemDir, path.lstrip('/'))
        # Normalize path separators just in case
        full_archive_path = os.path.normpath(full_archive_path).lstrip('/')

        print(f"Listing outputs in archive system '{details.archiveSystemId}' at path '{full_archive_path}'")
        try:
            # Use the main files.list_files function for consistency
            # Need to construct the full URI first
            archive_base_uri = f"tapis://{details.archiveSystemId}/{urllib.parse.quote(full_archive_path)}"
            return list_files(self._tapis, archive_base_uri, limit=limit, offset=offset)

        except BaseTapyException as e:
             raise FileOperationError(f"Failed list job outputs for {self.uuid} at path '{path}': {e}") from e
        except Exception as e:
             raise FileOperationError(f"Unexpected error listing job outputs for {self.uuid}: {e}") from e


    def download_output(self, remote_path: str, local_target: str):
        """
        Downloads a specific file or directory from the job's output archive.

        Args:
            remote_path: The path of the file/dir relative to the archive root.
            local_target: The local path to save the downloaded file/dir.

        Raises:
            FileOperationError: If download fails or archive info is missing.
        """
        details = self._get_details()
        if not details.archiveSystemId or not details.archiveSystemDir:
            raise FileOperationError(f"Job {self.uuid} archive system ID or directory not available.")

        # Construct the full remote Tapis URI for the specific file/path
        full_archive_path = os.path.join(details.archiveSystemDir, remote_path.lstrip('/'))
        full_archive_path = os.path.normpath(full_archive_path).lstrip('/')
        remote_uri = f"tapis://{details.archiveSystemId}/{urllib.parse.quote(full_archive_path)}"

        print(f"Attempting to download output '{remote_path}' from job {self.uuid} archive...")
        try:
            # Use the main files.download_file function
            download_file(self._tapis, remote_uri, local_target)
        except Exception as e: # Catch errors from download_file
             raise FileOperationError(f"Failed to download output '{remote_path}' for job {self.uuid}: {e}") from e


    def cancel(self):
        """Cancels the running job."""
        print(f"Attempting to cancel job {self.uuid}...")
        try:
            self._tapis.jobs.cancelJob(jobUuid=self.uuid)
            print(f"Cancel request sent for job {self.uuid}. Status may take time to update.")
            self._last_status = "CANCELLED" # Assume cancellation for immediate feedback
            self._job_details = None # Clear cache
        except BaseTapyException as e:
             # Check if already in terminal state
             if hasattr(e, 'response') and e.response and e.response.status_code == 400:
                  # Tapis often gives 400 if job is already finished/failed/cancelled
                  print(f"Could not cancel job {self.uuid}. It might already be in a terminal state. Fetching status...")
                  self.get_status(force_refresh=True) # Update status
                  print(f"Current status: {self.status}")
             else:
                  raise JobMonitorError(f"Failed to send cancel request for job {self.uuid}: {e}") from e
        except Exception as e:
             raise JobMonitorError(f"Unexpected error cancelling job {self.uuid}: {e}") from e


# --- Standalone Helper Functions (Optional but used in notebook) ---

def get_job_status(t: Tapis, job_uuid: str) -> str:
    """Standalone function to get job status."""
    job = SubmittedJob(t, job_uuid)
    return job.get_status(force_refresh=True) # Force refresh for standalone call

def get_runtime_summary(t: Tapis, job_uuid: str, verbose: bool = False):
    """Standalone function to print runtime summary."""
    job = SubmittedJob(t, job_uuid)
    job.print_runtime_summary(verbose=verbose)