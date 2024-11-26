from typing import Dict, Any, Optional
from .base_job_handler import BaseJobHandler


class MpmJobHandler(BaseJobHandler):
    """Custom handler for MPM (Material Point Method) jobs."""

    def generate_job_info(
        self,
        tapis_client,
        input_uri: str,
        input_file: str,
        job_name: Optional[str] = None,
        max_minutes: Optional[int] = None,
        node_count: Optional[int] = None,
        cores_per_node: Optional[int] = None,
        queue: Optional[str] = None,
        allocation: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Get app info for the single MPM app
        app_info = tapis_client.apps.getApp(appId="mpm")

        # Create the base job info
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
            "nodeCount": node_count or 1,  # Default to 1 if not specified
            "coresPerNode": cores_per_node or 1,  # Default to 1 if not specified
            "parameterSet": {
                "appArgs": [{"name": "Input Script", "arg": input_file}],
                "schedulerOptions": [],
            },
        }

        # Add TACC allocation if provided
        if allocation:
            job_info["parameterSet"]["schedulerOptions"].append(
                {"name": "TACC Allocation", "arg": f"-A {allocation}"}
            )

        return job_info
