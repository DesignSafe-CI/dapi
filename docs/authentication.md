# Authentication

dapi authenticates with DesignSafe via the TAPIS v3 API. Credentials are resolved in this order:

1. Explicit parameters passed to `DSClient()`
2. Environment variables (`DESIGNSAFE_USERNAME`, `DESIGNSAFE_PASSWORD`)
3. `.env` file in your project directory
4. Interactive prompts

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

## TMS Credentials (Execution System Access)

After authenticating with DesignSafe, you need TMS credentials on execution systems where you plan to submit jobs. TMS manages SSH key pairs that allow Tapis to access TACC systems (Frontera, Stampede3, Lonestar6) on your behalf.

:::{note} One-time setup
TMS credentials only need to be established once per system. After that, they persist until you revoke them.
:::

### Establish Credentials

```python
ds = DSClient()

ds.systems.establish_credentials("frontera")
ds.systems.establish_credentials("stampede3")
ds.systems.establish_credentials("ls6")
```

If credentials already exist, `establish_credentials` does nothing (idempotent). To force re-creation:

```python
ds.systems.establish_credentials("frontera", force=True)
```

### Check Credentials

```python
if ds.systems.check_credentials("frontera"):
    print("Ready to submit jobs on Frontera")
else:
    ds.systems.establish_credentials("frontera")
```

### Revoke Credentials

```python
ds.systems.revoke_credentials("frontera")
```

### Using TMS from Outside DesignSafe

TMS credentials work from any environment -- not just DesignSafe JupyterHub. As long as you can authenticate with Tapis (e.g., via `.env` file), you can manage TMS credentials from your laptop, CI/CD pipelines, or any Python script:

```python
from dapi import DSClient

ds = DSClient()
ds.systems.establish_credentials("frontera")

# Now submit jobs as usual
job_request = ds.jobs.generate(...)
job = ds.jobs.submit(job_request)
```

### Troubleshooting TMS

**Non-TMS System:**
```
CredentialError: System 'my-system' uses authentication method 'PASSWORD', not 'TMS_KEYS'.
```
TMS credential management only works for systems configured with `TMS_KEYS` authentication. TACC execution systems (frontera, stampede3, ls6) use TMS_KEYS.

**System Not Found:**
```
CredentialError: System 'nonexistent' not found.
```
Verify the system ID. Common system IDs: `frontera`, `stampede3`, `ls6`.

## Database Connections

Database connections use built-in public read-only credentials by default -- no `.env` setup is required. To override the defaults (e.g., for a private database instance), set environment variables:

```bash
# Optional: override database credentials
NGL_DB_USER=your_user
NGL_DB_PASSWORD=your_password
NGL_DB_HOST=your_host
NGL_DB_PORT=3306
```

The same pattern applies for VP (`VP_DB_*`) and Earthquake Recovery (`EQ_DB_*`) databases.

## JWT Token Expiration

Long-running sessions may encounter token expiration:

```
UnauthorizedError: message: b'TAPIS_SECURITY_JWT_EXPIRED ...'
```

Reinitialize your client to refresh tokens:

```python
ds = DSClient()
```

Tapis tokens have a limited lifespan. Long-running notebooks or scripts will hit this after several hours.

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

## Complete Setup Example

```python
# 1. Create .env file (only Tapis credentials required)
with open('.env', 'w') as f:
 f.write('DESIGNSAFE_USERNAME=your_username\n')
 f.write('DESIGNSAFE_PASSWORD=your_password\n')

# 2. Initialize client (auto-sets up TMS credentials)
from dapi import DSClient
ds = DSClient()
```
