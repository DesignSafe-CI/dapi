# Jobs

Job submission, monitoring, and management functionality for DesignSafe computational workflows.

## Job Request Generation

```{eval-rst}
.. autofunction:: dapi.jobs.generate_job_request
```

## Job Submission

```{eval-rst}
.. autofunction:: dapi.jobs.submit_job_request
```

## Job Monitoring

```{eval-rst}
.. autofunction:: dapi.jobs.get_job_status
```

```{eval-rst}
.. autofunction:: dapi.jobs.get_runtime_summary
```

```{eval-rst}
.. autofunction:: dapi.jobs.interpret_job_status
```

## SubmittedJob Class

```{eval-rst}
.. autoclass:: dapi.jobs.SubmittedJob
 :members:
 :undoc-members:
 :show-inheritance:
```

## Status Constants

```{eval-rst}
.. autodata:: dapi.jobs.STATUS_TIMEOUT
```

```{eval-rst}
.. autodata:: dapi.jobs.STATUS_INTERRUPTED
```

```{eval-rst}
.. autodata:: dapi.jobs.STATUS_MONITOR_ERROR
```

```{eval-rst}
.. autodata:: dapi.jobs.STATUS_UNKNOWN
```

```{eval-rst}
.. autodata:: dapi.jobs.TAPIS_TERMINAL_STATES
```
