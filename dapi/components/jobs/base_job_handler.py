from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class BaseJobHandler(ABC):
    """Abstract base class for job handlers."""

    def __init__(self, default_app_name: str):
        self.default_app_name = default_app_name

    def generate_job_info(
        self,
        tapis_client,
        input_uri: str,
        input_file: str,
        job_name: Optional[str] = None,
        app_name: Optional[str] = None,
        max_minutes: Optional[int] = None,
        node_count: Optional[int] = None,
        cores_per_node: Optional[int] = None,
        queue: Optional[str] = None,
        allocation: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate job information for a Tapis app.

        Args:
            tapis_client: Tapis client instance.
            input_uri: URI of the input directory or file.
            input_file: File to be used by the job.
            job_name: Optional job name.
            app_name: Name of the application (defaults to the handler's default app).
            max_minutes: Maximum runtime in minutes.
            node_count: Number of nodes to use.
            cores_per_node: Number of cores per node.
            queue: Queue name for job execution.
            allocation: Allocation for compute resources.
            additional_params: Additional parameters specific to the application.

        Returns:
            A dictionary containing job configuration details.
        """
        app_name = app_name or self.default_app_name
        app_info = tapis_client.apps.getAppLatestVersion(appId=app_name)
        job_name = job_name or self.default_job_name(app_name)

        job_info = {
            "name": job_name,
            "appId": app_info.id,
            "appVersion": app_info.version,
            "execSystemId": app_info.jobAttributes.execSystemId,
            "maxMinutes": max_minutes or app_info.jobAttributes.maxMinutes,
            "archiveOnAppError": app_info.jobAttributes.archiveOnAppError,
            "fileInputs": [{"name": "Input Directory", "sourceUrl": input_uri}],
            "execSystemLogicalQueue": queue
            or app_info.jobAttributes.execSystemLogicalQueue,
            "nodeCount": node_count or 1,
            "coresPerNode": cores_per_node or 1,
            "parameterSet": {
                "appArgs": [{"name": "Input Script", "arg": input_file}],
            },
        }

        # Add additional environment variables or application parameters
        if additional_params:
            job_info["parameterSet"].update(additional_params)

        # Add TACC allocation if provided
        if allocation:
            job_info["parameterSet"].setdefault("schedulerOptions", []).append(
                {"name": "TACC Allocation", "arg": f"-A {allocation}"}
            )

        return job_info

    @staticmethod
    def default_job_name(app_name: str) -> str:
        """Generate a default job name based on the app name and timestamp."""
        return f"{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
