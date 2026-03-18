# Systems

System information, queue management, and TMS credential management for DesignSafe execution systems.

## System Queues

::: dapi.systems.list_system_queues

## TMS Credential Management

Manage Tapis Managed Secrets (TMS) credentials on execution systems. TMS credentials are SSH key pairs that allow Tapis to access TACC systems (Frontera, Stampede3, Lonestar6) on behalf of a user. They must be established once per system before submitting jobs.

### Check Credentials

::: dapi.systems.check_credentials

### Establish Credentials

::: dapi.systems.establish_credentials

### Revoke Credentials

::: dapi.systems.revoke_credentials