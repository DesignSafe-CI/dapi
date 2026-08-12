# dapi/jobs.py
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from tqdm.auto import tqdm
import pandas as pd
from . import profiles
from .apps import get_app_details
from .exceptions import (
    DapiException,
    JobSubmissionError,
    JobMonitorError,
    FileOperationError,
    AppDiscoveryError,
)

import logging

logger = logging.getLogger(__name__)

# --- Module-Level Status Constants ---
STATUS_TIMEOUT = "TIMEOUT"
STATUS_INTERRUPTED = "INTERRUPTED"
STATUS_MONITOR_ERROR = "MONITOR_ERROR"
STATUS_UNKNOWN = "UNKNOWN"
TAPIS_TERMINAL_STATES = [
    "FINISHED",
    "FAILED",
    "CANCELLED",
    "STOPPED",
    "ARCHIVING_FAILED",
]

# Shareable job resources (Tapis grants READ only). JOB_INPUT is included by
# default so grantees can inspect and reproduce the run.
JOB_SHARE_RESOURCES = [
    "JOB_HISTORY",
    "JOB_RESUBMIT_REQUEST",
    "JOB_OUTPUT",
    "JOB_INPUT",
]


def _resolve_share_grantees(
    tapis_client: Tapis,
    user_id: Optional[Any] = None,
    project_id: Optional[str] = None,
) -> List[str]:
    """Validate and resolve share grantees from users and/or a project.

    Both sources are validated before any grant is issued: every username
    must exist in the tenant (authenticator profile lookup) and the project
    must resolve via the DesignSafe projects API. The job owner is dropped
    from the resolved list.

    Args:
        tapis_client (Tapis): Authenticated Tapis client instance.
        user_id (str or List[str], optional): Username(s) to validate.
        project_id (str, optional): DesignSafe project (e.g., "PRJ-1234");
            resolves to all project users (PI, co-PIs, team members).

    Returns:
        List[str]: Validated, de-duplicated usernames.

    Raises:
        ValueError: If neither user_id nor project_id is given, a username
            does not exist, or no grantees remain after removing the owner.
        FileOperationError: If the project cannot be resolved.
    """
    if user_id is None and project_id is None:
        raise ValueError("Provide user_id and/or project_id.")

    grantees: List[str] = []
    users = [user_id] if isinstance(user_id, str) else list(user_id or [])
    for user in users:
        try:
            tapis_client.authenticator.get_profile(username=user)
        except BaseTapyException as e:
            raise ValueError(
                f"User '{user}' not found in tenant 'designsafe': {e}"
            ) from e
        grantees.append(user)

    if project_id is not None:
        from . import projects as projects_module

        members = projects_module.get_project_users(tapis_client, project_id)
        member_names = [m["username"] for m in members if m.get("username")]
        if not member_names:
            raise ValueError(f"Project '{project_id}' has no users to share with.")
        grantees.extend(member_names)

    owner = getattr(tapis_client, "username", None)
    seen: set = set()
    resolved = []
    for grantee in grantees:
        if grantee == owner:
            continue
        if grantee not in seen:
            seen.add(grantee)
            resolved.append(grantee)
    if not resolved:
        raise ValueError(
            "No grantees to share with (the job owner is excluded automatically)."
        )
    return resolved


