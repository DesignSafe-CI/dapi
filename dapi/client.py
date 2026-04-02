# dapi/client.py
from tapipy.tapis import Tapis
from . import auth
from . import apps as apps_module
from . import files as files_module
from . import jobs as jobs_module
from . import systems as systems_module
from . import launcher as launcher_module
from . import projects as projects_module
from .db.accessor import DatabaseAccessor

# Import only the necessary classes/functions from jobs
from .jobs import SubmittedJob
from typing import List, Optional, Dict, Any


class DSClient:
    """Main client for interacting with DesignSafe resources via Tapis V3 using dapi.

    The DSClient provides a high-level interface for working with DesignSafe resources
    through the Tapis V3 API. It handles authentication and provides organized access
    to different service areas including applications, files, jobs, systems, and databases.

    Args:
        tapis_client (Tapis, optional): Pre-authenticated Tapis client instance.
            If provided, it will be used instead of creating a new one.
        **auth_kwargs: Additional authentication arguments passed to auth.init()
            when tapis_client is not provided. See auth.init() for available options.

    Attributes:
        tapis (Tapis): The underlying authenticated Tapis client instance.
        apps (AppMethods): Interface for application discovery and details.
        files (FileMethods): Interface for file operations (upload, download, list).
        jobs (JobMethods): Interface for job submission and monitoring.
        projects (ProjectMethods): Interface for DesignSafe project management.
        systems (SystemMethods): Interface for system information and queues.
        db (DatabaseAccessor): Interface for database connections and queries.

    Raises:
        TypeError: If tapis_client is provided but is not a Tapis instance.
        AuthenticationError: If authentication fails when creating a new Tapis client.

    Example:
        Basic usage with automatic authentication:

        >>> ds = DSClient()
        Enter DesignSafe Username: myuser
        Enter DesignSafe Password: [hidden]
        Authentication successful.

        Using explicit credentials:

        >>> ds = DSClient(username="myuser", password="mypass")
        Authentication successful.

        Using a pre-authenticated Tapis client:

        >>> tapis = Tapis(base_url="https://designsafe.tapis.io", ...)
        >>> tapis.get_tokens()
        >>> ds = DSClient(tapis_client=tapis)
    """

    def __init__(self, tapis_client: Optional[Tapis] = None, **auth_kwargs):
        """Initialize the DSClient with authentication and service interfaces.

        Args:
            tapis_client (Tapis, optional): Pre-authenticated Tapis client instance.
                If provided, it will be used instead of creating a new one.
            **auth_kwargs: Additional authentication arguments passed to auth.init()
                when tapis_client is not provided. Common arguments include:
                - username (str): DesignSafe username
                - password (str): DesignSafe password
                - base_url (str): Tapis base URL
                - env_file (str): Path to .env file with credentials

        Raises:
            TypeError: If tapis_client is provided but is not a Tapis instance.
            AuthenticationError: If authentication fails when creating new client.
        """
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
        self.projects = ProjectMethods(self.tapis)
        self.systems = SystemMethods(self.tapis)
        self.db = DatabaseAccessor()

        # Auto-setup TMS credentials on TACC execution systems
        systems_module.setup_tms_credentials(self.tapis)


# --- AppMethods and FileMethods remain the same ---
class AppMethods:
    """Interface for Tapis application discovery and details retrieval.

    This class provides methods for finding and getting detailed information
    about Tapis applications available for job submission.

    Args:
        tapis_client (Tapis): Authenticated Tapis client instance.
    """

    def __init__(self, tapis_client: Tapis):
        """Initialize AppMethods with a Tapis client.

        Args:
            tapis_client (Tapis): Authenticated Tapis client instance.
        """
        self._tapis = tapis_client

    def find(self, *args, **kwargs) -> List[Tapis]:
        """Search for Tapis apps matching a search term.

        This is a convenience wrapper around apps_module.find_apps().

        Args:
            *args: Positional arguments passed to find_apps().
            **kwargs: Keyword arguments passed to find_apps().

        Returns:
            List[Tapis]: List of matching Tapis app objects.

        Raises:
            AppDiscoveryError: If the search fails or encounters an error.
        """
        return apps_module.find_apps(self._tapis, *args, **kwargs)

    def get_details(self, *args, **kwargs) -> Optional[Tapis]:
        """Get detailed information for a specific app ID and version.

        This is a convenience wrapper around apps_module.get_app_details().

        Args:
            *args: Positional arguments passed to get_app_details().
            **kwargs: Keyword arguments passed to get_app_details().

        Returns:
            Optional[Tapis]: Tapis app object with full details, or None if not found.

        Raises:
            AppDiscoveryError: If the retrieval fails or encounters an error.
        """
        return apps_module.get_app_details(self._tapis, *args, **kwargs)


