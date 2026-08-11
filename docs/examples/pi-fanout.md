# Parallel Fan-Out and Fan-In

The [pi fan-out notebook](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/workflows/pi_fanout/DS_Pi_Fanout_Workflow.ipynb) runs the workflow shape behind most many-job studies. Three Monte-Carlo jobs estimate pi from different seeds at the same time, and an aggregator combines their counts, self-checking against pi itself.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/workflows/pi_fanout/DS_Pi_Fanout_Workflow.ipynb)

## What the notebook shows

1. **Fan-out.** Three shard jobs share one script and differ only in a `SEED` parameter. No edges connect them, so DesignSafe's workflow service submits all three at once.
2. **The run root.** Apps like `python-s3` accept one input directory, yet the fan-in needs every shard's output. Every task of a run archives under one run root, so the aggregator's single input directory is the run root itself, and the service submits it only after every shard has archived.
3. **Archive filters.** Every job archives only its result file. On this workflow the filters cut the aggregator's archiving from minutes to seconds.
4. **The estimate.** Six million samples land within about a thousandth of pi, so a wrong wiring cannot produce a right answer.

The [Workflows guide](../workflows.md) documents the API, and the [OpenSees ML workflow](opensees_ml.md) runs the sequential counterpart, a sweep feeding a training job.
