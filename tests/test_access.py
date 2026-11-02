"""jargon.access: who may read and write. Only the moniker is passed in; flags come from the engine.

member_flags is patched so the rule runs without a database.
"""

import pytest

import jargon.access as acc
from jargon.access import access


def _flags(mapping):
    """A member_flags stand-in: returns the flag set for each moniker in ``mapping``."""
    return lambda args, moniker, **kw: set(mapping.get(moniker, ()))


@pytest.fixture
def members(monkeypatch):
    def use(mapping):
        monkeypatch.setattr(acc, "member_flags", _flags(mapping))
    return use


@pytest.mark.unit
@pytest.mark.parametrize("moniker", [None, "", "anyone"])
def test_lookup_is_open_to_everyone(moniker, members):
    members({})
    assert access(None, "lookup", moniker) is True


@pytest.mark.unit
@pytest.mark.parametrize("op", ["create", "update"])
def test_sysop_may_write(op, members):
    members({"root": {"SYSOP"}})
    assert access(None, op, "root") is True


@pytest.mark.unit
@pytest.mark.parametrize("op", ["create", "update"])
def test_jargon_flag_may_write(op, members):
    members({"alice": {"JARGON"}})
    assert access(None, op, "alice") is True


@pytest.mark.unit
@pytest.mark.parametrize("op", ["create", "update"])
def test_member_without_a_flag_is_refused(op, members):
    members({"bob": {"APPROVED"}})
    assert access(None, op, "bob") is False


@pytest.mark.unit
def test_unknown_member_is_refused(members):
    members({})
    assert access(None, "create", "ghost") is False


@pytest.mark.unit
@pytest.mark.parametrize("moniker", [None, ""])
def test_unauthenticated_writes_are_refused(moniker, members):
    members({"root": {"SYSOP", "JARGON"}})
    assert access(None, "create", moniker) is False


@pytest.mark.unit
def test_unknown_operation_is_refused(members):
    members({"root": {"SYSOP"}})
    assert access(None, "delete", "root") is False


@pytest.mark.unit
def test_flag_names_are_matched_case_insensitively(members, monkeypatch):
    """member_flags upper-cases names, so a stored lower-case flag still matches."""
    monkeypatch.setattr(acc, "member_flags", lambda args, m, **kw: {n.upper() for n in ("jargon",)})
    assert access(None, "create", "alice") is True
