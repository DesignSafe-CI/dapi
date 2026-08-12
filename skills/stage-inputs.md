---
name: stage-inputs
description: Getting input files where Tapis apps can read them, and the path traps
---

# Stage inputs

Tapis apps read inputs from a `tapis://` URI. `ds.files.to_uri`
translates a DesignSafe path (MyData, projects) directly; nothing
uploads because the file is already on DesignSafe storage.

A laptop folder is different. `ds.jobs.prepare_inputs(app_id,
local_dir)` uploads it once and returns the staged location. The trap:
a local folder whose path merely *contains* `/MyData/` translates
without existing remotely, and the job fails at staging with
FILES_TXFR_SVC_SRCPAT. Recent dapi verifies the translated path exists
and falls back to uploading; on older versions verify with
`ds.files.list(uri)` before submitting.

CommunityData is read-only. Copy anything you need to modify into
MyData first, and never point `archive_path` at CommunityData.
