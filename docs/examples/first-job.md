# Your First dapi Job

One calculation, every dapi step. A 5%-damped oscillator is shaken at its natural frequency, and a single Stampede3 job integrates the motion and reports the dynamic amplification, which lands at the top of the resonance curve near `1/(2*damping) = 10`. The point of the pair is the dapi lifecycle itself: authenticate, point Tapis at a folder, generate the job request, submit and monitor, and read the result back from the archive, each as one visible call.

Exercise: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/python/first-dapi-job-exercise.ipynb)

Solution: [![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/python/first-dapi-job.ipynb)

## The five steps

1. **Authenticate.** `DSClient()` holds the connection every later call uses.
2. **Point Tapis at the folder.** `ds.files.to_uri` on JupyterHub; `prepare_inputs` uploads from anywhere else.
3. **Generate.** `ds.jobs.generate` builds the full request from the app definition; the notebook prints the dict Tapis receives.
4. **Submit and monitor.** `submit`, `monitor`, `interpret_status`, and the runtime summary showing that a ten-second calculation spends its wall clock on staging and queueing.
5. **Read the archive.** `archive_uri`, `ds.files.list`, and `get_output_content` bring `result.json` back, self-checked against the physics.

The same oscillator continues into the [PyLauncher sweep](pylauncher.md), which computes the whole resonance curve inside one job.