class FileMethods:
    """Interface for file operations on Tapis storage systems.

    This class provides methods for uploading, downloading, listing files,
    and translating DesignSafe-style paths to Tapis URIs.

    Args:
        tapis_client (Tapis): Authenticated Tapis client instance.
    """

    def __init__(self, tapis_client: Tapis):
        """Initialize FileMethods with a Tapis client.

        Args:
            tapis_client (Tapis): Authenticated Tapis client instance.
        """
        self._tapis = tapis_client

    def to_uri(self, *args, **kwargs) -> str:
        """Translate DesignSafe-style paths to Tapis URIs.

        Args:
            *args: Positional arguments passed to get_ds_path_uri().
            **kwargs: Keyword arguments passed to get_ds_path_uri().

        Returns:
            str: The corresponding Tapis URI (e.g., tapis://system-id/path).

        Raises:
            FileOperationError: If path translation fails.
            ValueError: If the input path format is unrecognized.
        """
        return files_module.get_ds_path_uri(self._tapis, *args, **kwargs)

    def to_path(self, *args, **kwargs) -> str:
        """Translate Tapis URIs to DesignSafe local paths.

        Args:
            *args: Positional arguments passed to tapis_uri_to_local_path().
            **kwargs: Keyword arguments passed to tapis_uri_to_local_path().

        Returns:
            str: The corresponding DesignSafe local path (e.g., /home/jupyter/MyData/path).

        Example:
            >>> local_path = ds.files.to_path(
            ...     "tapis://designsafe.storage.default/user/data"
            ... )
            >>> print(local_path)  # "/home/jupyter/MyData/data"
        """
        return files_module.tapis_uri_to_local_path(*args, **kwargs)

    def upload(self, *args, **kwargs):
        """Upload a local file to a Tapis storage system.

        This is a convenience wrapper around files_module.upload_file().

        Args:
            *args: Positional arguments passed to upload_file().
            **kwargs: Keyword arguments passed to upload_file().

        Raises:
            FileOperationError: If the upload operation fails.
            FileNotFoundError: If the local file does not exist.
        """
        return files_module.upload_file(self._tapis, *args, **kwargs)

    def download(self, *args, **kwargs):
        """Download a file from a Tapis storage system to local filesystem.

        This is a convenience wrapper around files_module.download_file().

        Args:
            *args: Positional arguments passed to download_file().
            **kwargs: Keyword arguments passed to download_file().

        Raises:
            FileOperationError: If the download operation fails.
        """
        return files_module.download_file(self._tapis, *args, **kwargs)

    def list(self, *args, **kwargs) -> List[Tapis]:
        """List files and directories in a Tapis storage system path.

        This is a convenience wrapper around files_module.list_files().

        Args:
            *args: Positional arguments passed to list_files().
            **kwargs: Keyword arguments passed to list_files().

        Returns:
            List[Tapis]: List of file/directory objects from the specified path.

        Raises:
            FileOperationError: If the listing operation fails.
        """
        return files_module.list_files(self._tapis, *args, **kwargs)


