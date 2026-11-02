"""jargon.rules: who may read and write. Only the moniker is passed in; flags come from the engine.

member_flags is patched so the rule runs without a database.
"""

import pytest

import jargon.rules as acc
from jargon.rules import access


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
    assert access(None, "lookup", moniker=moniker) is True


@pytest.mark.unit
@pytest.mark.parametrize("op", ["create", "update"])
def test_sysop_may_write(op, members):
    members({"root": {"SYSOP"}})
    assert access(None, op, moniker="root") is True


@pytest.mark.unit
@pytest.mark.parametrize("op", ["create", "update"])
def test_jargon_flag_may_write(op, members):
    members({"alice": {"JARGON"}})
    assert access(None, op, moniker="alice") is True


@pytest.mark.unit
@pytest.mark.parametrize("op", ["create", "update"])
def test_member_without_a_flag_is_refused(op, members):
    members({"bob": {"APPROVED"}})
    assert access(None, op, moniker="bob") is False


@pytest.mark.unit
def test_unknown_member_is_refused(members):
    members({})
    assert access(None, "create", moniker="ghost") is False


@pytest.mark.unit
@pytest.mark.parametrize("moniker", [None, ""])
def test_unauthenticated_writes_are_refused(moniker, members):
    members({"root": {"SYSOP", "JARGON"}})
    assert access(None, "create", moniker=moniker) is False


@pytest.mark.unit
def test_unknown_operation_is_refused(members):
    members({"root": {"SYSOP"}})
    assert access(None, "delete", moniker="root") is False


@pytest.mark.unit
def test_flag_names_are_matched_case_insensitively(members, monkeypatch):
    """member_flags upper-cases names, so a stored lower-case flag still matches."""
    monkeypatch.setattr(acc, "member_flags", lambda args, m, **kw: {n.upper() for n in ("jargon",)})
    assert access(None, "create", moniker="alice") is True


@pytest.mark.unit
def test_module_load_gate_run_passes_without_a_caller():
    """module.check calls access(args, "run") with no moniker; it must pass."""
    assert access(None, "run") is True


@pytest.mark.unit
@pytest.mark.parametrize("op", ["create", "update"])
def test_missing_moniker_argument_raises(op, members):
    """moniker is required: omitting it is a TypeError, not a silent refusal."""
    members({"root": {"SYSOP"}})
    with pytest.raises(TypeError, match="moniker"):
        access(None, op)


@pytest.mark.unit
def test_access_matches_module_check_stub():
    """module.check requires access(args, op, **kwargs); jargon's must pass that signature check."""
    from bbsengine6.module import _check_func_signature, _stub_access
    assert _check_func_signature(access, _stub_access)