def generate_job_request(
    tapis_client: Tapis,
    app_id: str,
    input_dir_uri: str,
    script_filename: Optional[
        str
    ] = None,  # Default is None, important for apps like OpenFOAM
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
    extra_file_inputs: Optional[List[Dict[str, Any]]] = None,
    extra_app_args: Optional[List[Dict[str, Any]]] = None,
    extra_env_vars: Optional[List[Dict[str, Any]]] = None,
    extra_scheduler_options: Optional[List[Dict[str, Any]]] = None,
    script_param_names: List[str] = ["Input Script", "Main Script", "tclScript"],
    input_dir_param_name: str = "Input Directory",  # Caller MUST override if app uses a different name (e.g., "Case Directory")
    allocation_param_name: str = "TACC Allocation",
) -> Dict[str, Any]:
    """Generate a Tapis job request dictionary based on app definition and inputs.

    Creates a properly formatted job request dictionary by retrieving the specified
    application details and applying user-provided overrides and additional parameters.
    The function automatically maps the script filename (if provided) and input
    directory to the appropriate app parameters. It dynamically reads the app definition
    to detect parameter names, determines whether to use appArgs or envVariables, and
    automatically populates all required parameters with default values when available.

    Args:
        tapis_client (Tapis): Authenticated Tapis client instance.
        app_id (str): The ID of the Tapis application to use for the job.
        input_dir_uri (str): Tapis URI to the input directory containing job files.
        script_filename (str, optional): Name of the main script file to execute.
            If None (default), no script parameter is added. This is suitable for
            apps like OpenFOAM that don't take a script argument.
        app_version (str, optional): Specific app version to use. If None, uses latest.
        job_name (str, optional): Custom job name. If None, auto-generates based on app ID and timestamp.
        description (str, optional): Job description. If None, uses app description.
        tags (List[str], optional): List of tags to associate with the job.
        max_minutes (int, optional): Maximum runtime in minutes. Overrides app default.
        node_count (int, optional): Number of compute nodes. Overrides app default.
        cores_per_node (int, optional): Cores per node. Overrides app default.
        memory_mb (int, optional): Memory in MB. Overrides app default.
        queue (str, optional): Execution queue name. Overrides app default.
        allocation (str, optional): TACC allocation to charge for compute time.
        archive_system (str, optional): Archive system for job outputs. If "designsafe" is specified,
            uses "designsafe.storage.default". If None, uses app default.
        archive_path (str, optional): Archive directory path. Can be a full path or just a directory name
            in MyData (e.g., "tapis-jobs-archive"). If None and archive_system is "designsafe",
            defaults to "${EffectiveUserId}/tapis-jobs-archive/${JobCreateDate}/${JobUUID}".
        extra_file_inputs (List[Dict[str, Any]], optional): Additional file inputs beyond the main input directory.
        extra_app_args (List[Dict[str, Any]], optional): Additional application arguments.
            Use for parameters expected in 'appArgs' by the Tapis app.
        extra_env_vars (List[Dict[str, Any]], optional): Additional environment variables.
            Use for parameters expected in 'envVariables' by the Tapis app (e.g., OpenFOAM solver, mesh).
            Each item should be a dict like {"key": "VAR_NAME", "value": "var_value"}.
        extra_scheduler_options (List[Dict[str, Any]], optional): Additional scheduler options.
        script_param_names (List[str], optional): Parameter names/keys to check for script placement
            if script_filename is provided. Defaults to ["Input Script", "Main Script", "tclScript"].
        input_dir_param_name (str, optional): The 'name' of the fileInput in the Tapis app definition
            that corresponds to input_dir_uri. Defaults to "Input Directory".
            The function will auto-detect the correct name from the app definition.
        allocation_param_name (str, optional): Parameter name for TACC allocation.
            Defaults to "TACC Allocation".

    Returns:
        Dict[str, Any]: Complete job request dictionary ready for submission to Tapis.

    Raises:
        AppDiscoveryError: If the specified app cannot be found or details cannot be retrieved.
        ValueError: If required parameters are missing, invalid, or if script_filename is provided
            but a suitable placement (matching script_param_names) cannot be found in the app's
            parameterSet.
        JobSubmissionError: If unexpected errors occur during job request generation.
    """
    logger.debug(f"Generating job request for app '{app_id}'...")
    try:
        app_details = get_app_details(tapis_client, app_id, app_version, verbose=False)
        if not app_details:
            raise AppDiscoveryError(
                f"App '{app_id}' (Version: {app_version or 'latest'}) not found."
            )
        final_app_version = app_details.version
        logger.debug(f"Using App Details: {app_details.id} v{final_app_version}")
        job_attrs = app_details.jobAttributes
        param_set_def = getattr(job_attrs, "parameterSet", None)
        final_job_name = (
            job_name or f"{app_details.id}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        final_description = (
            description or app_details.description or f"dapi job for {app_details.id}"
        )

        archive_system_id = None
        archive_system_dir = None
        if archive_system:
            if archive_system.lower() == "designsafe":
                archive_system_id = "designsafe.storage.default"
                if archive_path:
                    if archive_path.startswith("/") or archive_path.startswith("${"):
                        archive_system_dir = archive_path
                    else:
                        archive_system_dir = f"${{EffectiveUserId}}/{archive_path}/${{JobCreateDate}}/${{JobUUID}}"
                else:
                    archive_system_dir = "${EffectiveUserId}/tapis-jobs-archive/${JobCreateDate}/${JobUUID}"
            else:
                archive_system_id = archive_system
                if archive_path:
                    archive_system_dir = archive_path
        else:
            archive_system_id = getattr(job_attrs, "archiveSystemId", None)
            archive_system_dir = getattr(job_attrs, "archiveSystemDir", None)

        job_req = {
            "name": final_job_name,
            "appId": app_details.id,
            "appVersion": final_app_version,
            "description": final_description,
            "execSystemId": getattr(job_attrs, "execSystemId", None),
            "archiveSystemId": archive_system_id,
            **({"archiveSystemDir": archive_system_dir} if archive_system_dir else {}),
            "archiveOnAppError": getattr(job_attrs, "archiveOnAppError", True),
            "execSystemLogicalQueue": (
                queue
                if queue is not None
                else getattr(job_attrs, "execSystemLogicalQueue", None)
            ),
            "nodeCount": (
                node_count
                if node_count is not None
                else getattr(job_attrs, "nodeCount", None)
            ),
            "coresPerNode": (
                cores_per_node
                if cores_per_node is not None
                else getattr(job_attrs, "coresPerNode", None)
            ),
            "maxMinutes": (
                max_minutes
                if max_minutes is not None
                else getattr(job_attrs, "maxMinutes", None)
            ),
            "memoryMB": (
                memory_mb
                if memory_mb is not None
                else getattr(job_attrs, "memoryMB", None)
            ),
            **(
                {"isMpi": getattr(job_attrs, "isMpi", None)}
                if getattr(job_attrs, "isMpi", None) is not None
                else {}
            ),
            **(
                {"cmdPrefix": getattr(job_attrs, "cmdPrefix", None)}
                if getattr(job_attrs, "cmdPrefix", None) is not None
                else {}
            ),
            **({"tags": tags or []}),
            "fileInputs": [],
            "parameterSet": {"appArgs": [], "envVariables": [], "schedulerOptions": []},
        }

        # --- Handle main input directory ---
        # Automatically detect the correct input directory parameter name from app definition
        main_input_target_path = None
        main_input_automount = True
        found_input_def = False
        actual_input_param_name = input_dir_param_name  # Default fallback

        if hasattr(job_attrs, "fileInputs") and job_attrs.fileInputs:
            # First try to find exact match with provided name
            for fi_def in job_attrs.fileInputs:
                if getattr(fi_def, "name", "").lower() == input_dir_param_name.lower():
                    main_input_target_path = getattr(fi_def, "targetPath", None)
                    main_input_automount = getattr(fi_def, "autoMountLocal", True)
                    actual_input_param_name = getattr(fi_def, "name", "")
                    found_input_def = True
                    logger.debug(
                        f"Found exact match for input parameter: '{actual_input_param_name}'"
                    )
                    break

            # If no exact match found, try to auto-detect common input directory names
            if not found_input_def:
                common_input_names = [
                    "Input Directory",
                    "Case Directory",
                    "inputDirectory",
                    "inputDir",
                ]
                for fi_def in job_attrs.fileInputs:
                    fi_name = getattr(fi_def, "name", "")
                    if fi_name in common_input_names:
                        main_input_target_path = getattr(fi_def, "targetPath", None)
                        main_input_automount = getattr(fi_def, "autoMountLocal", True)
                        actual_input_param_name = fi_name
                        found_input_def = True
                        logger.debug(
                            f"Auto-detected input parameter: '{actual_input_param_name}' (provided: '{input_dir_param_name}')"
                        )
                        break

                # If still not found, use the first fileInput as fallback
                if not found_input_def and job_attrs.fileInputs:
                    fi_def = job_attrs.fileInputs[0]
                    main_input_target_path = getattr(fi_def, "targetPath", None)
                    main_input_automount = getattr(fi_def, "autoMountLocal", True)
                    actual_input_param_name = getattr(fi_def, "name", "")
                    found_input_def = True
                    logger.debug(
                        f"Using first available fileInput: '{actual_input_param_name}' (no match found for '{input_dir_param_name}')"
                    )

        if not found_input_def:
            logger.warning(
                f"Warning: No fileInputs found in app definition. Using provided name '{input_dir_param_name}'"
            )

        main_input_dict = {
            "name": actual_input_param_name,  # Use the detected/matched parameter name
            "sourceUrl": input_dir_uri,
            "autoMountLocal": main_input_automount,
        }
        if (
            main_input_target_path
        ):  # Add targetPath only if the app definition provided one for this input
            main_input_dict["targetPath"] = main_input_target_path
        job_req["fileInputs"].append(main_input_dict)

        if extra_file_inputs:
            job_req["fileInputs"].extend(extra_file_inputs)

        # --- Handle script parameter placement ---
        script_param_added = False
        if script_filename is not None:  # Only process if a script filename is provided
            # Try to place in appArgs
            if hasattr(param_set_def, "appArgs") and param_set_def.appArgs:
                for arg_def in param_set_def.appArgs:
                    arg_name = getattr(arg_def, "name", "")
                    if arg_name in script_param_names:
                        logger.debug(
                            f"Placing script '{script_filename}' in appArgs: '{arg_name}'"
                        )
                        job_req["parameterSet"]["appArgs"].append(
                            {"name": arg_name, "arg": script_filename}
                        )
                        script_param_added = True
                        break

            # If not placed in appArgs, try envVariables
            if (
                not script_param_added
                and hasattr(param_set_def, "envVariables")
                and param_set_def.envVariables
            ):
                for var_def in param_set_def.envVariables:
                    var_key = getattr(var_def, "key", "")
                    if var_key in script_param_names:
                        logger.debug(
                            f"Placing script '{script_filename}' in envVariables: '{var_key}'"
                        )
                        job_req["parameterSet"]["envVariables"].append(
                            {"key": var_key, "value": script_filename}
                        )
                        script_param_added = True
                        break

            if not script_param_added:
                # If script_filename was provided but could not be placed.
                app_args_details = getattr(param_set_def, "appArgs", [])
                env_vars_details = getattr(param_set_def, "envVariables", [])
                defined_app_arg_names = [
                    getattr(a, "name", None) for a in app_args_details
                ]
                defined_env_var_keys = [
                    getattr(e, "key", None) for e in env_vars_details
                ]
                raise ValueError(
                    f"script_filename '{script_filename}' was provided, but no matching parameter "
                    f"(expected names/keys from script_param_names: {script_param_names}) was found "
                    f"in the app's defined parameterSet. "
                    f"App's defined appArgs names: {defined_app_arg_names}. "
                    f"App's defined envVariables keys: {defined_env_var_keys}."
                )
        else:
            logger.debug(
                "script_filename is None, skipping script parameter placement."
            )

        # --- Auto-detect and add required parameters from app definition ---
        # Process appArgs first - add all required appArgs that aren't provided by user
        if hasattr(param_set_def, "appArgs") and param_set_def.appArgs:
            for app_arg_def in param_set_def.appArgs:
                arg_name = getattr(app_arg_def, "name", "")
                input_mode = getattr(app_arg_def, "inputMode", "")
                default_value = getattr(app_arg_def, "arg", "")

                # Skip if this is the script parameter (already handled above)
                if script_filename and arg_name in script_param_names:
                    continue

                # Check if this arg is required and not already provided
                if input_mode == "REQUIRED" and arg_name:
                    # Check if user already provided this arg
                    user_provided = False
                    if extra_app_args:
                        for user_arg in extra_app_args:
                            if user_arg.get("name") == arg_name:
                                user_provided = True
                                break

                    # Also check if already added to job_req
                    already_added = False
                    for existing_arg in job_req["parameterSet"]["appArgs"]:
                        if existing_arg.get("name") == arg_name:
                            already_added = True
                            break

                    if not user_provided and not already_added:
                        if default_value:
                            logger.debug(
                                f"Auto-adding required appArg '{arg_name}' with default: '{default_value}'"
                            )
                            job_req["parameterSet"]["appArgs"].append(
                                {"name": arg_name, "arg": default_value}
                            )
                        else:
                            logger.warning(
                                f"Warning: Required appArg '{arg_name}' has no default value."
                            )

        # Process envVariables - add all required envVariables that aren't provided by user
        if hasattr(param_set_def, "envVariables") and param_set_def.envVariables:
            for env_var_def in param_set_def.envVariables:
                var_key = getattr(env_var_def, "key", "")
                input_mode = getattr(env_var_def, "inputMode", "")
                default_value = getattr(env_var_def, "value", "")
                enum_values = getattr(env_var_def, "enum_values", None)

                # Skip if this is the script parameter (already handled above)
                if script_filename and var_key in script_param_names:
                    continue

                # Check if this variable is required and not already provided by user
                if input_mode == "REQUIRED" and var_key:
                    # Check if user already provided this variable
                    user_provided = False
                    if extra_env_vars:
                        for user_var in extra_env_vars:
                            if user_var.get("key") == var_key:
                                user_provided = True
                                break

                    # Also check if already added to job_req
                    already_added = False
                    for existing_var in job_req["parameterSet"]["envVariables"]:
                        if existing_var.get("key") == var_key:
                            already_added = True
                            break

                    if not user_provided and not already_added:
                        # Use default value if available
                        value_to_use = default_value

                        # If no default but has enum values, use the first one
                        if (
                            not value_to_use
                            and enum_values
                            and isinstance(enum_values, dict)
                        ):
                            value_to_use = list(enum_values.keys())[0]
                            logger.debug(
                                f"Auto-setting required env var '{var_key}' to first available option: '{value_to_use}'"
                            )
                        elif value_to_use:
                            logger.debug(
                                f"Auto-setting required env var '{var_key}' to default: '{value_to_use}'"
                            )
                        else:
                            logger.warning(
                                f"Warning: Required env var '{var_key}' has no default value."
                            )
                            continue

                        # Add to job request
                        job_req["parameterSet"]["envVariables"].append(
                            {"key": var_key, "value": value_to_use}
                        )

        # --- Handle extra parameters ---
        if extra_app_args:
            job_req["parameterSet"]["appArgs"].extend(extra_app_args)
        if extra_env_vars:  # For OpenFOAM, parameters like solver, mesh, decomp go here
            job_req["parameterSet"]["envVariables"].extend(extra_env_vars)

        # --- Handle scheduler options and allocation ---
        fixed_sched_opt_names = []
        if (
            hasattr(param_set_def, "schedulerOptions")
            and param_set_def.schedulerOptions
        ):
            for sched_opt_def in param_set_def.schedulerOptions:
                # Check if inputMode is FIXED for this specific option definition
                if getattr(sched_opt_def, "inputMode", None) == "FIXED" and hasattr(
                    sched_opt_def, "name"
                ):
                    fixed_sched_opt_names.append(getattr(sched_opt_def, "name"))

        if allocation:
            # Check if the app itself defines an allocation parameter that is FIXED
            allocation_is_fixed_by_app = False
            if (
                hasattr(param_set_def, "schedulerOptions")
                and param_set_def.schedulerOptions
            ):
                for sched_opt_def in param_set_def.schedulerOptions:
                    # Assuming allocation is identified by allocation_param_name
                    if (
                        getattr(sched_opt_def, "name", "") == allocation_param_name
                        and getattr(sched_opt_def, "inputMode", None) == "FIXED"
                    ):
                        allocation_is_fixed_by_app = True
                        logger.warning(
                            f"Warning: App definition marks '{allocation_param_name}' as FIXED with value '{getattr(sched_opt_def, 'arg', '')}'. "
                            f"User-provided allocation '{allocation}' will be ignored."
                        )
                        break

            if not allocation_is_fixed_by_app:
                # If user provides an allocation and it's not fixed by the app, add/override it.
                # Remove any existing scheduler option with the same name before adding the new one.
                job_req["parameterSet"]["schedulerOptions"] = [
                    opt
                    for opt in job_req["parameterSet"]["schedulerOptions"]
                    if getattr(opt, "name", opt.get("name"))
                    != allocation_param_name  # Handle both Tapis objects and dicts
                ]
                logger.debug(f"Adding/Updating TACC allocation: {allocation}")
                job_req["parameterSet"]["schedulerOptions"].append(
                    {"name": allocation_param_name, "arg": f"-A {allocation}"}
                )

        if extra_scheduler_options:
            for extra_opt in extra_scheduler_options:
                opt_name = extra_opt.get("name")
                if opt_name and opt_name in fixed_sched_opt_names:
                    logger.warning(
                        f"Warning: Skipping user-provided scheduler option '{opt_name}' because it is marked as FIXED in the app definition."
                    )
                else:
                    # Avoid duplicates if user tries to override allocation via extra_scheduler_options
                    if opt_name == allocation_param_name and allocation:
                        logger.debug(
                            f"Note: Allocation '{allocation}' is already being handled. Skipping duplicate allocation from extra_scheduler_options."
                        )
                        continue
                    job_req["parameterSet"]["schedulerOptions"].append(extra_opt)

        # --- Clean up empty parameterSet sections ---
        if not job_req["parameterSet"]["appArgs"]:
            del job_req["parameterSet"]["appArgs"]
        if not job_req["parameterSet"]["envVariables"]:
            del job_req["parameterSet"]["envVariables"]
        if not job_req["parameterSet"]["schedulerOptions"]:
            del job_req["parameterSet"]["schedulerOptions"]
        if not job_req["parameterSet"]:
            del job_req["parameterSet"]

        final_job_req = {k: v for k, v in job_req.items() if v is not None}

        # Apply app-profile adjustments for apps whose contract is not
        # declared in the app definition (e.g. SimCenter apps).
        profile = profiles.find(app_details.id)
        if profile is not None:
            logger.debug(f"Applying '{profile.name}' app profile adjustments.")
            final_job_req = profile.finalize_job_request(final_job_req)

        logger.debug("Job request dictionary generated successfully.")
        return final_job_req

    except (AppDiscoveryError, ValueError) as e:
        logger.error(f"ERROR: Failed to generate job request: {e}")
        raise
    except Exception as e:
        logger.error(f"ERROR: Unexpected error generating job request: {e}")
        raise JobSubmissionError(f"Unexpected error generating job request: {e}") from e


