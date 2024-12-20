import os
from getpass import getpass
from tapipy.tapis import Tapis
from dotenv import load_dotenv


def init():
    """
    Initialize a Tapis object with authentication.
    Tries to read credentials from environment variables first.
    If not found, prompts the user for input.

    Save the user credentials in the .env file.
    ```
    DESIGNSAFE_USERNAME=<username>
    DESIGNSAFE_PASSWORD=<password>
    ```

    Returns:
        object: The authenticated Tapis object.
    """
    base_url = "https://designsafe.tapis.io"

    # Load environment variables from .env file
    load_dotenv()

    # Try to get credentials from environment variables
    username = os.getenv("DESIGNSAFE_USERNAME")
    password = os.getenv("DESIGNSAFE_PASSWORD")

    # If environment variables are not set, prompt user for input
    if not username:
        username = input("Enter username: ")
    if not password:
        password = getpass("Enter password: ")

    # Initialize Tapis object
    t = Tapis(base_url=base_url, username=username, password=password)

    t.get_tokens()

    return t
