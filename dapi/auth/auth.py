from agavepy.agave import Agave
from collections.abc import Mapping


def init(username, password):
    """
    Initialize an Agave object with a new client and an active token.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        object: The Agave object.
    """
    # Authenticate with Agave
    ag = Agave(
        base_url="https://agave.designsafe-ci.org", username=username, password=password
    )
    # Create a new client
    new_client = ag.clients_create()
    # create a new ag object with the new client, at this point ag will have a new token
    ag = Agave(
        base_url="https://agave.designsafe-ci.org",
        username=username,
        password=password,
        api_key=new_client["api_key"],
        api_secret=new_client["api_secret"],
    )
    return ag
