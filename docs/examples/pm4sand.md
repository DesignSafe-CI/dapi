# PM4Sand Free-Field Site Response

A layered liquefiable soil column on an elastic half-space, shaken from below. The OpenSees model uses SSPquadUP elements for coupled soil and pore water and the PM4Sand constitutive model for the liquefiable layers, and the notebooks run it as a DesignSafe job and plot accelerations, response spectra, peak-response profiles, and the excess pore pressures that signal liquefaction. The model and plotting scripts come from the University of Washington's freeFieldJupyterPM4Sand example by the Arduino group; the dapi version runs from any machine through the `opensees-s3` app on Stampede3, one core of one node on `skx-dev`, and the solution also shows the no-allocation `opensees-express` variant.

The example ships as a pair. The **exercise** poses the run as four TODOs with hints, translate the inputs, submit and monitor, collect the recorders, plot, and the **solution** is the executed answer.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/opensees/pm4sand/DS_PM4Sand_FreeField_Exercise.ipynb)

[Solution notebook](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/opensees/pm4sand/DS_PM4Sand_FreeField_Solution.ipynb)

## Files

| File | Role |
|---|---|
| `DS_PM4Sand_FreeField_Exercise.ipynb` | The run as four TODOs with hints |
| `DS_PM4Sand_FreeField_Solution.ipynb` | The executed answer |
| `N10_T3.tcl` | The soil column model, gravity stages then dynamic analysis |
| `velocity.input` | The input motion |
| `plotAcc.py`, `plotProfile.py`, `plotPorepressure.py`, `respSpectra.py` | Plotting, each taking the results folder as its argument |

The tcl declares its input motion with the modern explicit `timeSeries` form; the legacy inline form in the original is rejected by current OpenSees, which left recorders empty.
