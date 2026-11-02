"""The write handlers refuse a caller with no bed-attached identity, before touching the database."""

from unittest.mock import MagicMock, patch

import pytest

from jargon.api.handler import JargonService


def _svc():
    return JargonService(args=object())


@pytest.mark.unit
@pytest.mark.parametrize("op,handler", [("create", "_create"), ("update", "_update")])
def test_write_without_identity_is_refused_before_the_database(op, handler):
    db = MagicMock()
    with patch("jargon.api.handler.database", db):
        reply = getattr(_svc(), handler)({"slug": "x", "term": "x", "definition": "x"}, "r1")
    assert reply["type"] == "error"
    assert "not permitted" in reply["message"]
    db.connect.assert_not_called()


@pytest.mark.unit
def test_body_moniker_is_not_trusted_as_identity():
    """A moniker sent in the message body is not an identity; only bed's _caller counts."""
    db = MagicMock()
    with patch("jargon.api.handler.database", db):
        reply = _svc()._create({"slug": "x", "term": "x", "definition": "x", "moniker": "root"}, "r2")
    assert reply["type"] == "error"
    db.connect.assert_not_called()


@pytest.mark.unit
def test_attached_sysop_identity_is_allowed_past_the_gate():
    svc = _svc()
    msg = {"_caller": {"moniker": "root", "is_sysop": True}}
    assert svc._authorized("create", msg, "r3") is None
