import time
from datetime import datetime, timedelta, timezone
from tqdm import tqdm
import logging
import json
from typing import Dict, Any, Optional

# Configuring the logging system
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )


def generate_job_info(
    t: Any,  # Tapis client
    app_name: str,
    input_uri: str,
    input_file: str,
    job_name: str = None,
    max_minutes: Optional[int] = None,
    node_count: Optional[int] = None,
    cores_per_node: Optional[int] = None,
    queue: Optional[str] = None,
    allocation: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a job info dictionary based on the provided application name, job name, input URI, input file, and optional allocation.

    Args:
        t (object): The Tapis API client object.
        app_name (str): The name of the application to use for the job.
        input_uri (str): The URI of the input data for the job.
        input_file (str): The local file path to the input data for the job.
        job_name (str, optional): The name of the job to be created. Defaults to None.
        max_minutes (int, optional): The maximum number of minutes the job can run. Defaults to None.
        node_count (int, optional): The number of nodes to use for the job. Defaults to None.
        cores_per_node (int, optional): The number of cores per node for the job. Defaults to None.
        queue (str, optional): The queue to use for the job. Defaults to None.
        allocation (str, optional): The allocation to use for the job. Defaults to None.

    Returns:
        dict: The job info dictionary.
    """

    # Fetch the latest app information
    app_info = t.apps.getAppLatestVersion(appId=app_name)

    # If job_name is not provided, use the app name and date
    if not job_name:
        job_name = f"{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

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


def get_status(t, mjobUuid, tlapse=15):
    """
    Retrieves and monitors the status of a job using Tapis API.
    This function waits for the job to start, then monitors it for up to maxMinutes.

    Args:
    t (object): The Tapis API client object.
    mjobUuid (str): The unique identifier of the job to monitor.
    tlapse (int, optional): Time interval, in seconds, to wait between status checks. Defaults to 15 seconds.

    Returns:
    str: The final status of the job (FINISHED, FAILED, or STOPPED).
    """
    previous_status = None
    # Initially check if the job is already running
    status = t.jobs.getJobStatus(jobUuid=mjobUuid).status
    max_minutes = t.jobs.getJob(jobUuid=mjobUuid).maxMinutes

    # Using tqdm to provide visual feedback while waiting for job to start
    with tqdm(desc="Waiting for job to start", dynamic_ncols=True) as pbar:
        while status not in ["RUNNING", "FINISHED", "FAILED", "STOPPED"]:
            time.sleep(tlapse)
            status = t.jobs.getJobStatus(jobUuid=mjobUuid).status
            pbar.update(1)
            pbar.set_postfix_str(f"Status: {status}")

    # Once the job is running, monitor it for up to maxMinutes
    max_iterations = int(max_minutes * 60 // tlapse)

    # Using tqdm for progress bar
    for _ in tqdm(range(max_iterations), desc="Monitoring job", ncols=100):
        status = t.jobs.getJobStatus(jobUuid=mjobUuid).status

        # Print status if it has changed
        if status != previous_status:
            tqdm.write(f"\tStatus: {status}")
            previous_status = status

        # Break the loop if job reaches one of these statuses
        if status in ["FINISHED", "FAILED", "STOPPED"]:
            break

        time.sleep(tlapse)
    else:
        # This block will execute if the for loop completes without a 'break'
        logging.warning(
            f"Warning: Maximum monitoring time of {max_minutes} minutes reached!"
        )

    return status


def runtime_summary(ag, job_id, verbose=False):
    """Get the runtime of a job.

    Args:
        ag (object): The Agave object that has the job details.
        job_id (str): The ID of the job for which the runtime needs to be determined.
        verbose (bool): If True, prints all statuses. Otherwise, prints only specific statuses.

    Returns:
        None: This function doesn't return a value, but it prints the runtime details.

    """

    print("Runtime Summary")
    print("---------------")

    job_history = ag.jobs.getHistory(jobId=job_id)
    total_time = job_history[-1]["created"] - job_history[0]["created"]

    status_times = {}

    for i in range(len(job_history) - 1):
        current_status = job_history[i]["status"]
        elapsed_time = job_history[i + 1]["created"] - job_history[i]["created"]

        # Aggregate times for each status
        if current_status in status_times:
            status_times[current_status] += elapsed_time
        else:
            status_times[current_status] = elapsed_time

    # Filter the statuses if verbose is False
    if not verbose:
        filtered_statuses = {
            "PENDING",
            "QUEUED",
            "RUNNING",
            "FINISHED",
            "FAILED",
        }
        status_times = {
            status: time
            for status, time in status_times.items()
            if status in filtered_statuses
        }

    # Determine the max width of status names for alignment
    max_status_width = max(len(status) for status in status_times.keys())

    # Print the aggregated times for each unique status in a table format
    for status, time in status_times.items():
        print(f"{status.upper():<{max_status_width + 2}} time: {time}")

    print(f"{'TOTAL':<{max_status_width + 2}} time: {total_time}")
    print("---------------")


def get_archive_path(ag, job_id):
    """
    Get the archive path for a given job ID and modifies the user directory
    to '/home/jupyter/MyData'.

    Args:
        ag (object): The Agave object to interact with the platform.
        job_id (str): The job ID to retrieve the archive path for.

    Returns:
        str: The modified archive path.

    Raises:
        ValueError: If the archivePath format is unexpected.
    """

    # Fetch the job info.
    job_info = ag.jobs.get(jobId=job_id)

    # Try to split the archive path to extract the user.
    try:
        user, _ = job_info.archivePath.split("/", 1)
    except ValueError:
        raise ValueError(f"Unexpected archivePath format for jobId={job_id}")

    # Construct the new path.
    new_path = job_info.archivePath.replace(user, "/home/jupyter/MyData")

    return new_path
