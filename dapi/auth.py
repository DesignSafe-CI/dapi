import os
from getpass import getpass
from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException
from dotenv import load_dotenv
from .exceptions import AuthenticationError

def init(base_url: str = "https://designsafe.tapis.io",
         username: str = None,
         password: str = None,
         env_file: str = None) -> Tapis:
    """
    Initialize and authenticate a Tapis client for DesignSafe.

    Tries credentials in this order:
    1. Explicitly passed username/password arguments.
    2. Environment variables (DESIGNSAFE_USERNAME, DESIGNSAFE_PASSWORD).
       Loads from `env_file` (e.g., '.env') if specified, otherwise checks system env.
    3. Prompts user for username/password if none found.

    Args:
        base_url: The Tapis base URL for DesignSafe.
        username: Explicit DesignSafe username.
        password: Explicit DesignSafe password.
        env_file: Path to a .env file to load credentials from.

    Returns:
        An authenticated tapipy.Tapis object.

    Raises:
        AuthenticationError: If authentication fails.
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
        except Exception: # Fallback for non-terminal environments
             final_password = input("Enter DesignSafe Password: ")


    if not final_username or not final_password:
        raise AuthenticationError("Username and password are required.")

    # Initialize Tapis object
    try:
        t = Tapis(base_url=base_url,
                  username=final_username,
                  password=final_password,
                  download_latest_specs=False) # Avoid slow spec downloads by default

        # Attempt to get tokens to verify credentials
        t.get_tokens()
        print("Authentication successful.")
        return t

    except BaseTapyException as e:
        # Catch Tapis-specific errors during init or get_tokens
        raise AuthenticationError(f"Tapis authentication failed: {e}") from e
    except Exception as e:
        # Catch other potential errors
        raise AuthenticationError(f"An unexpected error occurred during authentication: {e}") from e