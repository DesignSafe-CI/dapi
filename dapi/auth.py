import os
from getpass import getpass
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from dotenv import load_dotenv
from .exceptions import AuthenticationError


def init(
    base_url: str = "https://designsafe.tapis.io",
    username: str = None,
    password: str = None,
    env_file: str = None,
) -> Tapis:
    """Initialize and authenticate a Tapis client for DesignSafe.

    Creates and authenticates a Tapis client instance for interacting with
    DesignSafe resources. The function follows a credential resolution hierarchy
    and handles secure password input when needed.

    Credential Resolution Order:
        1. Explicitly passed username/password arguments
        2. Environment variables (DESIGNSAFE_USERNAME, DESIGNSAFE_PASSWORD)
           - Loads from env_file if specified, otherwise checks system environment
        3. Interactive prompts for missing credentials

    Args:
        base_url (str, optional): The Tapis base URL for DesignSafe API endpoints.
            Defaults to "https://designsafe.tapis.io".
        username (str, optional): Explicit DesignSafe username. If None, will
            attempt to load from environment or prompt user. Defaults to None.
        password (str, optional): Explicit DesignSafe password. If None, will
            attempt to load from environment or prompt user securely. Defaults to None.
        env_file (str, optional): Path to a .env file containing credentials.
            If None, attempts to load from default .env file if it exists.
            Defaults to None.

    Returns:
        Tapis: An authenticated tapipy.Tapis client object ready for API calls.

    Raises:
        AuthenticationError: If authentication fails due to invalid credentials,
            network issues, or if required credentials cannot be obtained.

    Example:
        >>> # Using explicit credentials
        >>> client = init(username="myuser", password="mypass")
        Authentication successful.

        >>> # Using environment variables or .env file
        >>> client = init(env_file=".env")
        Authentication successful.

        >>> # Interactive authentication
        >>> client = init()
        Enter DesignSafe Username: myuser
        Enter DesignSafe Password: [hidden]
        Authentication successful.

    Note:
        The function disables automatic spec downloads for faster initialization.
        Password input uses getpass for secure entry in terminal environments.
    """
    # Load environment variables if a file path is provided
    if env_file:
        load_dotenv(dotenv_path=env_file)
    else:
        # Try loading from default .env if it exists, but don't require it
        load_dotenv()

    # Determine credentials
    final_username = username or os.getenv("DESIGNSAFE_USERNAME")
    final_password = password or os.getenv("DESIGNSAFE_PASSWORD")

    # Prompt if still missing
    if not final_username:
        final_username = input("Enter DesignSafe Username: ")
    if not final_password:
        # Use getpass for secure password entry in terminals
        try:
            final_password = getpass("Enter DesignSafe Password: ")
        except (EOFError, KeyboardInterrupt):
            raise AuthenticationError("Password input cancelled.")
        except Exception:  # Fallback for non-terminal environments
            final_password = input("Enter DesignSafe Password: ")

    if not final_username or not final_password:
        raise AuthenticationError("Username and password are required.")

    # Initialize Tapis object
    try:
        t = Tapis(
            base_url=base_url,
            username=final_username,
            password=final_password,
            download_latest_specs=False,
        )  # Avoid slow spec downloads by default

        # Attempt to get tokens to verify credentials
        t.get_tokens()
        print("Authentication successful.")
        return t

    except BaseTapyException as e:
        # Catch Tapis-specific errors during init or get_tokens
        raise AuthenticationError(f"Tapis authentication failed: {e}") from e
    except Exception as e:
        # Catch other potential errors
        raise AuthenticationError(
            f"An unexpected error occurred during authentication: {e}"
        ) from e
