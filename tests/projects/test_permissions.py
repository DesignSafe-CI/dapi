import unittest
from types import SimpleNamespace
from unittest import mock

from dapi.projects import get_permissions


def _acl(type_, principal, perms, default=False):
    return SimpleNamespace(
        type=type_, principal=principal, permissions=perms, defaultAcl=default
    )


class _Files:
    def __init__(self, entries):
        self.entries = entries
        self.setfacl_calls = []

    def getFacl(self, systemId, path):
        return self.entries

    def getPermissions(self, systemId, path, username):
        return SimpleNamespace(permission="MODIFY")

    def setFacl(self, **kw):
        self.setfacl_calls.append(kw)
        return SimpleNamespace(exitCode=0, stdErr="")


class _Tapis:
    def __init__(self, entries):
        self.files = _Files(entries)


MEMBERS = [
    {"username": "alice", "role": "pi"},
    {"username": "bob", "role": "team_member"},
]


class TestGetPermissions(unittest.TestCase):
    def _run(self, entries):
        t = _Tapis(entries)
        with (
            mock.patch("dapi.projects.resolve_project_uuid", return_value="project-x"),
            mock.patch("dapi.projects.get_project_users", return_value=MEMBERS),
        ):
            return get_permissions(t, "PRJ-1")

    def test_healthy_file_reports_effective_access(self):
        report = self._run(
            [
                _acl("user", "alice", "rwx"),
                _acl("user", "bob", "rwx"),
                _acl("mask", None, "rw-"),
            ]
        )
        bob = next(r for r in report if r["username"] == "bob")
        self.assertEqual(bob["effective"], "rw-")

    def test_scp_clobbered_mask_reports_none(self):
        # scp of a 600-mode file: named entries survive, mask becomes ---
        report = self._run(
            [
                _acl("user", "alice", "rwx"),
                _acl("user", "bob", "rwx"),
                _acl("mask", None, "---"),
            ]
        )
        bob = next(r for r in report if r["username"] == "bob")
        self.assertEqual(bob["effective"], "none")

    def test_moved_file_without_acl_reports_missing(self):
        report = self._run([_acl("mask", None, "rwx")])
        bob = next(r for r in report if r["username"] == "bob")
        self.assertEqual(bob["posix_acl"], "missing")
        self.assertEqual(bob["effective"], "none")

    def test_world_readable_file_is_readable_despite_missing_acl(self):
        # mv'd file: no named entries, but mode rw-rw-r-- leaves other=r--
        report = self._run([_acl("other", None, "r--")])
        bob = next(r for r in report if r["username"] == "bob")
        self.assertEqual(bob["posix_acl"], "missing")
        self.assertEqual(bob["effective"], "r--")

    def test_world_bits_floor_combines_with_masked_entry(self):
        # named entry masked to nothing, but other=r-- still grants read
        report = self._run(
            [
                _acl("user", "bob", "rwx"),
                _acl("mask", None, "---"),
                _acl("other", None, "r--"),
            ]
        )
        bob = next(r for r in report if r["username"] == "bob")
        self.assertEqual(bob["effective"], "r--")


class _FixFiles:
    """Scriptable files API for the tiered fixer."""

    def __init__(self, facl_by_path, setfacl_fail_paths=(), copy_fail=False):
        self.facl_by_path = facl_by_path
        self.setfacl_fail = set(setfacl_fail_paths)
        self.copy_fail = copy_fail
        self.calls = []

    def listFiles(self, systemId, path, recurse=False):
        if path == "/":
            entries = [
                SimpleNamespace(name=n.lstrip("/"), path=n.lstrip("/"), type="file")
                for n in self.facl_by_path
                if n != "/"
            ]
            if not recurse:
                return entries or [SimpleNamespace(name="", path="/", type="dir")]
            return entries
        return [
            SimpleNamespace(name=path.lstrip("/"), path=path.lstrip("/"), type="file")
        ]

    def getFacl(self, systemId, path):
        key = "/" + path.lstrip("/")
        if key.split("/")[-1] in getattr(self, "owner_fixed", set()):
            return self.facl_by_path.get("/HEALTHY", [])
        return self.facl_by_path.get(path, self.facl_by_path.get(key, []))

    def setFacl(self, **kw):
        system = kw.get("systemId", "")
        self.calls.append(("setFacl", kw["path"], kw["aclString"], system))
        if system == "cloud.data":
            if getattr(self, "owner_fail", False):
                return SimpleNamespace(exitCode=1, stdErr="Operation not permitted")
            self.owner_fixed = getattr(self, "owner_fixed", set())
            self.owner_fixed.add(kw["path"].split("/")[-1])
            return SimpleNamespace(exitCode=0, stdErr="")
        code = 1 if kw["path"] in self.setfacl_fail else 0
        return SimpleNamespace(exitCode=code, stdErr="")

    def moveCopy(self, systemId, path, operation, newPath):
        self.calls.append(("moveCopy", operation, path, newPath))
        if operation == "COPY" and self.copy_fail:
            raise RuntimeError("Permission denied")
        # a fixed copy has healthy ACLs
        self.facl_by_path[newPath] = self.facl_by_path.get("/HEALTHY", [])
        return SimpleNamespace()

    def delete(self, systemId, path):
        self.calls.append(("delete", path))
        return SimpleNamespace()


