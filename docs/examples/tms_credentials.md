# TMS Credential Management

This example demonstrates how to manage TMS (Trust Management System) credentials on TACC execution systems using dapi. TMS credentials are SSH key pairs that allow Tapis to access systems like Frontera, Stampede3, and Lonestar6 on your behalf.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/tms_credentials.ipynb)

## Overview

Before submitting jobs to TACC execution systems, you need TMS credentials established on each system. This is a **one-time setup** per system -- once established, credentials persist until you revoke them.

This example covers:

- Checking if credentials exist on a system
- Establishing new credentials (idempotent)
- Force re-creating credentials
- Revoking credentials for cleanup
- Error handling for non-TMS systems

## Quick Start

```python
from dapi import DSClient

ds = DSClient()

# Check and establish credentials on TACC systems
systems = ["frontera", "stampede3", "ls6"]

for system_id in systems:
    ds.systems.establish_credentials(system_id)
```

## API Reference

| Method | Purpose |
|--------|---------|
| `ds.systems.check_credentials("system_id")` | Returns `True`/`False` |
| `ds.systems.establish_credentials("system_id")` | Creates credentials if missing |
| `ds.systems.establish_credentials("system_id", force=True)` | Re-creates credentials |
| `ds.systems.revoke_credentials("system_id")` | Removes credentials |

All methods auto-detect your username. Pass `username="other_user"` to override.

See the [Systems API Reference](../api/systems.md) for full details.
