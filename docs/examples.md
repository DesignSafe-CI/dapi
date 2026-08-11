# Examples

Complete worked examples showing dapi workflows. Each links to a runnable notebook on DesignSafe JupyterHub.

### Your First dapi Job
One calculation, every dapi step: authenticate, stage, generate, submit, monitor, and read the result from the archive.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/python/first-dapi-job-exercise.ipynb)

Solution: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/python/first-dapi-job.ipynb)

[Full documentation](examples/first-job.md)

---

### File Access
Access files across all DesignSafe storage systems (MyData, CommunityData, NHERI-Published, NEES, MyProjects).

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/files.ipynb)

---

### Projects
List, inspect, and access files in DesignSafe projects.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/projects.ipynb)

---

### Publications
Search and browse published datasets on DesignSafe.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/publications.ipynb)

---

### Systems
List HPC and storage systems, check credentials, and view queues.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/systems.ipynb)

---

### Logging and Verbosity
Control how much dapi reports: INFO milestones, full DEBUG trace, or silence.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/logging.ipynb)

[Full documentation](logging.md)

---

### Application Management
Discover and manage applications on DesignSafe.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/apps.ipynb)

---

### Database Queries
Access DesignSafe research databases (NGL, Earthquake Recovery, Vp).

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/db.ipynb)

[Full documentation](examples/database.md)

---

### Generic Python on HPC
Run any Python script (or executable) on Stampede3 with the general-purpose `python-s3` app, shown here as Monte Carlo pi across all 48 cores of a node.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/python/python-s3-pi.ipynb)

[Full documentation](examples/python.md) · [App documentation](https://designsafe-ci.github.io/ds-workflows/apps/python)

---

### Material Point Method (MPM)
Submit and monitor MPM simulations.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/mpm/mpm-minimal.ipynb)

[Full documentation](examples/mpm.md)

---

### OpenFOAM CFD
Computational fluid dynamics with OpenFOAM.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/openfoam/openfoam-minimal.ipynb)

[Full documentation](examples/openfoam.md)

---

### OpenSees Structural Analysis
Earthquake engineering simulations with OpenSees.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/opensees/OpenSeesMP-dapi.ipynb)

[Full documentation](examples/opensees.md)

---

### quoFEM Sensitivity Analysis
Global sensitivity analysis with the SimCenter UQ engine (quoFEM) on Stampede3, with automatic input bundling and Sobol-index post-processing.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/quoFEM-sensitivity/quoFEM-sensitivity-dapi.ipynb)

[Full documentation](examples/quofem.md)

---

### PyLauncher Parameter Sweeps
Sweep the forcing frequency of a damped oscillator, one task per frequency, and reassemble the resonance curve from the archive.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/pylauncher/pylauncher_sweep.ipynb)

Exercise: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/pylauncher/pylauncher_sweep_exercise.ipynb)

[Full documentation](examples/pylauncher.md)

---

### PyLauncher: OpenSees Cantilever Sweep
Fifteen pushover analyses in one job, and the pushover curves plotted from the archived recorders.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/pylauncher/pylauncher_opensees.ipynb)

Exercise: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/pylauncher/pylauncher_opensees_exercise.ipynb)

[Full documentation](examples/pylauncher_opensees.md)

---

### OpenSees ML Sweep
Sweep an OpenSeesPy cantilever with PyLauncher, then fit a regression that recovers the physics, one job end to end.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/opensees_ml/DS_OpenSees_ML_Example.ipynb)

[Full documentation](examples/opensees_ml.md)

---

### PM4Sand Free-Field Site Response
Exercise and solution: a liquefiable soil column runs as an OpenSees job and the plots find the liquefying layer.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/opensees/pm4sand/DS_PM4Sand_FreeField_Exercise.ipynb)

Solution: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/opensees/pm4sand/DS_PM4Sand_FreeField_Solution.ipynb)

[Full documentation](examples/pm4sand.md)

---

### Run Your Own Container
Register a container app in two calls and run a GitHub-published image on a compute node.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/custom-container-app.ipynb)

[Full documentation](examples/custom-container-app.md)

---

### Parallel Fan-Out and Fan-In
Three Monte-Carlo jobs run at once and an aggregator combines them, the workflow shape behind most many-job studies.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/workflows/pi_fanout/DS_Pi_Fanout_Workflow.ipynb)

Exercise: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/workflows/pi_fanout/DS_Pi_Fanout_Exercise.ipynb)

[Full documentation](examples/pi-fanout.md)

---

### Build Your Own Tapis App
Scaffold, register, and run a custom app with two dapi calls.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/custom-app.ipynb)

[Full documentation](examples/custom-app.md)

---

### Project Permissions
Audit who can see project files and repair broken sharing with one call.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/project-permissions.ipynb)

[Full documentation](examples/project-permissions.md)

---

### TMS Credentials
Manage SSH credentials on TACC execution systems.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/tms_credentials.ipynb)

[Full documentation](examples/tms_credentials.md)
