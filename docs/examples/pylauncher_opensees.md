# PyLauncher: OpenSees Cantilever Sweep

A parameter sweep over a 2D cantilever pushover analysis using PyLauncher.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/pylauncher/pylauncher_opensees.ipynb)

For PyLauncher basics, see [PyLauncher Parameter Sweeps](pylauncher.md).

## The model

```
   ^Y
   |
   2       __
   |         |
   |         |
   |         |
 (1)      LCol
   |         |
   |         |
   |         |
 =1=    ----  -------->X
```

- Node 1: fixed base
- Node 2: free top with `NodalMass`
- Elastic beam-column element (A=3.6e9, E=4227, I=1.08e6)
- Gravity load (2000 kip down) then lateral pushover (displacement-controlled, 1000 steps)

## Sweep parameters

5 nodal masses x 3 column lengths = 15 independent runs.

```python
sweep = {
    "NODAL_MASS": [4.19, 4.39, 4.59, 4.79, 4.99],
    "LCOL": [100, 200, 300],
}
```

## Preview

```python
ds.jobs.parametric_sweep.generate(
    "python3 cantilever.py --NodalMass NODAL_MASS --LCol LCOL --outDir out_NODAL_MASS_LCOL",
    sweep,
    preview=True,
)
```

## Generate and submit

```python
ds.jobs.parametric_sweep.generate(
    "python3 cantilever.py --NodalMass NODAL_MASS --LCol LCOL --outDir out_NODAL_MASS_LCOL",
    sweep,
    "/home/jupyter/MyData/opensees_sweep/",
)

job = ds.jobs.parametric_sweep.submit(
    "/MyData/opensees_sweep/",
    app_id="designsafe-agnostic-app",
    allocation="your_allocation",
    node_count=1,
    cores_per_node=48,
    max_minutes=30,
)
job.monitor()
```

## Output

Each run writes to its own directory (`out_4.19_100`, `out_4.19_200`, etc.) containing:

- `DFree.out` — free node displacements
- `RBase.out` — base reactions
- `FCol.out` — column element forces
