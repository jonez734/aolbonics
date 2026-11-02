"""jargon.access: who may read and write jargon entries.

The rule is tested without a database by supplying has_write_flag directly.
"""

import pytest

from jargon.access import access


@pytest.mark.unit
@pytest.mark.parametrize("moniker", [None, "", "anyone"])
def test_lookup_is_open_to_everyone(moniker):
    assert access(None, "lookup", moniker=moniker) is True


@pytest.mark.unit
def test_sysop_may_create_and_update_without_the_flag():
    assert access(None, "create", moniker="root", is_sysop=True, has_write_flag=False) is True
    assert access(None, "update", moniker="root", is_sysop=True, has_write_flag=False) is True


@pytest.mark.unit
def test_member_with_the_flag_may_create_and_update():
    assert access(None, "create", moniker="alice", has_write_flag=True) is True
    assert access(None, "update", moniker="alice", has_write_flag=True) is True


@pytest.mark.unit
def test_member_without_the_flag_is_refused():
    assert access(None, "create", moniker="bob", has_write_flag=False) is False
    assert access(None, "update", moniker="bob", has_write_flag=False) is False


@pytest.mark.unit
@pytest.mark.parametrize("op", ["create", "update"])
def test_unauthenticated_writes_are_refused(op):
    """No moniker means no identity: a write is refused even if a flag would otherwise allow it."""
    assert access(None, op, moniker=None, is_sysop=True, has_write_flag=True) is False
    assert access(None, op, moniker="", has_write_flag=True) is False


@pytest.mark.unit
def test_unknown_operation_is_refused():
    assert access(None, "delete", moniker="root", is_sysop=True) is False


@pytest.mark.unit
def test_flag_lookup_happens_only_when_not_supplied(monkeypatch):
    called = []
    import jargon.access as acc
    monkeypatch.setattr(acc, "_member_has_write_flag", lambda args, m: called.append(m) or True)
    assert access(None, "create", moniker="carol") is True
    assert called == ["carol"]
    called.clear()
    assert access(None, "create", moniker="carol", has_write_flag=False) is False
    assert called == []
