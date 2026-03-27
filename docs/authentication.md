# Authentication

dapi authenticates with DesignSafe via the TAPIS v3 API. Credentials are resolved in this order:

1. Explicit parameters passed to `DSClient()`
2. Environment variables (`DESIGNSAFE_USERNAME`, `DESIGNSAFE_PASSWORD`)
3. `.env` file in your project directory
4. Interactive prompts

On [DesignSafe JupyterHub](https://jupyter.designsafe-ci.org), authentication is handled automatically. The sections below are for running dapi from a laptop, CI pipeline, or other environment.

## Environment Variables

```bash
export DESIGNSAFE_USERNAME="your_username"
export DESIGNSAFE_PASSWORD="your_password"
```

```python
from dapi import DSClient

ds = DSClient()  # uses environment variables
```

To persist across sessions, add the exports to `~/.bashrc` or `~/.zshrc`.

## .env File

Create a `.env` file in your project root:

```bash
# .env file
DESIGNSAFE_USERNAME=your_username
DESIGNSAFE_PASSWORD=your_password
```

:::{warning} Security Note
Never commit `.env` files to version control. Add `.env` to your `.gitignore`.
:::

```python
from dapi import DSClient

ds = DSClient()  # loads from .env

# Or specify a custom path
ds = DSClient(env_file="path/to/custom.env")
```

## Interactive Prompts

If no credentials are found, dapi prompts for them:

```python
ds = DSClient()
# Enter DesignSafe Username: your_username
# Enter DesignSafe Password: [hidden input]
# Authentication successful.
```

## Explicit Parameters

```python
ds = DSClient(
 username="your_username",
 password="your_password"
)
```

## TMS Credentials

After authenticating, dapi needs SSH credentials on TACC execution systems to submit jobs. `DSClient()` sets these up automatically on first use. See [Systems](systems.md) for manual TMS credential management.

## Database Connections

Database connections use built-in public read-only credentials by default. No setup is required. See [Database Access](database.md) for override options.

## JWT Token Expiration

Long-running sessions may encounter token expiration:

```
UnauthorizedError: message: b'TAPIS_SECURITY_JWT_EXPIRED ...'
```

Reinitialize your client to refresh tokens:

```python
ds = DSClient()
```

## Troubleshooting

**Invalid credentials:**
```
AuthenticationError: Tapis authentication failed
```
Verify your DesignSafe username and password.

**Network issues:**
```
AuthenticationError: An unexpected error occurred during authentication
```
Check your internet connection and DesignSafe service status.

**Environment variables not detected:**
```bash
echo $DESIGNSAFE_USERNAME
echo $DESIGNSAFE_PASSWORD
```
