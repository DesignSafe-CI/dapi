from tapipy.tapis import Tapis
from . import auth
from . import apps as apps_module
from . import files as files_module
from . import jobs as jobs_module
from .jobs import JobDefinition, SubmittedJob # Make these easily accessible
from typing import List, Optional

# Renamed class from Client to DSClient
class DSClient:
    """
    Main client for interacting with DesignSafe resources via Tapis V3 using dapi.

    Provides abstracted methods for common operations (apps, files, jobs) and
    direct access to the underlying tapipy.Tapis client via the `.tapis` attribute.
    """
    def __init__(self, tapis_client: Optional[Tapis] = None, **auth_kwargs):
        """
        Initializes the Dapi DSClient.

        If an authenticated `tapis_client` (tapipy.Tapis object) is provided,
        it uses that instance directly.

        Otherwise, it calls dapi.auth.init() to create and authenticate
        a new Tapis client, passing any additional `auth_kwargs` (like
        base_url, username, password, env_file) to the init function.

        Args:
            tapis_client: An optional pre-authenticated tapipy.Tapis instance.
            **auth_kwargs: Keyword arguments passed to dapi.auth.init() if
                           tapis_client is not provided.
        """
        if tapis_client:
            if not isinstance(tapis_client, Tapis):
                raise TypeError("tapis_client must be an instance of tapipy.Tapis")
            # Verify the provided client is likely authenticated (has a token)
            if not tapis_client.get_access_jwt():
                 print("Warning: Provided tapis_client does not appear to be authenticated (no access token found).")
            self.tapis = tapis_client # Store the raw client here
        else:
            # Initialize and store the raw client
            self.tapis = auth.init(**auth_kwargs)

        # Provide access to abstracted modules/functionality
        self.apps = AppMethods(self.tapis)
        self.files = FileMethods(self.tapis)
        self.jobs = JobMethods(self.tapis)

    # Expose JobDefinition for convenience as a class attribute
    # This allows usage like: my_def = ds.JobDefinition(...)
    JobDefinition = JobDefinition

# --- Wrapper classes remain the same ---
class AppMethods:
    def __init__(self, tapis_client: Tapis):
        self._tapis = tapis_client # Keep internal reference

    def find(self, search_term: str, list_type: str = "ALL", verbose: bool = True) -> List[Tapis]:
        """Search for Tapis apps matching a search term."""
        return apps_module.find_apps(self._tapis, search_term, list_type, verbose)

    def get_details(self, app_id: str, app_version: Optional[str] = None, verbose: bool = True) -> Optional[Tapis]:
        """Get details for a specific app ID and optionally version."""
        return apps_module.get_app_details(self._tapis, app_id, app_version, verbose)

class FileMethods:
    def __init__(self, tapis_client: Tapis):
        self._tapis = tapis_client # Keep internal reference

    def translate_path_to_uri(self, path: str) -> str:
        """Given a path on DesignSafe, determine the correct Tapis system URI."""
        return files_module.get_ds_path_uri(self._tapis, path)

    def upload(self, local_path: str, remote_uri: str):
        """Uploads a local file to a Tapis system URI."""
        return files_module.upload_file(self._tapis, local_path, remote_uri)

    def download(self, remote_uri: str, local_path: str):
        """Downloads a file from a Tapis system URI to a local path."""
        return files_module.download_file(self._tapis, remote_uri, local_path)

    def list(self, remote_uri: str, limit: int = 100, offset: int = 0) -> List[Tapis]:
        """Lists files at a given Tapis system URI."""
        return files_module.list_files(self._tapis, remote_uri, limit, offset)

class JobMethods:
    def __init__(self, tapis_client: Tapis):
        self._tapis = tapis_client # Keep internal reference

    def submit(self, definition: JobDefinition, allocation: Optional[str] = None) -> SubmittedJob:
        """Submits a job based on a JobDefinition."""
        # Pass the raw client from the DSClient instance
        return jobs_module.submit_job(self._tapis, definition, allocation)

    def get(self, job_uuid: str) -> SubmittedJob:
        """Returns a SubmittedJob object for managing an existing job."""
        # Pass the raw client from the DSClient instance
        return SubmittedJob(self._tapis, job_uuid)

    # Optional: direct access to status/summary if needed without object
    def get_status(self, job_uuid: str) -> str:
         """Gets the current status of a job by UUID."""
         # Pass the raw client from the DSClient instance
         return jobs_module.get_job_status(self._tapis, job_uuid)

    def get_runtime_summary(self, job_uuid: str, verbose: bool = False):
         """Prints the runtime summary for a job by UUID."""
         # Pass the raw client from the DSClient instance
         jobs_module.get_runtime_summary(self._tapis, job_uuid, verbose=verbose)