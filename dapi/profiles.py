"""Application profiles: per-app adjustments dapi applies automatically.

Most Tapis apps declare their full interface (fileInputs, envVariables,
appArgs) in the app definition, and ``ds.jobs.generate`` adapts to it by
reading that metadata. Some apps do not: their contract lives in the app's
wrapper script and is invisible to Tapis metadata. An :class:`AppProfile`
encodes such a contract so the public dapi API stays app-agnostic.

Profiles are dispatched by app id at three points of the job lifecycle:

- ``ds.jobs.prepare_inputs``: local input preparation before staging,
- ``ds.jobs.generate``: finalizing the job request dictionary,
- ``SubmittedJob.get_results()``: parsing the outputs of a finished job.

Registering a profile (see :mod:`dapi.simcenter` for a real one)::

    @register
    class MyAppProfile(AppProfile):
        name = "myapp"

        @classmethod
        def matches(cls, app_id):
            return app_id.startswith("myapp-")
"""

from typing import Any, Dict, List, Optional, Type


class AppProfile:
    """Base class for application profiles.

    Subclasses override :meth:`matches` (required) and any lifecycle hooks
    they need. The defaults are no-ops: no input preparation, no job request
    changes, no results parser.
    """

    name: str = "base"

    @classmethod
    def matches(cls, app_id: str) -> bool:
        """Return True if this profile applies to the given app id."""
        return False

    @classmethod
    def prepare_inputs(
        cls, input_dir: str, app_id: str, **options: Any
    ) -> Dict[str, Any]:
        """Prepare a local input directory before staging. No-op by default.

        Args:
            input_dir (str): Local path to the job input directory.
            app_id (str): The Tapis app id being targeted.
            **options: Profile-specific options.

        Returns:
            Dict[str, Any]: Summary of what was prepared.
        """
        return {"app_id": app_id, "input_dir": input_dir, "prepared": False}

    @classmethod
    def finalize_job_request(cls, job_request: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust a generated job request. Returns it unchanged by default.

        Args:
            job_request (Dict[str, Any]): Job request from
                :func:`dapi.jobs.generate_job_request`.

        Returns:
            Dict[str, Any]: The (possibly adjusted) job request.
        """
        return job_request

    @classmethod
    def parse_results(cls, tapis_client: Any, job: Any, **options: Any) -> Any:
        """Fetch and parse the results of a finished job.

        Args:
            tapis_client: Authenticated Tapis client instance.
            job: SubmittedJob instance for the finished job.
            **options: Profile-specific options.

        Raises:
            NotImplementedError: If the profile provides no results parser.
        """
        raise NotImplementedError(
            f"App profile '{cls.name}' provides no results parser."
        )


_REGISTRY: List[Type[AppProfile]] = []


def register(profile: Type[AppProfile]) -> Type[AppProfile]:
    """Register an app profile. Usable as a class decorator."""
    if profile not in _REGISTRY:
        _REGISTRY.append(profile)
    return profile


def find(app_id: Optional[str]) -> Optional[Type[AppProfile]]:
    """Return the first registered profile matching app_id, or None."""
    if not app_id:
        return None
    for profile in _REGISTRY:
        if profile.matches(app_id):
            return profile
    return None
