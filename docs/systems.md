# Systems

## List available systems

```python
from dapi import DSClient
ds = DSClient()

# HPC + storage systems (default)
ds.systems.list()

# HPC execution systems only (with credential status)
ds.systems.list("hpc")

# Storage systems only
ds.systems.list("storage")

# All systems including internal
ds.systems.list("all")
```

## TACC Systems

DesignSafe jobs run on TACC execution systems. For hardware specs, node types, queues, and allocations, see the [DesignSafe Workflows: Compute Environments](https://kks32.github.io/ds-workflows/guide/compute-environments.html).

| System ID | System | Notes |
|---|---|---|
| `stampede3` | [Stampede3](https://docs.tacc.utexas.edu/hpc/stampede3/) | Primary DesignSafe execution system (SKX, ICX, SPR, PVC nodes) |
| `frontera` | [Frontera](https://docs.tacc.utexas.edu/hpc/frontera/) | Leadership-class, 56-core Cascade Lake nodes |
| `ls6` | [Lonestar6](https://docs.tacc.utexas.edu/hpc/lonestar6/) | General-purpose, 128-core AMD Milan, NVIDIA A100 GPUs |

## Queues

List available batch queues on a TACC execution system.

```python
from dapi import DSClient

ds = DSClient()

queues = ds.systems.queues("stampede3")
for q in queues:
    print(f"{q.name}: max {q.maxNodeCount} nodes, {q.maxMinutes} min")
```

## TMS Credentials

TMS (TACC Management System) manages SSH key pairs that allow Tapis to access TACC systems on your behalf. `DSClient()` establishes TMS credentials automatically on first use. The methods below are for manual management.

### Establish Credentials

```python
ds.systems.establish_credentials("stampede3")
ds.systems.establish_credentials("frontera")
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

TMS credentials work from any environment, not just DesignSafe JupyterHub. As long as you can authenticate with Tapis (e.g., via `.env` file), you can manage TMS credentials from your laptop, CI/CD pipelines, or any Python script:

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
TMS credential management only works for systems configured with `TMS_KEYS` authentication. TACC execution systems (`frontera`, `stampede3`, `ls6`) use TMS_KEYS.

**System Not Found:**
```
CredentialError: System 'nonexistent' not found.
```
Verify the system ID. Common system IDs: `frontera`, `stampede3`, `ls6`.
