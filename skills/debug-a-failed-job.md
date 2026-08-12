---
name: debug-a-failed-job
description: Where to look when a Tapis job fails or seems stuck
---

# Debug a failed job

Read `tapisjob.out` in the archive first; the scheduler and wrapper
write everything there.

```python
job = ds.jobs.job(uuid)
print(job.status, job.last_message)
print(job.get_output_content("tapisjob.out")[-3000:])
```

Failures by stage. Rejected at submit with an allocation message means
the allocation is wrong or inactive for that system. Stuck in
PROCESSING_INPUTS or STAGING means an input URI does not resolve;
check `ds.files.list` on each fileInput. BLOCKED is not failure, the
scheduler is holding the job; wait. FINISHED but empty archive usually
means the app archives elsewhere (opensees-s3 archives to Stampede3
$WORK, not MyData) or an archiveFilter excluded your files.

Transient network errors during a long monitor are survivable; recent
dapi retries polling. A monitor timeout defaults to the job's
maxMinutes, so a long queue wait needs
`monitor(timeout_minutes=...)` above the runtime.
