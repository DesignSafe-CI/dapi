# Systems

## Queues

List available batch queues on a TACC execution system.

```python
from dapi import DSClient

ds = DSClient()

queues = ds.systems.queues("frontera")
for q in queues:
    print(f"{q.name}: max {q.maxNodeCount} nodes, {q.maxMinutes} min")
```

## TMS credentials

dapi needs SSH credentials on TACC systems to submit jobs. `DSClient()` sets these up automatically on init. To manage them manually:

```python
# Check
ds.systems.check_credentials("frontera")
# → True / False

# Establish (idempotent — skips if already set)
ds.systems.establish_credentials("frontera")

# Force re-create
ds.systems.establish_credentials("frontera", force=True)

# Revoke
ds.systems.revoke_credentials("frontera")
```

## TACC systems

| System | Typical use |
|---|---|
| `frontera` | Large-scale compute |
| `stampede3` | General-purpose compute |
| `ls6` | Lone Star 6 |
