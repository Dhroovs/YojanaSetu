"""Linux local-demo credentials must remain private and must not replace files."""

import os

import pytest

from scripts import local_demo

pytestmark = pytest.mark.skipif(os.name == "nt", reason="Linux filesystem permission checks")


def test_linux_access_is_private_and_refuses_replacement(tmp_path, monkeypatch):
    path = tmp_path / "access.json"
    monkeypatch.setattr(local_demo, "ACCESS", path)
    accounts = {"synthetic-alias": "temporary-test-value"}
    local_demo.encrypt_access(accounts)
    assert path.stat().st_mode & 0o777 == 0o600
    assert local_demo.read_access() == accounts
    with pytest.raises(FileExistsError):
        local_demo.encrypt_access({"replacement": "must-not-write"})
    assert local_demo.read_access() == accounts


def test_linux_access_rejects_shared_permissions_and_symlinks(tmp_path, monkeypatch):
    path = tmp_path / "access.json"
    monkeypatch.setattr(local_demo, "ACCESS", path)
    local_demo.encrypt_access({"synthetic-alias": "temporary-test-value"})
    path.chmod(0o644)
    with pytest.raises(RuntimeError, match="owner-only"):
        local_demo.read_access()
    path.chmod(0o600)
    link = tmp_path / "symlink.json"
    link.symlink_to(path)
    monkeypatch.setattr(local_demo, "ACCESS", link)
    with pytest.raises(RuntimeError, match="owner-only"):
        local_demo.read_access()
