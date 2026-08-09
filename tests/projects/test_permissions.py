import unittest
from types import SimpleNamespace
from unittest import mock

from dapi.projects import fix_project_permissions, get_permissions


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


class TestFixPermissions(unittest.TestCase):
    def test_acl_string_covers_members_mask_and_defaults(self):
        t = _Tapis([])
        with (
            mock.patch("dapi.projects.resolve_project_uuid", return_value="project-x"),
            mock.patch("dapi.projects.get_project_users", return_value=MEMBERS),
        ):
            plan = fix_project_permissions(t, "PRJ-1", "/results")
        call = (
            t.files.setFacl_calls
            if hasattr(t.files, "setFacl_calls")
            else t.files.setfacl_calls
        )
        kw = call[0]
        self.assertEqual(kw["operation"], "ADD")
        self.assertEqual(kw["recursionMethod"], "PHYSICAL")
        for token in (
            "user:alice:rwX",
            "user:bob:rwX",
            "mask::rwX",
            "default:user:bob:rwX",
            "default:mask::rwX",
        ):
            self.assertIn(token, kw["aclString"])
        self.assertTrue(plan["applied"])

    def test_dry_run_applies_nothing(self):
        t = _Tapis([])
        with (
            mock.patch("dapi.projects.resolve_project_uuid", return_value="project-x"),
            mock.patch("dapi.projects.get_project_users", return_value=MEMBERS),
        ):
            plan = fix_project_permissions(t, "PRJ-1", dry_run=True)
        self.assertFalse(plan["applied"])
        self.assertEqual(t.files.setfacl_calls, [])


if __name__ == "__main__":
    unittest.main()
