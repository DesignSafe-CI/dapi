import time
from datetime import datetime, timedelta, timezone
from tqdm import tqdm
import logging

# Configuring the logging system
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )


def get_status(ag, job_id, time_lapse=15):
    """
    Retrieves and monitors the status of a job from Agave.

    This function initially waits for the job to start, displaying its progress using
    a tqdm progress bar. Once the job starts, it monitors the job's status up to
    a maximum duration specified by the job's "maxHours". If the job completes or fails
    before reaching this maximum duration, it returns the job's final status.

    Args:
      ag (object): The Agave job object used to interact with the job.
      job_id (str): The unique identifier of the job to monitor.
      time_lapse (int, optional): Time interval, in seconds, to wait between status
        checks. Defaults to 15 seconds.

    Returns:
      str: The final status of the job. Typical values include "FINISHED", "FAILED",
           and "STOPPED".

    Raises:
      No exceptions are explicitly raised, but potential exceptions raised by the Agave
      job object or other called functions/methods will propagate.
    """

    previous_status = None
    # Initially check if the job is already running
    status = ag.jobs.getStatus(jobId=job_id)["status"]

    job_details = ag.jobs.get(jobId=job_id)
    max_hours = job_details["maxHours"]

    # Using tqdm to provide visual feedback while waiting for job to start
    with tqdm(desc="Waiting for job to start", dynamic_ncols=True) as pbar:
        while status not in ["RUNNING", "FINISHED", "FAILED", "STOPPED"]:
            time.sleep(time_lapse)
            status = ag.jobs.getStatus(jobId=job_id)["status"]
            pbar.update(1)
            pbar.set_postfix_str(f"Status: {status}")

    # Once the job is running, monitor it for up to maxHours
    max_iterations = int(max_hours * 3600 // time_lapse)

    # Using tqdm for progress bar
    for _ in tqdm(range(max_iterations), desc="Monitoring job", ncols=100):
        status = ag.jobs.getStatus(jobId=job_id)["status"]

        # Print status if it has changed
        if status != previous_status:
            tqdm.write(f"\tStatus: {status}")
            previous_status = status

        # Break the loop if job reaches one of these statuses
        if status in ["FINISHED", "FAILED", "STOPPED"]:
            break

        time.sleep(time_lapse)
    else:
        # This block will execute if the for loop completes without a 'break'
        logging.warn("Warning: Maximum monitoring time reached!")

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


def generate_job_info(
    ag,
    appid: str,
    jobname: str = "dsjob",
    queue: str = "development",
    nnodes: int = 1,
    nprocessors: int = 1,
    runtime: str = "00:10:00",
    inputs=None,
    parameters=None,
) -> dict:
    """Generate a job information dictionary based on provided arguments.

    Args:
        ag (object): The Agave object to interact with the platform.
        appid (str): The application ID for the job.
        jobname (str, optional): The name of the job. Defaults to 'dsjob'.
        queue (str, optional): The batch queue name. Defaults to 'skx-dev'.
        nnodes (int, optional): The number of nodes required. Defaults to 1.
        nprocessors (int, optional): The number of processors per node. Defaults to 1.
        runtime (str, optional): The maximum runtime in the format 'HH:MM:SS'. Defaults to '00:10:00'.
        inputs (dict, optional): The inputs for the job. Defaults to None.
        parameters (dict, optional): The parameters for the job. Defaults to None.

    Returns:
        dict: A dictionary containing the job information.

    Raises:
        ValueError: If the provided appid is not valid.
    """

    try:
        app = ag.apps.get(appId=appid)
    except Exception:
        raise ValueError(f"Invalid app ID: {appid}")

    job_info = {
        "appId": appid,
        "name": jobname,
        "batchQueue": queue,
        "nodeCount": nnodes,
        "processorsPerNode": nprocessors,
        "memoryPerNode": "1",
        "maxRunTime": runtime,
        "archive": True,
        "inputs": inputs,
        "parameters": parameters,
    }

    return job_info


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
