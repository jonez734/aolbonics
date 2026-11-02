"""The write handlers refuse a caller with no bed-attached identity, before touching the database."""

from unittest.mock import MagicMock, patch

import pytest

import jargon.rules as acc
from jargon.api.handler import JargonService


def _svc():
    return JargonService(args=object())


@pytest.mark.unit
@pytest.mark.parametrize("handler", ["_create", "_update"])
def test_write_without_identity_is_refused_before_the_database(handler, monkeypatch):
    monkeypatch.setattr(acc, "member_flags", lambda *a, **k: {"SYSOP"})
    db = MagicMock()
    with patch("jargon.api.handler.database", db):
        reply = getattr(_svc(), handler)({"slug": "x", "term": "x", "definition": "x"}, "r1")
    assert reply["type"] == "error"
    assert "not permitted" in reply["message"]
    db.connect.assert_not_called()


@pytest.mark.unit
def test_body_moniker_is_not_trusted_as_identity(monkeypatch):
    """A moniker sent in the body is not an identity; only bed's _caller counts."""
    monkeypatch.setattr(acc, "member_flags", lambda *a, **k: {"SYSOP"})
    db = MagicMock()
    with patch("jargon.api.handler.database", db):
        reply = _svc()._create({"slug": "x", "term": "x", "definition": "x", "moniker": "root"}, "r2")
    assert reply["type"] == "error"
    db.connect.assert_not_called()


@pytest.mark.unit
def test_attached_identity_with_a_flag_passes_the_gate(monkeypatch):
    monkeypatch.setattr(acc, "member_flags", lambda *a, **k: {"JARGON"})
    msg = {"_caller": {"moniker": "alice"}}
    assert _svc()._authorized("create", msg, "r3") is None
