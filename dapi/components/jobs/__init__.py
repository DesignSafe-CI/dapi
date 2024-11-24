from typing import Dict, Type, Any, Optional
from .base_job_handler import BaseJobHandler
from ...core import BaseComponent  # Importing BaseComponent from core
from datetime import datetime
from tqdm import tqdm
import time


class JobsComponent(BaseComponent):
    """Jobs component for managing Tapis jobs."""

    def __init__(self, api):
        super().__init__(api)
        self.handlers: Dict[str, Type[BaseJobHandler]] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default job handlers."""
        from .opensees_job_handler import OpenSeesJobHandler  # Import default handlers

        self.register_handler("opensees", OpenSeesJobHandler)

    def register_handler(
        self, app_name: str, handler_class: Type[BaseJobHandler]
    ) -> None:
        """Register a handler for a specific app."""
        self.handlers[app_name] = handler_class

        # Dynamically add a method for the app
        def app_method(
            input_file: str,
            input_uri: Optional[str] = None,
            job_name: Optional[str] = None,
            max_minutes: Optional[int] = None,
            node_count: Optional[int] = None,
            cores_per_node: Optional[int] = None,
            queue: Optional[str] = None,
            allocation: Optional[str] = None,
        ) -> Any:
            handler = self.handlers[app_name](app_name)
            job_info = handler.generate_job_info(
                self.tapis,
                input_uri or "tapis://example/input/",
                input_file,
                job_name,
                max_minutes,
                node_count,
                cores_per_node,
                queue,
                allocation,
            )
            return job_info

        setattr(self, app_name, app_method)

    def submit_job(self, job_info: Dict[str, Any]) -> Any:
        """Submit a job to Tapis."""
        response = self.tapis.jobs.submitJob(**job_info)
        return response

    def monitor_job(self, job_uuid: str, interval: int = 15) -> str:
        """Monitor the status of a job."""
        status = self.tapis.jobs.getJobStatus(jobUuid=job_uuid).status
        max_minutes = self.tapis.jobs.getJob(jobUuid=job_uuid).maxMinutes
        previous_status = None

        with tqdm(desc="Monitoring Job", dynamic_ncols=True) as pbar:
            for _ in range(int(max_minutes * 60 / interval)):
                time.sleep(interval)
                status = self.tapis.jobs.getJobStatus(jobUuid=job_uuid).status
                if status != previous_status:
                    tqdm.write(f"Status changed: {status}")
                    previous_status = status

                if status in ["FINISHED", "FAILED", "STOPPED"]:
                    break
                pbar.update(1)

        return status

    def get_job_history(self, job_uuid: str) -> Dict[str, Any]:
        """Retrieve job history and compute timings."""
        history = self.tapis.jobs.getJobHistory(jobUuid=job_uuid)
        timing_summary = {}

        def parse_timestamps(event_list, event_name):
            timestamps = [
                datetime.strptime(event.created, "%Y-%m-%dT%H:%M:%S.%fZ")
                for event in event_list
                if event.eventDetail == event_name
            ]
            return timestamps

        queued_times = parse_timestamps(history, "QUEUED")
        running_times = parse_timestamps(history, "RUNNING")

        if queued_times and running_times:
            timing_summary["QUEUED"] = (
                running_times[0] - queued_times[0]
            ).total_seconds()

        if running_times and len(running_times) > 1:
            timing_summary["RUNNING"] = (
                running_times[-1] - running_times[0]
            ).total_seconds()

        return timing_summary