class _FixTapis:
    def __init__(self, files):
        self.files = files
        self.systems = SimpleNamespace(
            getSystem=lambda systemId: SimpleNamespace(rootDir="/corral/proj/x")
        )


HEALTHY = [
    _acl("user", "alice", "rwx"),
    _acl("user", "bob", "rwx"),
    _acl("mask", None, "rw-"),
]
MASKED = [
    _acl("user", "alice", "rwx"),
    _acl("user", "bob", "rwx"),
    _acl("mask", None, "---"),
]
WIPED = [_acl("mask", None, "rwx")] and []


def _run_fix(files, **kw):
    from dapi.projects import fix_project_permissions

    t = _FixTapis(files)
    with (
        mock.patch("dapi.projects.resolve_project_uuid", return_value="project-x"),
        mock.patch("dapi.projects.get_project_users", return_value=MEMBERS),
    ):
        return fix_project_permissions(t, "PRJ-1", "/", **kw)


class TestFixPermissions(unittest.TestCase):
    def test_healthy_files_are_skipped(self):
        files = _FixFiles({"/good.txt": HEALTHY, "/HEALTHY": HEALTHY})
        report = _run_fix(files)
        self.assertIn("/good.txt", report["skipped_healthy"])
        self.assertEqual(report["fixed"], {})

    def test_masked_service_owned_fixed_directly(self):
        files = _FixFiles({"/bad.txt": MASKED, "/HEALTHY": HEALTHY})
        report = _run_fix(files)
        self.assertEqual(report["fixed"]["/bad.txt"], "direct")

    def test_eperm_falls_back_to_copy_recreate(self):
        files = _FixFiles(
            {"/bad.txt": MASKED, "/HEALTHY": HEALTHY},
            setfacl_fail_paths={"/bad.txt"},
        )
        files.owner_fail = True  # not the caller's file either
        report = _run_fix(files)
        self.assertTrue(report["fixed"]["/bad.txt"].startswith("copy"))
        ops = [c for c in files.calls if c[0] in ("moveCopy", "delete")]
        self.assertEqual(ops[0][:2], ("moveCopy", "COPY"))
        self.assertEqual(ops[1], ("delete", "/bad.txt"))
        self.assertEqual(ops[2][:2], ("moveCopy", "MOVE"))

    def test_unreadable_file_reported_with_owner_command(self):
        files = _FixFiles(
            {"/locked.txt": MASKED, "/HEALTHY": HEALTHY},
            setfacl_fail_paths={"/locked.txt"},
            copy_fail=True,
        )
        files.owner_fail = True
        report = _run_fix(files)
        self.assertEqual(report["fixed"], {})
        item = report["unfixable"][0]
        self.assertEqual(item["disease"], "mask")
        self.assertIn("fix_permissions", item["owner_fix"])

    def test_user_owned_file_fixed_by_owner_tier(self):
        files = _FixFiles(
            {"/mine.txt": MASKED, "/HEALTHY": HEALTHY},
            setfacl_fail_paths={"/mine.txt"},  # project-system EPERM
        )
        report = _run_fix(files)
        self.assertEqual(report["fixed"]["/mine.txt"], "owner (via cloud.data)")
        owner_calls = [c for c in files.calls if c[3] == "cloud.data"]
        self.assertIn("corral/proj/x/mine.txt", owner_calls[0][1])

    def test_other_owner_unreadable_reports_their_fix_call(self):
        files = _FixFiles(
            {"/theirs.txt": MASKED, "/HEALTHY": HEALTHY},
            setfacl_fail_paths={"/theirs.txt"},
            copy_fail=True,
        )
        files.owner_fail = True  # cloud.data EPERM: caller is not the owner
        report = _run_fix(files)
        self.assertEqual(report["fixed"], {})
        item = report["unfixable"][0]
        self.assertIn("fix_permissions('PRJ-1', '/theirs.txt')", item["owner_fix"])

    def test_dry_run_changes_nothing(self):
        files = _FixFiles({"/bad.txt": MASKED, "/HEALTHY": HEALTHY})
        report = _run_fix(files, dry_run=True)
        self.assertEqual(report["fixed"]["/bad.txt"], "planned (mask)")
        self.assertEqual([c for c in files.calls if c[0] == "setFacl"], [])


if __name__ == "__main__":
    unittest.main()
