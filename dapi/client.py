# dapi/client.py
from tapipy.tapis import Tapis
from . import auth
from . import apps as apps_module
from . import files as files_module
from . import jobs as jobs_module
from . import systems as systems_module 
from .db.accessor import DatabaseAccessor

# Import only the necessary classes/functions from jobs
from .jobs import SubmittedJob, interpret_job_status
from typing import List, Optional, Dict, Any


class DSClient:
    """
    Main client for interacting with DesignSafe resources via Tapis V3 using dapi.
    """

    def __init__(self, tapis_client: Optional[Tapis] = None, **auth_kwargs):
        if tapis_client:
            if not isinstance(tapis_client, Tapis):
                raise TypeError("tapis_client must be an instance of tapipy.Tapis")
            if not tapis_client.get_access_jwt():
                print(
                    "Warning: Provided tapis_client does not appear to be authenticated."
                )
            self.tapis = tapis_client
        else:
            self.tapis = auth.init(**auth_kwargs)

        # Instantiate Accessors
        self.apps = AppMethods(self.tapis)
        self.files = FileMethods(self.tapis)
        self.jobs = JobMethods(self.tapis)
        self.systems = SystemMethods(self.tapis)
        self.db = DatabaseAccessor()


# --- AppMethods and FileMethods remain the same ---
class AppMethods:
    def __init__(self, tapis_client: Tapis):
        self._tapis = tapis_client

    def find(self, *args, **kwargs) -> List[Tapis]:
        return apps_module.find_apps(self._tapis, *args, **kwargs)

    def get_details(self, *args, **kwargs) -> Optional[Tapis]:
        return apps_module.get_app_details(self._tapis, *args, **kwargs)


class FileMethods:
    def __init__(self, tapis_client: Tapis):
        self._tapis = tapis_client

    def translate_path_to_uri(self, *args, **kwargs) -> str:
        return files_module.get_ds_path_uri(self._tapis, *args, **kwargs)

    def upload(self, *args, **kwargs):
        return files_module.upload_file(self._tapis, *args, **kwargs)

    def download(self, *args, **kwargs):
        return files_module.download_file(self._tapis, *args, **kwargs)

    def list(self, *args, **kwargs) -> List[Tapis]:
        return files_module.list_files(self._tapis, *args, **kwargs)

class SystemMethods:
    def __init__(self, tapis_client: Tapis):
        self._tapis = tapis_client

    def list_queues(self, system_id: str, verbose: bool = True) -> List[Any]:
        """Lists logical queues for a given Tapis system."""
        return systems_module.list_system_queues(self._tapis, system_id, verbose=verbose)
    
class JobMethods:
    def __init__(self, tapis_client: Tapis):
        self._tapis = tapis_client

    # Method to generate the request dictionary
    def generate_request(
        self,
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
        # --- Optional Extra Parameters ---
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
        Generates a Tapis job request dictionary based on app definition and inputs.

        This is a convenience wrapper around jobs.generate_job_request.
        """
        return jobs_module.generate_job_request(
            tapis_client=self._tapis,
            app_id=app_id,
            input_dir_uri=input_dir_uri,
            script_filename=script_filename,
            app_version=app_version,
            job_name=job_name,
            description=description,
            tags=tags,
            max_minutes=max_minutes,
            node_count=node_count,
            cores_per_node=cores_per_node,
            memory_mb=memory_mb,
            queue=queue,
            allocation=allocation,
            extra_file_inputs=extra_file_inputs,
            extra_app_args=extra_app_args,
            extra_env_vars=extra_env_vars,
            extra_scheduler_options=extra_scheduler_options,
            script_param_names=script_param_names,
            input_dir_param_name=input_dir_param_name,
            allocation_param_name=allocation_param_name,
        )

    # Method to submit the generated request dictionary
    def submit_request(self, job_request: Dict[str, Any]) -> SubmittedJob:
        """
        Submits a pre-generated job request dictionary to Tapis.

        This is a convenience wrapper around jobs.submit_job_request.
        """
        return jobs_module.submit_job_request(self._tapis, job_request)

    # --- Management methods remain the same ---
    def get(self, job_uuid: str) -> SubmittedJob:
        """Returns a SubmittedJob object for managing an existing job."""
        return SubmittedJob(self._tapis, job_uuid)

    def get_status(self, job_uuid: str) -> str:
        """Gets the current status of a job by UUID."""
        return jobs_module.get_job_status(self._tapis, job_uuid)

    def get_runtime_summary(self, job_uuid: str, verbose: bool = False):
        """Prints the runtime summary for a job by UUID."""
        jobs_module.get_runtime_summary(self._tapis, job_uuid, verbose=verbose)

    def interpret_status(self, final_status: str, job_uuid: Optional[str] = None):
        """Prints a user-friendly interpretation of the final job status."""
        jobs_module.interpret_job_status(final_status, job_uuid)
