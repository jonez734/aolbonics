"""The jargon client attaches the login token to writes only, and never invents one."""

import pytest

from jargon import client


class _Args:
    def __init__(self, token_file=None):
        self.token_file = token_file


def _capture(monkeypatch):
    sent = {}

    def fake_get(args):
        return object()

    def fake_run(conn, fn):
        return {"type": "x_result", "term": None, "ok": True}

    monkeypatch.setattr(client, "get_bed_connection", fake_get)
    monkeypatch.setattr(client, "run_with_connection", lambda conn, fn: (sent.setdefault("msg", None), {"ok": True})[1])

    class _Conn:
        def send(self, message):
            sent["msg"] = message
            return {"type": "ok"}

    monkeypatch.setattr(client, "get_bed_connection", lambda args: _Conn())
    monkeypatch.setattr(client, "run_with_connection", lambda conn, fn: fn())
    return sent


@pytest.mark.unit
def test_write_carries_the_token_from_the_token_file(monkeypatch, tmp_path):
    tok = tmp_path / "bed.token"
    tok.write_text("abc.def\n")
    sent = _capture(monkeypatch)
    client.create(_Args(str(tok)), "x", "X", "d")
    assert sent["msg"]["token"] == "abc.def"


@pytest.mark.unit
def test_read_does_not_send_a_token(monkeypatch, tmp_path):
    tok = tmp_path / "bed.token"
    tok.write_text("abc.def")
    sent = _capture(monkeypatch)
    client.lookup(_Args(str(tok)), "x")
    assert "token" not in sent["msg"]


@pytest.mark.unit
def test_missing_token_file_sends_no_token(monkeypatch, tmp_path):
    sent = _capture(monkeypatch)
    client.create(_Args(str(tmp_path / "missing")), "x", "X", "d")
    assert "token" not in sent["msg"]
