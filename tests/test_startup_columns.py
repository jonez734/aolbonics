"""--startup checks the required jargon columns. The database is mocked; the query is read-only."""

from unittest.mock import MagicMock

import pytest

from jargon.api import handler as h


def _conn(present: bool):
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (present,)
    return conn


@pytest.mark.unit
def test_present_column_is_not_reported():
    assert h._missing_columns(_conn(present=True)) == []


@pytest.mark.unit
def test_missing_column_is_reported_by_name():
    assert h._missing_columns(_conn(present=False)) == ["column jargon.__terms.nsfw"]


@pytest.mark.unit
def test_check_is_read_only():
    """The column check issues a single select against information_schema and nothing else."""
    conn = _conn(present=True)
    h._missing_columns(conn)
    sql = conn.execute.call_args[0][0].lower()
    assert sql.lstrip().startswith("select")
    assert "information_schema.columns" in sql
    for verb in ("alter", "insert", "update", "delete", "create", "drop"):
        assert verb not in sql


@pytest.mark.unit
def test_startup_reply_is_partial_when_a_column_is_missing(monkeypatch):
    svc = h.JargonService(args=object())
    report = MagicMock(status="installed", present=[1, 2, 3], missing=[])
    monkeypatch.setattr(h.objects, "load_manifest", lambda d: MagicMock(objects=[1, 2, 3]))
    monkeypatch.setattr(h.objects, "check_objects", lambda *a, **k: report)
    monkeypatch.setattr(h, "_missing_grants", lambda conn: [])
    monkeypatch.setattr(h, "_missing_columns", lambda conn: ["column jargon.__terms.nsfw"])
    monkeypatch.setattr(h.database, "connect", lambda *a, **k: _ctx())
    reply = svc._startup("r1")
    assert reply["status"] == "partial"
    assert "column jargon.__terms.nsfw" in reply["missing"]
    assert reply["upgrade_file"] == "sql/schema.sql"


def _ctx():
    cm = MagicMock()
    cm.__enter__.return_value = MagicMock()
    cm.__exit__.return_value = False
    return cm
