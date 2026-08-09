# Project Permissions: Break It, See It, Fix It

A live walkthrough of the My Projects file-sharing problem and its one-call repair.

[![Try on DesignSafe](https://raw.githubusercontent.com/DesignSafe-CI/dapi/main/DesignSafe-Badge.svg)](https://jupyter.designsafe-ci.org/hub/user-redirect/lab/tree/CommunityData/dapi/project-permissions.ipynb)

For the reference documentation, see [Projects](../projects.md).

## The problem

A researcher runs a job on Stampede3, then copies results into a shared project from a login-node terminal. The files arrive, the portal lists them, and the other project members see nothing, or an empty preview, or read-only files. No error appeared anywhere, and historically only an administrator with sudo could put it right.

The mechanism is POSIX. Project sharing works through a named ACL entry per member plus an ACL mask that caps every entry. Command-line tools damage one or the other:

| Tool | What it does | Result for members |
|---|---|---|
| `scp`, `cp` | file created fresh, member entries inherited, but the source's mode becomes the **mask** | invisible (600 source) or read-only (644 source) |
| `mv`, `cp -p`, `rsync -a` | replicate the source's ACL wholesale, **wiping member entries** | invisible, and `chmod` cannot help |
| Tapis (portal, dapi, job archiving) | service account writes, ACLs inherited intact | healthy |

## The walkthrough

The [notebook](https://github.com/DesignSafe-CI/dapi/blob/main/examples/project-permissions.ipynb) runs the full lifecycle against a real project:

1. **Create** a file owned by you, exactly like an scp'd file (uploaded through `cloud.data`, which acts as the calling user on the storage host).
2. **Break** it the way `scp` of a private file does, by capping the ACL mask.
3. **Audit** with `ds.projects.permissions()`: every member shows `effective: none` while their membership looks perfectly healthy.
4. **Fix** with `ds.projects.fix_permissions()`: the report shows the repair strategy used, here `owner (via cloud.data)`, because a file's owner may always repair its ACLs, from any machine.
5. **Verify**, then audit and repair the whole project in one call.

## The three lines that matter

```python
ds.projects.permissions("PRJ-1234", "/results/run1.out")  # who can actually see it
ds.projects.fix_permissions("PRJ-1234", dry_run=True)  # what a repair would do
ds.projects.fix_permissions("PRJ-1234")  # do it
```

## Prevention

Transfer into projects through Tapis and none of this arises: the portal, dapi uploads, and job archiving straight into the project system (`ds.jobs.generate(archive_system="project-<uuid>", ...)`) all produce correctly shared files. If the command line is unavoidable, use `cp` or `scp` from a login node and finish with `chmod -R g+rwX` on the destination. Never `mv`, `cp -p`, or `rsync -a` into a project.