# --- submit_job_request function ---
def prepare_job_inputs(app_id: str, input_dir: str, **options: Any) -> Dict[str, Any]:
    """Prepare a local input directory for an app before staging.

    Dispatches to the app's profile (see :mod:`dapi.profiles`) when one is
    registered. For apps without a profile this is a no-op beyond checking
    that the directory exists — most apps need no input preparation.

    For SimCenter apps (``simcenter-*``) this rewrites the workflow JSON's
    ``remoteAppDir``/``remoteAppWorkingDir`` to the backend installation on
    the execution system, and by default bundles the inputs into a single
    ``tmpSimCenter.zip`` (unpacked natively by the app wrapper) so staging
    transfers one file instead of many. Stage the returned ``staged_dir``.

    Args:
        app_id (str): The Tapis app id the inputs are being prepared for.
        input_dir (str): Local path to the job input directory.
        **options: Profile-specific options (e.g. ``backend_dir``,
            ``input_filename``, ``bundle=False`` for SimCenter apps).

    Returns:
        Dict[str, Any]: Summary of the preparation performed. Always
            includes ``staged_dir`` — the directory callers should stage.

    Raises:
        ValueError: If input_dir does not exist, or a profile rejects the
            options.

    Example:
        >>> ds.jobs.prepare_inputs("simcenter-uq-stampede3", "./DS_input")
        >>> ds.jobs.prepare_inputs("opensees-mp-s3", "./input")  # no-op
    """
    if not os.path.isdir(input_dir):
        raise ValueError(f"Input directory '{input_dir}' does not exist.")
    profile = profiles.find(app_id)
    if profile is None:
        logger.debug(f"App '{app_id}' requires no input preparation.")
        return {
            "app_id": app_id,
            "input_dir": input_dir,
            "prepared": False,
            "staged_dir": input_dir,
        }
    logger.debug(f"Preparing inputs with '{profile.name}' app profile.")
    return profile.prepare_inputs(input_dir, app_id=app_id, **options)


