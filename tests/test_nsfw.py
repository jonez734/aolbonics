"""nsfw on jargon terms: a boolean, default true, returned by lookups and accepted by writes.

The database is not touched; the handler's SQL is checked through a mocked cursor, and the
schema text is checked for the default and the upgrade.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import jargon.access as acc
from jargon.api.handler import JargonService

SQL = Path(__file__).parents[1] / "src" / "jargon" / "sql" / "schema.sql"


@pytest.mark.unit
def test_schema_defaults_nsfw_to_true():
    text = SQL.read_text()
    assert "nsfw boolean not null default true" in text


@pytest.mark.unit
def test_schema_upgrades_an_existing_table():
    text = SQL.read_text()
    assert "alter table jargon.__terms add column if not exists nsfw boolean not null default true" in text


@pytest.mark.unit
def test_lookup_returns_nsfw():
    svc = JargonService(args=object())
    row = {"slug": "wtf", "term": "WTF", "definition": "d", "origin": None, "nsfw": True,
           "datecreatedlocal": None, "dateupdatedlocal": None}
    db = MagicMock()
    db.connect.return_value.__enter__.return_value = MagicMock()
    cur = db.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = row
    with patch("jargon.api.handler.database", db):
        reply = svc._lookup({"slug": "wtf"}, "r1")
    assert reply["term"]["nsfw"] is True


@pytest.mark.unit
def test_create_rejects_a_non_boolean_nsfw(monkeypatch):
    monkeypatch.setattr(acc, "member_flags", lambda *a, **k: {"SYSOP"})
    svc = JargonService(args=object())
    reply = svc._create({"_caller": {"moniker": "root"}, "slug": "x", "term": "x",
                         "definition": "x", "nsfw": "yes"}, "r2")
    assert reply["type"] == "error" and "nsfw" in reply["message"]


@pytest.mark.unit
def test_update_rejects_a_non_boolean_nsfw(monkeypatch):
    monkeypatch.setattr(acc, "member_flags", lambda *a, **k: {"SYSOP"})
    svc = JargonService(args=object())
    reply = svc._update({"_caller": {"moniker": "root"}, "slug": "x", "nsfw": 1}, "r3")
    assert reply["type"] == "error" and "nsfw" in reply["message"]