class ProjectMethods:
    """Interface for DesignSafe project management.

    Provides methods for listing projects, getting project metadata,
    and listing files within projects.

    Args:
        tapis_client (Tapis): Authenticated Tapis client instance.
    """

    def __init__(self, tapis_client: Tapis):
        self._tapis = tapis_client

    def list(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List DesignSafe projects you have access to.

        Args:
            limit (int, optional): Maximum projects to return. Defaults to 100.
            offset (int, optional): Number of projects to skip. Defaults to 0.

        Returns:
            List[Dict]: List of project dicts with uuid, projectId, title, pi, etc.

        Example:
            >>> projects = ds.projects.list()
            >>> for p in projects[:3]:
            ...     print(f"{p['projectId']} - {p['title']}")
        """
        return projects_module.list_projects(self._tapis, limit=limit, offset=offset)

    def get(self, project_id: str) -> Dict:
        """Get detailed metadata for a project.

        Args:
            project_id (str): Project ID (e.g., "PRJ-1305").

        Returns:
            Dict: Project metadata including title, description, PI, team,
                DOIs, award numbers, keywords, systemId.

        Example:
            >>> info = ds.projects.get("PRJ-6270")
            >>> print(info["title"])
            >>> print(info["systemId"])
        """
        return projects_module.get_project(self._tapis, project_id)

    def files(self, project_id: str, path: str = "/", limit: int = 100) -> List:
        """List files in a project.

        Args:
            project_id (str): Project ID (e.g., "PRJ-1305").
            path (str, optional): Path within the project. Defaults to "/".
            limit (int, optional): Max items to return. Defaults to 100.

        Returns:
            List: List of Tapis file objects.

        Example:
            >>> files = ds.projects.files("PRJ-1305", "/Training/")
            >>> for f in files[:5]:
            ...     print(f"{f.name} ({f.type})")
        """
        return projects_module.list_project_files(
            self._tapis, project_id, path=path, limit=limit
        )


class SystemMethods:
    """Interface for Tapis system information and queue management.

    This class provides methods for retrieving information about Tapis
    execution systems and their available job queues.

    Args:
        tapis_client (Tapis): Authenticated Tapis client instance.
    """

    def __init__(self, tapis_client: Tapis):
        """Initialize SystemMethods with a Tapis client.

        Args:
            tapis_client (Tapis): Authenticated Tapis client instance.
        """
        self._tapis = tapis_client

    def queues(self, system_id: str, verbose: bool = True) -> List[Any]:
        """List logical queues available on a Tapis execution system.

        This is a convenience wrapper around systems_module.list_system_queues().

        Args:
            system_id (str): The ID of the execution system (e.g., 'frontera').
            verbose (bool, optional): If True, prints detailed queue information.
                Defaults to True.

        Returns:
            List[Any]: List of queue objects with queue configuration details.

        Raises:
            SystemInfoError: If the system is not found or queue retrieval fails.
            ValueError: If system_id is empty.
        """
        return systems_module.list_system_queues(
            self._tapis, system_id, verbose=verbose
        )

    def check_credentials(self, system_id: str, username: str = None) -> bool:
        """Check whether TMS credentials exist for a user on a system.

        Args:
            system_id (str): The ID of the Tapis system (e.g., 'frontera').
            username (str, optional): Username to check. Defaults to
                the authenticated user.

        Returns:
            bool: True if credentials exist, False otherwise.

        Raises:
            CredentialError: If the credential check fails unexpectedly.
            ValueError: If system_id is empty.
        """
        return systems_module.check_credentials(
            self._tapis, system_id, username=username
        )

    def establish_credentials(
        self,
        system_id: str,
        username: str = None,
        force: bool = False,
        verbose: bool = True,
    ) -> None:
        """Establish TMS credentials for a user on a Tapis system.

        Idempotent: skips creation if credentials already exist (unless force=True).
        Only supported for systems using TMS_KEYS authentication.

        Args:
            system_id (str): The ID of the Tapis system (e.g., 'frontera').
            username (str, optional): Username. Defaults to the authenticated user.
            force (bool, optional): Re-create even if credentials exist.
                Defaults to False.
            verbose (bool, optional): Print status messages. Defaults to True.

        Raises:
            CredentialError: If the system is not TMS_KEYS or creation fails.
            ValueError: If system_id is empty.
        """
        return systems_module.establish_credentials(
            self._tapis,
            system_id,
            username=username,
            force=force,
            verbose=verbose,
        )

    def revoke_credentials(
        self,
        system_id: str,
        username: str = None,
        verbose: bool = True,
    ) -> None:
        """Remove TMS credentials for a user on a Tapis system.

        Idempotent: succeeds silently if credentials do not exist.

        Args:
            system_id (str): The ID of the Tapis system (e.g., 'frontera').
            username (str, optional): Username. Defaults to the authenticated user.
            verbose (bool, optional): Print status messages. Defaults to True.

        Raises:
            CredentialError: If credential removal fails unexpectedly.
            ValueError: If system_id is empty.
        """
        return systems_module.revoke_credentials(
            self._tapis, system_id, username=username, verbose=verbose
        )


class ParametricSweepMethods:
    """Interface for PyLauncher parameter sweeps.

    - ``generate`` — preview (``preview=True``) or write sweep files.
    - ``submit`` — submit the sweep job to TACC.
    """

    def __init__(self, tapis_client):
        self._tapis = tapis_client

    def generate(
        self,
        command: str,
        sweep: Dict[str, Any],
        directory: str = None,
        *,
        placeholder_style: str = "token",
        debug: str = None,
        preview: bool = False,
    ):
        """Generate PyLauncher sweep files or preview the parameter grid.

        With ``preview=True``, returns a DataFrame of all parameter
        combinations — no files are written.

        Otherwise, expands *command* into one command per combination
        and writes ``runsList.txt`` and ``call_pylauncher.py`` into
        *directory*. Returns the list of generated commands.

        Args:
            command: Command template with placeholders matching sweep keys.
            sweep: Mapping of placeholder name to sequence of values.
            directory: Directory to write files into (created if needed).
                Required when *preview* is ``False``.
            placeholder_style: ``"token"`` (default) for bare ``ALPHA``,
                or ``"braces"`` for ``{ALPHA}``.
            debug: Optional debug string (e.g. ``"host+job"``).
            preview: If ``True``, return a DataFrame (dry run).

        Returns:
            ``List[str]`` of commands, or ``pandas.DataFrame`` when
            *preview* is ``True``.
        """
        return launcher_module.generate_sweep(
            command,
            sweep,
            directory,
            placeholder_style=placeholder_style,
            debug=debug,
            preview=preview,
        )

    def submit(
        self,
        directory: str,
        app_id: str,
        allocation: str,
        *,
        node_count: Optional[int] = None,
        cores_per_node: Optional[int] = None,
        max_minutes: Optional[int] = None,
        queue: Optional[str] = None,
        archive_system: Optional[str] = "designsafe",
        archive_path: Optional[str] = None,
        **kwargs,
    ):
        """Submit a PyLauncher sweep job.

        Translates *directory* to a Tapis URI, builds a job request with
        ``call_pylauncher.py`` as the script, and submits it.

        Archives to the user's DesignSafe storage by default (not the
        app's archive path, which may belong to the app owner).

        Args:
            directory: Path to the input directory containing
                ``runsList.txt`` and ``call_pylauncher.py``
                (e.g. ``"/MyData/sweep/"``).
            app_id: Tapis application ID (e.g. ``"designsafe-agnostic-app"``).
            allocation: TACC allocation to charge.
            node_count: Number of compute nodes.
            cores_per_node: Cores per node.
            max_minutes: Maximum runtime in minutes.
            queue: Execution queue name.
            archive_system: Archive system. Defaults to ``"designsafe"``
                (the user's own storage).
            archive_path: Archive directory path. If None, uses the
                default ``tapis-jobs-archive/`` under the user's MyData.
            **kwargs: Additional arguments passed to
                ``ds.jobs.generate()``.

        Returns:
            SubmittedJob: A job object for monitoring via ``.monitor()``.
        """
        input_uri = files_module.get_ds_path_uri(self._tapis, directory)
        job_request = jobs_module.generate_job_request(
            tapis_client=self._tapis,
            app_id=app_id,
            input_dir_uri=input_uri,
            script_filename="call_pylauncher.py",
            node_count=node_count,
            cores_per_node=cores_per_node,
            max_minutes=max_minutes,
            queue=queue,
            allocation=allocation,
            archive_system=archive_system,
            archive_path=archive_path,
            **kwargs,
        )
        return jobs_module.submit_job_request(self._tapis, job_request)


class JobMethods:
    """Interface for Tapis job submission, monitoring, and management.

    This class provides methods for generating job requests, submitting jobs,
    monitoring job status, and managing submitted jobs.

    Args:
        tapis_client (Tapis): Authenticated Tapis client instance.

    Attributes:
        parametric_sweep (ParametricSweepMethods): Interface for PyLauncher
            parameter sweep generation.
    """

    def __init__(self, tapis_client: Tapis):
        """Initialize JobMethods with a Tapis client.

        Args:
            tapis_client (Tapis): Authenticated Tapis client instance.
        """
        self._tapis = tapis_client
        self.parametric_sweep = ParametricSweepMethods(tapis_client)

    # Method to generate the request dictionary
    def generate(
        self,
        app_id: str,
        input_dir_uri: str,
        # --- Optional Overrides ---
        script_filename: Optional[str] = None,
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
        archive_system: Optional[str] = None,
        archive_path: Optional[str] = None,
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
        """Generate a Tapis job request dictionary based on app definition and inputs.

        This method creates a properly formatted job request dictionary that can be
        submitted to Tapis. It automatically retrieves app details and applies
        user-specified overrides and extra parameters.

        Args:
            app_id (str): The ID of the Tapis application to use for the job.
            input_dir_uri (str): Tapis URI to the input directory containing job files.
            script_filename (str, optional): Name of the main script file to execute.
                If None, no script parameter is added (suitable for apps like OpenFOAM).
            app_version (str, optional): Specific app version. If None, uses latest.
            job_name (str, optional): Custom job name. If None, auto-generates one.
            description (str, optional): Job description. If None, uses app description.
            tags (List[str], optional): List of tags to associate with the job.
            max_minutes (int, optional): Maximum runtime in minutes. Overrides app default.
            node_count (int, optional): Number of compute nodes. Overrides app default.
            cores_per_node (int, optional): Cores per node. Overrides app default.
            memory_mb (int, optional): Memory in MB. Overrides app default.
            queue (str, optional): Execution queue name. Overrides app default.
            allocation (str, optional): TACC allocation to charge for compute time.
            archive_system (str, optional): Archive system for job outputs. Use "designsafe"
                for designsafe.storage.default. If None, uses app default.
            archive_path (str, optional): Archive directory path. Can be a full path or just
                a directory name in MyData. If None and archive_system is "designsafe",
                defaults to "tapis-jobs-archive/${JobCreateDate}/${JobUUID}".
            extra_file_inputs (List[Dict[str, Any]], optional): Additional file inputs.
            extra_app_args (List[Dict[str, Any]], optional): Additional app arguments.
            extra_env_vars (List[Dict[str, Any]], optional): Additional environment variables.
            extra_scheduler_options (List[Dict[str, Any]], optional): Additional scheduler options.
            script_param_names (List[str], optional): Parameter names to check for script placement.
            input_dir_param_name (str, optional): Parameter name for input directory.
            allocation_param_name (str, optional): Parameter name for allocation.

        Returns:
            Dict[str, Any]: Complete job request dictionary ready for submission.

        Raises:
            AppDiscoveryError: If the specified app cannot be found.
            ValueError: If required parameters are missing or invalid.
            JobSubmissionError: If job request generation fails.

        Example:
            >>> job_request = ds.jobs.generate(
            ...     app_id="matlab-r2023a",
            ...     input_dir_uri="tapis://designsafe.storage.default/username/input/",
            ...     script_filename="run_analysis.m",
            ...     max_minutes=120,
            ...     allocation="MyProject-123",
            ... )
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
            archive_system=archive_system,
            archive_path=archive_path,
            extra_file_inputs=extra_file_inputs,
            extra_app_args=extra_app_args,
            extra_env_vars=extra_env_vars,
            extra_scheduler_options=extra_scheduler_options,
            script_param_names=script_param_names,
            input_dir_param_name=input_dir_param_name,
            allocation_param_name=allocation_param_name,
        )

    # Method to submit the generated request dictionary
    def submit(self, job_request: Dict[str, Any]) -> SubmittedJob:
        """Submit a job request dictionary to Tapis.

        Takes a job request dictionary (typically from ``generate()``) and
        submits it to Tapis for execution.

        Args:
            job_request (Dict[str, Any]): Complete job request dictionary.

        Returns:
            SubmittedJob: A SubmittedJob object for monitoring and managing the job.

        Raises:
            ValueError: If job_request is not a dictionary.
            JobSubmissionError: If the Tapis submission fails.

        Example:
            >>> job_request = ds.jobs.generate(...)
            >>> job = ds.jobs.submit(job_request)
            >>> print(f"Job submitted with UUID: {job.uuid}")
        """
        return jobs_module.submit_job_request(self._tapis, job_request)

    def job(self, job_uuid: str) -> SubmittedJob:
        """Get a SubmittedJob object for an existing job by UUID.

        Args:
            job_uuid (str): The UUID of an existing Tapis job.

        Returns:
            SubmittedJob: A job object for monitoring via ``.monitor()``.

        Example:
            >>> job = ds.jobs.job("12345678-1234-1234-1234-123456789abc")
            >>> job.monitor()
        """
        return SubmittedJob(self._tapis, job_uuid)

    def status(self, job_uuid: str) -> str:
        """Get the current status of a job by UUID.

        Args:
            job_uuid (str): The UUID of the job to check.

        Returns:
            str: The current job status (e.g., "QUEUED", "RUNNING", "FINISHED").

        Raises:
            JobMonitorError: If status retrieval fails.

        Example:
            >>> ds.jobs.status("12345678-1234-1234-1234-123456789abc")
            'FINISHED'
        """
        return jobs_module.get_job_status(self._tapis, job_uuid)

    def runtime_summary(self, job_uuid: str, verbose: bool = False):
        """Print the runtime summary for a job by UUID.

        Args:
            job_uuid (str): The UUID of the job to analyze.
            verbose (bool, optional): If True, prints detailed job history events.
                Defaults to False.

        Example:
            >>> ds.jobs.runtime_summary("12345678-1234-1234-1234-123456789abc")
            Runtime Summary
            ---------------
            QUEUED  time: 00:05:30
            RUNNING time: 01:23:45
            TOTAL   time: 01:29:15
        """
        jobs_module.get_runtime_summary(self._tapis, job_uuid, verbose=verbose)

    def interpret_status(self, final_status: str, job_uuid: Optional[str] = None):
        """Print a user-friendly interpretation of a job status.

        Args:
            final_status (str): The job status to interpret.
            job_uuid (str, optional): The job UUID for context in the message.

        Example:
            >>> ds.jobs.interpret_status(
            ...     "FINISHED", "12345678-1234-1234-1234-123456789abc"
            ... )
            Job 12345678-1234-1234-1234-123456789abc completed successfully.
        """
        jobs_module.interpret_job_status(final_status, job_uuid)

    def list(
        self,
        app_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        output: str = "df",
        verbose: bool = False,
    ):
        """List jobs with optional filtering.

        Fetches jobs from Tapis ordered by creation date (newest first).
        Filters are applied client-side.

        Args:
            app_id (str, optional): Filter by application ID.
            status (str, optional): Filter by job status (e.g., "FINISHED").
                Case-insensitive.
            limit (int, optional): Maximum jobs to fetch. Defaults to 100.
            output (str, optional): Output format. "df" for pandas DataFrame
                (default), "list" for list of dicts, "raw" for TapisResult
                objects.
            verbose (bool, optional): Print job count. Defaults to False.

        Returns:
            Depends on output: DataFrame, list of dicts, or list of
            TapisResult objects.

        Raises:
            JobMonitorError: If the Tapis API call fails.

        Example:
            >>> df = ds.jobs.list(app_id="matlab-r2023a", status="FINISHED")
            >>> jobs = ds.jobs.list(output="list")
            >>> raw = ds.jobs.list(limit=10, output="raw")
        """
        return jobs_module.list_jobs(
            self._tapis,
            app_id=app_id,
            status=status,
            limit=limit,
            output=output,
            verbose=verbose,
        )