def submit_job_request(
    tapis_client: Tapis, job_request: Dict[str, Any]
) -> "SubmittedJob":
    """Submit a pre-generated job request dictionary to Tapis.

    Takes a complete job request dictionary (typically generated by generate_job_request)
    and submits it to the Tapis jobs service for execution. Prints the job request
    details before submission for debugging purposes.

    Args:
        tapis_client (Tapis): Authenticated Tapis client instance.
        job_request (Dict[str, Any]): Complete job request dictionary containing
            all necessary job parameters, file inputs, and configuration.

    Returns:
        SubmittedJob: A SubmittedJob object for monitoring and managing the submitted job.

    Raises:
        ValueError: If job_request is not a dictionary.
        JobSubmissionError: If the Tapis job submission fails, with additional context
            from the HTTP request and response when available.

    Example:
        >>> job_request = generate_job_request(...)
        >>> submitted_job = submit_job_request(client, job_request)

        --- Submitting Tapis Job Request ---
        {
          "name": "matlab-r2023a-20231201_143022",
          "appId": "matlab-r2023a",
          ...
        }
        ------------------------------------
        Job submitted successfully. UUID: 12345678-1234-1234-1234-123456789abc
    """
    if not isinstance(job_request, dict):
        raise ValueError("Input 'job_request' must be a dictionary.")
    logger.debug("\n--- Submitting Tapis Job Request ---")
    logger.debug(json.dumps(job_request, indent=2, default=str))
    logger.debug("------------------------------------")
    try:
        submitted = tapis_client.jobs.submitJob(**job_request)
        logger.info(f"Job submitted successfully. UUID: {submitted.uuid}")
        return SubmittedJob(tapis_client, submitted.uuid)
    except BaseTapyException as e:
        logger.error(f"ERROR: Tapis job submission API call failed: {e}")
        raise JobSubmissionError(
            f"Tapis job submission failed: {e}",
            request=getattr(e, "request", None),
            response=getattr(e, "response", None),
        ) from e
    except Exception as e:
        logger.error(f"ERROR: Unexpected error during job submission: {e}")
        raise JobSubmissionError(f"Unexpected error during job submission: {e}") from e


