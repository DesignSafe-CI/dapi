from typing import Dict, Any, Optional
from .base_job_handler import BaseJobHandler


class OpenSeesJobHandler(BaseJobHandler):
    """Custom handler for OpenSees jobs."""

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
    ) -> Dict[str, Any]:
        # Custom environment variables for OpenSees
        additional_params = {
            "envVariables": [{"key": "tclScript", "value": input_file}]
        }
        app_name

        # Call the generic generate_job_info with OpenSees-specific params
        return super().generate_job_info(
            tapis_client=tapis_client,
            input_uri=input_uri,
            input_file=input_file,
            job_name=job_name,
            app_name=app_name,
            max_minutes=max_minutes,
            node_count=node_count,
            cores_per_node=cores_per_node,
            queue=queue,
            allocation=allocation,
            additional_params=additional_params,
        )
