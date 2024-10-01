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
    }

    # Handle input file based on app name
    if "opensees" in app_name.lower():
        job_info["parameterSet"] = {
            "envVariables": [{"key": "tclScript", "value": input_file}]
        }
    else:
        job_info["parameterSet"] = {
            "appArgs": [{"name": "Input Script", "arg": input_file}]
        }

    # Add TACC allocation if provided
    if allocation:
        if "schedulerOptions" not in job_info["parameterSet"]:
            job_info["parameterSet"]["schedulerOptions"] = []
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


def runtime_summary(t, job_uuid, verbose=False):
    """Get the runtime of a job.
    Args:
    t (object): The Tapis v3 client object.
    job_uuid (str): The UUID of the job for which the runtime needs to be determined.
    verbose (bool): If True, prints all history events. Otherwise, prints only specific statuses.
    Returns:
    None: This function doesn't return a value, but it prints the runtime details.
    """
    from datetime import datetime, timedelta

    print("\nRuntime Summary")
    print("---------------")
    hist = t.jobs.getJobHistory(jobUuid=job_uuid)

    def format_timedelta(td):
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    time1 = datetime.strptime(hist[-1].created, "%Y-%m-%dT%H:%M:%S.%fZ")
    time0 = datetime.strptime(hist[0].created, "%Y-%m-%dT%H:%M:%S.%fZ")
    total_time = time1 - time0

    if verbose:
        print("\nDetailed Job History:")
        for event in hist:
            print(
                f"Event: {event.event}, Detail: {event.eventDetail}, Time: {event.created}"
            )
        print("\nSummary:")

    for i in range(len(hist) - 1):
        if hist[i].eventDetail == "RUNNING":
            time1 = datetime.strptime(hist[i + 1].created, "%Y-%m-%dT%H:%M:%S.%fZ")
            time0 = datetime.strptime(hist[i].created, "%Y-%m-%dT%H:%M:%S.%fZ")
            print("RUNNING time:", format_timedelta(time1 - time0))
        elif hist[i].eventDetail == "QUEUED":
            time1 = datetime.strptime(hist[i + 1].created, "%Y-%m-%dT%H:%M:%S.%fZ")
            time0 = datetime.strptime(hist[i].created, "%Y-%m-%dT%H:%M:%S.%fZ")
            print("QUEUED  time:", format_timedelta(time1 - time0))

    print("TOTAL   time:", format_timedelta(total_time))
    print("---------------")