# --- SubmittedJob Class ---
class SubmittedJob:
    """Represents a submitted Tapis job with methods for monitoring and management.

    This class provides a high-level interface for interacting with Tapis jobs,
    including status monitoring, output retrieval, job cancellation, and runtime
    analysis. It caches job details and status to minimize API calls.

    Attributes:
        uuid (str): The unique identifier of the Tapis job.
        TERMINAL_STATES (List[str]): List of job states that indicate completion.

    Example:
        >>> job = SubmittedJob(client, "12345678-1234-1234-1234-123456789abc")
        >>> status = job.status
        >>> if status in job.TERMINAL_STATES:
        ...     print("Job completed")
        >>> final_status = job.monitor(timeout_minutes=60)
    """

    TERMINAL_STATES = TAPIS_TERMINAL_STATES  # Use module-level constant

    def __init__(self, tapis_client: Tapis, job_uuid: str):
        """Initialize a SubmittedJob instance for an existing Tapis job.

        Args:
            tapis_client (Tapis): Authenticated Tapis client instance.
            job_uuid (str): The UUID of an existing Tapis job.

        Raises:
            TypeError: If tapis_client is not a Tapis instance.
            ValueError: If job_uuid is empty or not a string.
        """
        if not isinstance(tapis_client, Tapis):
            raise TypeError("tapis_client must be an instance of tapipy.Tapis")
        if not job_uuid or not isinstance(job_uuid, str):
            raise ValueError("job_uuid must be a non-empty string.")
        self._tapis = tapis_client
        self.uuid = job_uuid
        self._last_status: Optional[str] = None
        self._job_details: Optional[Tapis] = None

    def _get_details(self, force_refresh: bool = False) -> Tapis:
        """Fetch and cache job details from Tapis.

        Args:
            force_refresh (bool, optional): If True, forces a fresh API call
                even if details are already cached. Defaults to False.

        Returns:
            Tapis: Complete job details object from Tapis API.

        Raises:
            JobMonitorError: If job details cannot be retrieved from Tapis.
        """
        if not self._job_details or force_refresh:
            try:
                self._job_details = self._tapis.jobs.getJob(jobUuid=self.uuid)
                self._last_status = self._job_details.status
            except BaseTapyException as e:
                raise JobMonitorError(
                    f"Failed to get details for job {self.uuid}: {e}"
                ) from e
        return self._job_details

    @property
    def details(self) -> Tapis:
        """Get cached job details, fetching from Tapis if not already cached.

        Returns:
            Tapis: Complete job details object containing all job metadata,
                configuration, and current state information.
        """
        return self._get_details()

    @property
    def status(self) -> str:
        """Get the current job status, using cached value when appropriate.

        For terminal states, returns the cached status without making an API call.
        For non-terminal states, may fetch fresh status depending on cache state.

        Returns:
            str: Current job status (e.g., "QUEUED", "RUNNING", "FINISHED", "FAILED").
                Returns STATUS_UNKNOWN if status cannot be determined.
        """
        try:
            if self._last_status and self._last_status not in self.TERMINAL_STATES:
                return self.get_status(force_refresh=False)
            elif self._last_status:
                return self._last_status
            else:
                return self.get_status(force_refresh=True)
        except JobMonitorError:
            return STATUS_UNKNOWN

    def get_status(self, force_refresh: bool = True) -> str:
        """Get the current job status from Tapis API.

        Args:
            force_refresh (bool, optional): If True, always makes a fresh API call.
                If False, may return cached status. Defaults to True.

        Returns:
            str: Current job status from Tapis API.

        Raises:
            JobMonitorError: If status cannot be retrieved from Tapis.
        """
        if not force_refresh and self._last_status:
            return self._last_status
        try:
            status_obj = self._tapis.jobs.getJobStatus(jobUuid=self.uuid)
            new_status = status_obj.status
            if new_status != self._last_status:
                self._last_status = new_status
            if self._job_details and self._job_details.status != self._last_status:
                self._job_details = None
            return self._last_status
        except BaseTapyException as e:
            raise JobMonitorError(
                f"Failed to get status for job {self.uuid}: {e}"
            ) from e

    @property
    def last_message(self) -> Optional[str]:
        """Get the last status message recorded for the job.

        Retrieves the most recent status message from the job details, which
        typically contains information about the current job state or any
        errors that have occurred.

        Returns:
            str or None: The last status message if available and non-empty,
                otherwise None. Empty strings are treated as None.

        Note:
            Returns None if job details cannot be retrieved or if no message
            is available. Does not raise exceptions for retrieval failures.
        """
        try:
            details = self.details  # Ensures job details are loaded
            message = getattr(details, "lastMessage", None)
            if message:
                # Sometimes messages might be empty strings, treat as None for consistency
                return str(message).strip() if str(message).strip() else None
            return None
        except JobMonitorError as e:
            logger.debug(
                f"Could not retrieve job details to get last_message for job {self.uuid}: {e}"
            )
            return None
        except Exception as e:
            logger.debug(
                f"An unexpected error occurred while fetching last_message for job {self.uuid}: {e}"
            )
            return None

    def monitor(self, interval: int = 15, timeout_minutes: Optional[int] = None) -> str:
        """Monitor job status with progress bars until completion or timeout.

        Continuously monitors the job status using tqdm progress bars to show
        progress through different job phases (waiting, running). Handles
        interruptions and errors gracefully.

        Args:
            interval (int, optional): Status check interval in seconds. Defaults to 15.
            timeout_minutes (int, optional): Maximum monitoring time in minutes.
                If None, uses the job's maxMinutes from its configuration.
                Use -1 or 0 for unlimited monitoring. Defaults to None.

        Returns:
            str: Final job status. Can be a standard Tapis status ("FINISHED", "FAILED",
                etc.) or a special monitoring status:
                - STATUS_TIMEOUT: Monitoring timed out
                - STATUS_INTERRUPTED: User interrupted monitoring (Ctrl+C)
                - STATUS_MONITOR_ERROR: Error occurred during monitoring

        Example:
            >>> job = SubmittedJob(client, job_uuid)
            >>> final_status = job.monitor(interval=30, timeout_minutes=120)
            Monitoring Job: 12345678-1234-1234-1234-123456789abc
            Waiting for job to start: 100%|████████| 12 checks
            Monitoring job: 100%|████████████| 45/45 checks
                Status: FINISHED
            >>> if final_status == "FINISHED":
            ...     print("Job completed successfully!")
        """
        previous_status = None
        current_status = STATUS_UNKNOWN
        start_time = time.time()
        effective_timeout_minutes = -1
        timeout_seconds = float("inf")
        max_iterations = float("inf")
        pbar_waiting = None
        pbar_monitoring = None

        logger.info(f"\nMonitoring Job: {self.uuid}")  # Print Job ID once at the start

        try:
            # Fetch initial details
            details = self._get_details(force_refresh=True)
            current_status = details.status
            previous_status = current_status
            effective_timeout_minutes = (
                timeout_minutes if timeout_minutes is not None else details.maxMinutes
            )

            if effective_timeout_minutes <= 0:
                logger.debug(
                    f"Job has maxMinutes <= 0 ({details.maxMinutes}). Monitoring indefinitely or until terminal state."
                )
                timeout_seconds = float("inf")
                max_iterations = float("inf")
            else:
                timeout_seconds = effective_timeout_minutes * 60
                max_iterations = (
                    int(timeout_seconds // interval) if interval > 0 else float("inf")
                )

            waiting_states = [
                "PENDING",
                "PROCESSING_INPUTS",
                "STAGING_INPUTS",
                "STAGING_JOB",
                "SUBMITTING_JOB",
                "QUEUED",
                # Tapis pauses a job on transient trouble (a slow transfer,
                # a busy host) and resumes it; still pre-run, keep waiting.
                "BLOCKED",
            ]
            running_states = [
                "RUNNING",
                "ARCHIVING",
            ]  # Treat ARCHIVING as part of the active monitoring phase

            # --- Waiting Phase ---
            if current_status in waiting_states:
                pbar_waiting = tqdm(
                    desc="Waiting for job to start",
                    dynamic_ncols=True,
                    unit=" checks",
                    leave=False,
                )  # leave=False hides bar on completion
                while current_status in waiting_states:
                    pbar_waiting.set_postfix_str(
                        f"Status: {current_status}", refresh=True
                    )
                    time.sleep(interval)
                    try:
                        current_status = self.get_status(force_refresh=True)
                        self._poll_failures = 0
                    except JobMonitorError as e:
                        # A dropped request must not kill a long poll; the
                        # job keeps running, so retry until a bound.
                        poll_failures = getattr(self, "_poll_failures", 0) + 1
                        self._poll_failures = poll_failures
                        if poll_failures >= 20:
                            raise
                        logger.debug(f"Status poll failed ({e}); retrying")
                        continue
                    pbar_waiting.update(1)
                    if time.time() - start_time > timeout_seconds:
                        tqdm.write(
                            f"\nWarning: Monitoring timeout ({effective_timeout_minutes} mins) reached while waiting."
                        )
                        return STATUS_TIMEOUT
                    if current_status in self.TERMINAL_STATES:
                        pbar_waiting.set_postfix_str(
                            f"Status: {current_status}", refresh=True
                        )
                        tqdm.write(
                            f"\nJob reached terminal state while waiting: {current_status}"
                        )
                        return current_status  # Return actual terminal status
                pbar_waiting.close()
                pbar_waiting = None

            # --- Monitoring Phase ---
            if current_status in running_states:
                total_iterations = (
                    max_iterations if max_iterations != float("inf") else None
                )
                pbar_monitoring = tqdm(
                    total=total_iterations,
                    desc="Monitoring job",
                    dynamic_ncols=True,
                    unit=" checks",
                    leave=True,
                )  # leave=True keeps bar after completion
                iteration_count = 0
                # Initial status print for this phase
                tqdm.write(f"\tStatus: {current_status}")
                previous_status = current_status

                while current_status in running_states:
                    # Update description only if status changes within this phase (less noisy)
                    if current_status != previous_status:
                        pbar_monitoring.set_description(
                            f"Monitoring job (Status: {current_status})"
                        )
                        tqdm.write(f"\tStatus: {current_status}")
                        previous_status = current_status

                    pbar_monitoring.update(1)
                    iteration_count += 1

                    if (
                        max_iterations != float("inf")
                        and iteration_count >= max_iterations
                    ):
                        tqdm.write(
                            f"\nWarning: Monitoring timeout ({effective_timeout_minutes} mins) reached."
                        )
                        return STATUS_TIMEOUT

                    time.sleep(interval)
                    try:
                        current_status = self.get_status(force_refresh=True)
                        self._poll_failures = 0
                    except JobMonitorError as e:
                        poll_failures = getattr(self, "_poll_failures", 0) + 1
                        self._poll_failures = poll_failures
                        if poll_failures >= 20:
                            raise
                        logger.debug(f"Status poll failed ({e}); retrying")
                        continue

                    if current_status in self.TERMINAL_STATES:
                        tqdm.write(f"\tStatus: {current_status}")  # Write final status
                        if total_iterations:
                            pbar_monitoring.n = total_iterations
                            pbar_monitoring.refresh()
                        return current_status  # Return actual terminal status
                pbar_monitoring.close()
                pbar_monitoring = None

            # --- Handle Other Cases ---
            elif current_status in self.TERMINAL_STATES:
                logger.debug(f"Job already in terminal state: {current_status}")
                return current_status
            else:
                logger.debug(
                    f"Job in unexpected initial state '{current_status}'. Monitoring stopped."
                )
                return current_status

            return current_status  # Should be a terminal state if loops finished

        except KeyboardInterrupt:
            logger.debug("\nMonitoring interrupted by user.")
            return STATUS_INTERRUPTED
        except JobMonitorError as e:
            logger.debug(f"\nError during monitoring: {e}")
            return STATUS_MONITOR_ERROR
        except Exception as e:
            logger.debug(f"\nUnexpected error during monitoring: {e}")
            return STATUS_MONITOR_ERROR
        finally:
            # Safely close progress bars
            if pbar_waiting is not None:
                try:
                    pbar_waiting.close()
                except Exception:
                    pass
            if pbar_monitoring is not None:
                try:
                    pbar_monitoring.close()
                except Exception:
                    pass

    def print_runtime_summary(self, verbose: bool = False):
        """Print a summary of job runtime phases and total execution time.

        Analyzes the job's execution history to show time spent in different
        phases (queued, running) and calculates the total runtime from submission
        to completion.

        Args:
            verbose (bool, optional): If True, prints detailed job history events
                in addition to the runtime summary. Defaults to False.

        Example:
            >>> job.print_runtime_summary()

            Runtime Summary
            ---------------
            QUEUED  time: 00:05:30
            RUNNING time: 01:23:45
            TOTAL   time: 01:29:15
            ---------------

            >>> job.print_runtime_summary(verbose=True)

            Detailed Job History:
            Event: JOB_NEW_STATUS, Detail: PENDING, Time: 2023-12-01T14:30:22.123456Z
            Event: JOB_NEW_STATUS, Detail: QUEUED, Time: 2023-12-01T14:30:25.234567Z
            ...

            Summary:
            QUEUED  time: 00:05:30
            RUNNING time: 01:23:45
            TOTAL   time: 01:29:15
            ---------------
        """
        from datetime import datetime

        t = self._tapis

        print("\nRuntime Summary")
        print("---------------")
        hist = t.jobs.getJobHistory(jobUuid=self.uuid)

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

    # --- Other SubmittedJob methods (archive_uri, list_outputs, etc.) ---
    # (No changes needed in these methods from the previous correct version)
    @property
    def archive_uri(self) -> Optional[str]:
        """Get the Tapis URI of the job's archive directory.

        Returns the URI where job outputs are stored after completion.
        The archive directory contains all job outputs, logs, and metadata.

        Returns:
            str or None: Tapis URI of the archive directory if available,
                otherwise None if archive information is not set.

        Example:
            >>> uri = job.archive_uri
            >>> if uri:
            ...     print(f"Job outputs at: {uri}")
            ...     files = client.files.list(uri)
        """
        details = self._get_details()
        if details.archiveSystemId and details.archiveSystemDir:
            archive_path = details.archiveSystemDir.lstrip("/")
            return f"tapis://{details.archiveSystemId}/{archive_path}"
        return None

    def list_outputs(
        self, path: str = "/", limit: int = 100, offset: int = 0
    ) -> List[Tapis]:
        """List files and directories in the job's archive directory.

        Args:
            path (str, optional): Relative path within the job archive to list.
                Defaults to "/" (archive root).
            limit (int, optional): Maximum number of items to return. Defaults to 100.
            offset (int, optional): Number of items to skip for pagination. Defaults to 0.

        Returns:
            List[Tapis]: List of file and directory objects in the specified path.

        Raises:
            FileOperationError: If archive information is not available, the path
                cannot be accessed, or listing fails.

        Example:
            >>> outputs = job.list_outputs()
            >>> for item in outputs:
            ...     print(f"{item.name} ({item.type})")
            tapisjob.out (file)
            tapisjob.err (file)
            results/ (dir)

            >>> results = job.list_outputs(path="results/")
        """
        details = self._get_details()
        if not details.archiveSystemId or not details.archiveSystemDir:
            raise FileOperationError(
                f"Job {self.uuid} archive system ID or directory not available."
            )
        full_archive_path = os.path.join(details.archiveSystemDir, path.lstrip("/"))
        full_archive_path = os.path.normpath(full_archive_path).lstrip("/")
        try:
            archive_base_uri = f"tapis://{details.archiveSystemId}/{full_archive_path}"
            from .files import list_files

            return list_files(self._tapis, archive_base_uri, limit=limit, offset=offset)
        except BaseTapyException as e:
            raise FileOperationError(
                f"Failed list job outputs for {self.uuid} at path '{path}': {e}"
            ) from e
        except Exception as e:
            raise FileOperationError(
                f"Unexpected error listing job outputs for {self.uuid}: {e}"
            ) from e

    def download_output(self, remote_path: str, local_target: str):
        """Download a specific file from the job's archive directory.

        Args:
            remote_path (str): Relative path to the file within the job archive.
            local_target (str): Local filesystem path where the file should be saved.

        Raises:
            FileOperationError: If archive information is not available or download fails.

        Example:
            >>> job.download_output("tapisjob.out", "/local/job_output.txt")
            >>> job.download_output("results/data.txt", "/local/results/data.txt")
        """
        details = self._get_details()
        if not details.archiveSystemId or not details.archiveSystemDir:
            raise FileOperationError(
                f"Job {self.uuid} archive system ID or directory not available."
            )
        full_archive_path = os.path.join(
            details.archiveSystemDir, remote_path.lstrip("/")
        )
        full_archive_path = os.path.normpath(full_archive_path).lstrip("/")
        remote_uri = f"tapis://{details.archiveSystemId}/{full_archive_path}"
        try:
            from .files import download_file

            download_file(self._tapis, remote_uri, local_target)
        except Exception as e:
            raise FileOperationError(
                f"Failed to download output '{remote_path}' for job {self.uuid}: {e}"
            ) from e

    def get_output_content(
        self,
        output_filename: str,
        max_lines: Optional[int] = None,
        missing_ok: bool = True,
    ) -> Optional[str]:
        """Retrieve the content of a specific output file from the job's archive.

        Fetches and returns the content of a file from the job's archive directory
        as a string. Useful for examining log files, output files, and error files.

        Args:
            output_filename (str): Name of the file in the job's archive root
                (e.g., "tapisjob.out", "tapisjob.err", "results.txt").
            max_lines (int, optional): If specified, returns only the last N lines
                of the file. Useful for large log files. Defaults to None (full file).
            missing_ok (bool, optional): If True and the file is not found, returns None.
                If False and not found, raises FileOperationError. Defaults to True.

        Returns:
            str or None: Content of the file as a string, or None if the file
                is not found and missing_ok=True.

        Raises:
            FileOperationError: If the job archive is not available, the file is not
                found (and missing_ok=False), or if there's an error fetching the file.

        Example:
            >>> # Get job output log
            >>> output = job.get_output_content("tapisjob.out")
            >>> if output:
            ...     print(output)

            >>> # Get last 50 lines of error log
            >>> errors = job.get_output_content("tapisjob.err", max_lines=50)

            >>> # Require file to exist (raise error if missing)
            >>> results = job.get_output_content("results.txt", missing_ok=False)
        """
        logger.debug(
            f"Attempting to fetch content of '{output_filename}' from job archive..."
        )
        details = self._get_details()  # Ensure details are loaded
        if not details.archiveSystemId or not details.archiveSystemDir:
            raise FileOperationError(
                f"Job {self.uuid} archive system ID or directory not available. Cannot fetch output."
            )

        full_archive_path = os.path.join(
            details.archiveSystemDir, output_filename.lstrip("/")
        )
        full_archive_path = os.path.normpath(full_archive_path).lstrip("/")

        try:
            # self._tapis.files.getContents() is expected to return the full file content as bytes
            # when the response is not JSON. The stream=True parameter is for the API endpoint.
            content_bytes = self._tapis.files.getContents(
                systemId=details.archiveSystemId,
                path=full_archive_path,
                stream=True,  # Good to keep, as it's a hint for the server
            )

            # Verify that we indeed received bytes
            if not isinstance(content_bytes, bytes):
                raise FileOperationError(
                    f"Tapis API returned unexpected type for file content of '{output_filename}': {type(content_bytes)}. Expected bytes."
                )

            content_str = content_bytes.decode(
                "utf-8", errors="replace"
            )  # Decode to string

            if max_lines is not None and max_lines > 0:
                lines = content_str.splitlines()
                if len(lines) > max_lines:
                    # Slice to get the last max_lines
                    content_str = "\n".join(lines[-max_lines:])
                    logger.debug(
                        f"Returning last {max_lines} lines of '{output_filename}'."
                    )
                else:
                    logger.debug(
                        f"File '{output_filename}' has {len(lines)} lines (less than/equal to max_lines={max_lines}). Returning full content."
                    )
            else:
                logger.debug(f"Returning full content of '{output_filename}'.")
            return content_str

        except BaseTapyException as e:
            if hasattr(e, "response") and e.response and e.response.status_code == 404:
                if missing_ok:
                    logger.debug(
                        f"Output file '{output_filename}' not found in archive (missing_ok=True). Path: {details.archiveSystemId}/{full_archive_path}"
                    )
                    return None
                else:
                    raise FileOperationError(
                        f"Output file '{output_filename}' not found in job archive "
                        f"at system '{details.archiveSystemId}', path '{full_archive_path}'."
                    ) from e
            else:
                raise FileOperationError(
                    f"Tapis error fetching output file '{output_filename}' for job {self.uuid} (Path: {details.archiveSystemId}/{full_archive_path}): {e}"
                ) from e
        except FileOperationError:  # Re-raise FileOperationErrors from above
            raise
        except Exception as e:  # Catch other unexpected errors
            raise FileOperationError(
                f"Unexpected error fetching content of '{output_filename}' for job {self.uuid} (Path: {details.archiveSystemId}/{full_archive_path}): {e}"
            ) from e

    def get_results(self, **options: Any) -> Any:
        """Fetch and parse this job's results using its app profile.

        Dispatches to the profile registered for this job's app (see
        :mod:`dapi.profiles`). For SimCenter jobs this downloads
        ``results.zip`` from the archive in memory and returns a
        :class:`dapi.simcenter.SimCenterResults` with the ``dakotaTab.out``
        sample table as a DataFrame and parsed Sobol sensitivity indices.

        Args:
            **options: Profile-specific options (e.g. ``results_filename``
                for SimCenter jobs).

        Returns:
            Parsed results object; type depends on the app profile.

        Raises:
            FileOperationError: If no results parser is registered for this
                job's app, or retrieval/parsing fails.

        Example:
            >>> results = job.get_results()
            >>> results.samples.head()
            >>> results.sobol_indices
        """
        details = self._get_details()
        app_id = getattr(details, "appId", None)
        profile = profiles.find(app_id)
        if profile is None:
            raise FileOperationError(
                f"No results parser registered for app '{app_id}'. Use "
                "list_outputs(), download_output(), or get_output_content() "
                "to access the job archive directly."
            )
        try:
            return profile.parse_results(self._tapis, self, **options)
        except NotImplementedError as e:
            raise FileOperationError(str(e)) from e

    def share(
        self,
        user_id: Optional[Any] = None,
        project_id: Optional[str] = None,
        resources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Share this job (READ) with users and/or all members of a project.

        All grantees are validated before any grant is issued: usernames
        must exist in the tenant, and the project must resolve via the
        DesignSafe projects API. The job owner is excluded automatically.

        Grantees can view the job record and, depending on the granted
        resources, its history, inputs, outputs, and resubmit request.
        They can find shared jobs with ``ds.jobs.list(list_type="SHARED_JOBS")``.

        Args:
            user_id (str or List[str], optional): Username(s) to share with.
            project_id (str, optional): DesignSafe project id (e.g.,
                "PRJ-1234"); shares with every project user (PI, co-PIs,
                team members).
            resources (List[str], optional): Job resources to grant.
                Defaults to all of ``JOB_SHARE_RESOURCES``.

        Returns:
            Dict[str, Any]: Summary with ``job_uuid``, ``grantees``,
                ``resources``, and ``permission``.

        Raises:
            ValueError: If validation fails (unknown user, empty project,
                invalid resource, or no grantees).
            DapiException: If a Tapis share request fails.

        Example:
            >>> job.share(user_id="jdoe")
            >>> job.share(project_id="PRJ-1234")
            >>> job.share(user_id=["jdoe", "asmith"], resources=["JOB_OUTPUT"])
        """
        share_resources = list(resources) if resources else list(JOB_SHARE_RESOURCES)
        invalid = sorted(set(share_resources) - set(JOB_SHARE_RESOURCES))
        if invalid:
            raise ValueError(
                f"Invalid share resources {invalid}. Valid: {JOB_SHARE_RESOURCES}"
            )

        grantees = _resolve_share_grantees(self._tapis, user_id, project_id)
        for grantee in grantees:
            try:
                self._tapis.jobs.shareJob(
                    jobUuid=self.uuid,
                    grantee=grantee,
                    jobResource=share_resources,
                    jobPermission="READ",
                )
            except BaseTapyException as e:
                raise DapiException(
                    f"Failed to share job {self.uuid} with '{grantee}': {e}"
                ) from e
            logger.info(f"Shared job {self.uuid} with '{grantee}' (READ).")
        return {
            "job_uuid": self.uuid,
            "grantees": grantees,
            "resources": share_resources,
            "permission": "READ",
        }

    @property
    def shares(self) -> pd.DataFrame:
        """Current share grants on this job.

        Returns:
            pd.DataFrame: One row per (grantee, resource) grant with columns
                grantee, resource, permission, created, createdBy.

        Example:
            >>> job.shares
        """
        try:
            rows = self._tapis.jobs.getJobShare(jobUuid=self.uuid)
        except BaseTapyException as e:
            raise DapiException(
                f"Failed to list shares for job {self.uuid}: {e}"
            ) from e
        data = [
            {
                "grantee": getattr(r, "grantee", None),
                "resource": getattr(r, "jobResource", None),
                "permission": getattr(r, "jobPermission", None),
                "created": getattr(r, "created", None),
                "createdBy": getattr(r, "createdby", None),
            }
            for r in rows or []
        ]
        return pd.DataFrame(
            data, columns=["grantee", "resource", "permission", "created", "createdBy"]
        )

    def cancel(self):
        """Attempt to cancel the job execution.

        Sends a cancellation request to Tapis. Note that cancellation may not
        be immediate and depends on the job's current state and the execution system.

        Raises:
            JobMonitorError: If the cancellation request fails or encounters an error.

        Note:
            Jobs that are already in terminal states cannot be cancelled.
            The method will print the current status if cancellation is not possible.

        Example:
            >>> job.cancel()
            Attempting to cancel job 12345678-1234-1234-1234-123456789abc...
            Cancel request sent for job 12345678-1234-1234-1234-123456789abc. Status may take time to update.
        """
        logger.info(f"Attempting to cancel job {self.uuid}...")
        try:
            self._tapis.jobs.cancelJob(jobUuid=self.uuid)
            logger.debug(
                f"Cancel request sent for job {self.uuid}. Status may take time to update."
            )
            self._last_status = "CANCELLED"
            self._job_details = None
        except BaseTapyException as e:
            if hasattr(e, "response") and e.response and e.response.status_code == 400:
                logger.debug(
                    f"Could not cancel job {self.uuid}. It might already be in a terminal state. Fetching status..."
                )
                self.get_status(force_refresh=True)
                logger.debug(f"Current status: {self.status}")
            else:
                raise JobMonitorError(
                    f"Failed to send cancel request for job {self.uuid}: {e}"
                ) from e
        except Exception as e:
            raise JobMonitorError(
                f"Unexpected error cancelling job {self.uuid}: {e}"
            ) from e


# --- Standalone Helper Functions ---
def get_job_status(t: Tapis, job_uuid: str) -> str:
    """Get the current status of a job by UUID.

    Standalone convenience function that creates a temporary SubmittedJob instance
    to retrieve the current status of an existing job.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        job_uuid (str): The UUID of the job to check.

    Returns:
        str: Current job status (e.g., "QUEUED", "RUNNING", "FINISHED", "FAILED").

    Raises:
        JobMonitorError: If status retrieval fails.
        TypeError: If t is not a Tapis instance.
        ValueError: If job_uuid is empty or invalid.

    Example:
        >>> status = get_job_status(client, "12345678-1234-1234-1234-123456789abc")
        >>> print(f"Job status: {status}")
    """
    job = SubmittedJob(t, job_uuid)
    return job.get_status(force_refresh=True)


def get_runtime_summary(t: Tapis, job_uuid: str, verbose: bool = False):
    """Print a runtime summary for a job by UUID.

    Standalone convenience function that creates a temporary SubmittedJob instance
    to analyze and print the runtime summary of an existing job.

    Args:
        t (Tapis): Authenticated Tapis client instance.
        job_uuid (str): The UUID of the job to analyze.
        verbose (bool, optional): If True, prints detailed job history events
            in addition to the runtime summary. Defaults to False.

    Raises:
        JobMonitorError: If job details cannot be retrieved.
        TypeError: If t is not a Tapis instance.
        ValueError: If job_uuid is empty or invalid.

    Example:
        >>> get_runtime_summary(client, "12345678-1234-1234-1234-123456789abc")

        Runtime Summary
        ---------------
        QUEUED  time: 00:05:30
        RUNNING time: 01:23:45
        TOTAL   time: 01:29:15
        ---------------
    """
    job = SubmittedJob(t, job_uuid)
    job.print_runtime_summary(verbose=verbose)


def interpret_job_status(final_status: str, job_uuid: Optional[str] = None):
    """Print a user-friendly interpretation of a job status.

    Provides human-readable explanations for various job status values,
    including both standard Tapis states and special monitoring states.

    Args:
        final_status (str): The job status to interpret. Can be a standard Tapis
            status ("FINISHED", "FAILED", etc.) or a special monitoring status
            (STATUS_TIMEOUT, STATUS_INTERRUPTED, etc.).
        job_uuid (str, optional): The job UUID to include in the message for context.
            If None, uses generic "Job" in the message. Defaults to None.

    Example:
        >>> interpret_job_status("FINISHED", "12345678-1234-1234-1234-123456789abc")
        Job 12345678-1234-1234-1234-123456789abc completed successfully.

        >>> interpret_job_status("FAILED")
        Job failed. Check logs or job details.

        >>> interpret_job_status(STATUS_TIMEOUT, "12345678-1234-1234-1234-123456789abc")
        Job 12345678-1234-1234-1234-123456789abc monitoring timed out.
    """
    job_id_str = f"Job {job_uuid}" if job_uuid else "Job"
    if final_status == "FINISHED":
        print(f"{job_id_str} completed successfully.")
    elif final_status == "FAILED":
        print(f"{job_id_str} failed. Check logs or job details.")
    elif final_status == STATUS_TIMEOUT:
        print(f"{job_id_str} monitoring timed out.")
    elif final_status == STATUS_INTERRUPTED:
        print(f"{job_id_str} monitoring was interrupted.")
    elif final_status == STATUS_MONITOR_ERROR:
        print(f"An error occurred while monitoring {job_id_str}.")
    elif final_status == STATUS_UNKNOWN:
        print(f"Could not determine final status of {job_id_str}.")
    elif final_status in TAPIS_TERMINAL_STATES:
        print(f"{job_id_str} ended with status: {final_status}")
    else:
        print(f"{job_id_str} ended with an unexpected status: {final_status}")


def list_jobs(
    tapis_client: Tapis,
    app_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    output: str = "df",
    verbose: bool = False,
    list_type: str = "MY_JOBS",
):
    """Fetch Tapis jobs with optional filtering.

    Retrieves jobs from Tapis ordered by creation date (newest first)
    and optionally filters by app ID and/or status. Filters are applied
    client-side after fetching.

    Args:
        tapis_client: Authenticated Tapis client instance.
        app_id: Filter by application ID (e.g., "opensees-mp-s3").
        status: Filter by job status (e.g., "FINISHED", "FAILED").
            Case-insensitive.
        limit: Maximum number of jobs to fetch from Tapis. Defaults to 100.
        output: Output format. "df" returns a pandas DataFrame (default),
            "list" returns a list of dicts, "raw" returns the raw
            TapisResult objects.
        verbose: If True, prints the number of jobs found.
        list_type: Which jobs to list. "MY_JOBS" (default) lists jobs you
            own, "SHARED_JOBS" lists jobs shared with you, "ALL_JOBS" both.

    Returns:
        Depends on ``output``:
        - "df": pandas DataFrame with formatted datetime columns.
        - "list": list of dicts with job metadata.
        - "raw": list of TapisResult objects as returned by the API.

    Raises:
        JobMonitorError: If the Tapis API call fails.
        ValueError: If output format is not recognized.

    Example:
        >>> df = list_jobs(t, app_id="matlab-r2023a", status="FINISHED")
        >>> jobs = list_jobs(t, output="list")
        >>> raw = list_jobs(t, limit=10, output="raw")
    """
    if output not in ("df", "list", "raw"):
        raise ValueError(f"output must be 'df', 'list', or 'raw', got '{output}'")
    list_type = list_type.upper()
    if list_type not in ("MY_JOBS", "SHARED_JOBS", "ALL_JOBS"):
        raise ValueError(
            f"list_type must be 'MY_JOBS', 'SHARED_JOBS', or 'ALL_JOBS', got '{list_type}'"
        )

    try:
        jobs_list = tapis_client.jobs.getJobList(
            limit=limit,
            orderBy="created(desc)",
            listType=list_type,
        )
    except BaseTapyException as e:
        raise JobMonitorError(f"Failed to list jobs: {e}") from e
    except Exception as e:
        raise JobMonitorError(f"Unexpected error listing jobs: {e}") from e

    if not jobs_list:
        if verbose:
            logger.debug("Found 0 jobs.")
        if output == "raw":
            return []
        if output == "list":
            return []
        return pd.DataFrame()

    # For raw output, apply filters manually on TapisResult objects
    if output == "raw":
        results = jobs_list
        if app_id:
            results = [j for j in results if getattr(j, "appId", None) == app_id]
        if status:
            results = [
                j for j in results if getattr(j, "status", "").upper() == status.upper()
            ]
        if verbose:
            logger.debug(f"Found {len(results)} jobs.")
        return results

    # Convert TapisResult objects to dicts
    jobs_dicts = [job.__dict__ for job in jobs_list]

    # Apply client-side filters
    if app_id:
        jobs_dicts = [j for j in jobs_dicts if j.get("appId") == app_id]
    if status:
        jobs_dicts = [
            j for j in jobs_dicts if j.get("status", "").upper() == status.upper()
        ]

    if verbose:
        logger.debug(f"Found {len(jobs_dicts)} jobs.")

    if output == "list":
        return jobs_dicts

    # Build DataFrame
    df = pd.DataFrame(jobs_dicts)

    if df.empty:
        return df

    # Add formatted datetime columns
    time_cols = ["created", "ended", "remoteStarted", "lastUpdated"]
    for col in time_cols:
        if col in df.columns:
            df[f"{col}_dt"] = pd.to_datetime(df[col], utc=True, errors="coerce")
            df[f"{col}_date"] = df[f"{col}_dt"].dt.date

    # Reorder: priority columns first
    priority = [
        "name",
        "uuid",
        "status",
        "appId",
        "appVersion",
        "created_dt",
        "ended_dt",
    ]
    priority_present = [c for c in priority if c in df.columns]
    remaining = [c for c in df.columns if c not in priority_present]
    df = df[priority_present + remaining]

    df = df.reset_index(drop=True)

    return df
