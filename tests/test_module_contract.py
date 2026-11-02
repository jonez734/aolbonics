"""jargon's module contract: module.check's stubs pass, and init registers jargon with bbsengine6."""

import argparse

import pytest

import jargon
from bbsengine6 import module
from bbsengine6.module import (
    _check_func_signature,
    _stub_access,
    _stub_buildargs,
    _stub_init,
    _stub_main,
)


_CONTRACT = {
    "init": jargon.init,
    "buildargs": jargon.buildargs,
    "main": jargon.main,
    "access": jargon.access,
}


@pytest.mark.unit
@pytest.mark.parametrize(
    "fn,stub",
    [
        (_CONTRACT["init"], _stub_init),
        (_CONTRACT["buildargs"], _stub_buildargs),
        (_CONTRACT["main"], _stub_main),
        (_CONTRACT["access"], _stub_access),
    ],
)
def test_contract_function_matches_module_check_stub(fn, stub):
    assert _check_func_signature(fn, stub)


@pytest.mark.unit
def test_init_registers_jargon(monkeypatch):
    seen = {}
    monkeypatch.setattr(module, "_register_module",
                        lambda name, path, version, apis: seen.update(name=name, path=path, version=version))
    import bbsengine6
    monkeypatch.setattr(bbsengine6, "register",
                        lambda **kw: seen.update(name=kw["name"], path=kw["module_path"], version=kw["version"]))
    assert jargon.init(argparse.Namespace(debug=False)) is True
    assert seen == {"name": "jargon", "path": "jargon", "version": jargon.__version__}


@pytest.mark.unit
def test_module_name_and_path_are_constants():
    assert jargon.MODULE_NAME == "jargon"
    assert jargon.MODULE_PATH == "jargon"
    assert jargon.ROUTER_PATH == "jargon.api.handler"


@pytest.mark.unit
def test_message_router_registers_jargon_on_construction(monkeypatch):
    """zoid6 never calls the package init(); the sub-router's constructor must register jargon."""
    from jargon.api import handler
    calls = []
    monkeypatch.setattr(handler, "_init_for_router", lambda args: calls.append(args), raising=False)
    import jargon
    monkeypatch.setattr(jargon, "init", lambda args, **kw: calls.append(args) or True)
    handler.MessageRouter(args="ARGS")
    assert calls, "MessageRouter did not register jargon"
