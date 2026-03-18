# Auth

Authentication and credential management for DesignSafe access.

## Authentication

### `init`

```python
dapi.auth.init(
    base_url: str = "https://designsafe.tapis.io",
    username: str = None,
    password: str = None,
    env_file: str = None,
) -> Tapis
```

Initialize and authenticate a Tapis client for DesignSafe.

Creates and authenticates a Tapis client instance for interacting with DesignSafe resources. The function follows a credential resolution hierarchy and handles secure password input when needed.

**Credential Resolution Order:**

1. Explicitly passed `username`/`password` arguments
2. Environment variables (`DESIGNSAFE_USERNAME`, `DESIGNSAFE_PASSWORD`) -- loads from `env_file` if specified, otherwise checks system environment
3. Interactive prompts for missing credentials

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `base_url` | `str` | `"https://designsafe.tapis.io"` | The Tapis base URL for DesignSafe API endpoints. |
| `username` | `str` | `None` | Explicit DesignSafe username. If `None`, attempts to load from environment or prompts the user. |
| `password` | `str` | `None` | Explicit DesignSafe password. If `None`, attempts to load from environment or prompts the user securely. |
| `env_file` | `str` | `None` | Path to a `.env` file containing credentials. If `None`, attempts to load from a default `.env` file if it exists. |

**Returns:**

`Tapis` -- An authenticated `tapipy.Tapis` client object ready for API calls.

**Raises:**

- {py:class}`~dapi.exceptions.AuthenticationError` -- If authentication fails due to invalid credentials, network issues, or if required credentials cannot be obtained.

**Examples:**

```python
# Using explicit credentials
client = init(username="myuser", password="mypass")

# Using environment variables or .env file
client = init(env_file=".env")

# Interactive authentication
client = init()
# Enter DesignSafe Username: myuser
# Enter DesignSafe Password: [hidden]
```

:::{note}
The function disables automatic spec downloads for faster initialization. Password input uses `getpass` for secure entry in terminal environments.
:::
