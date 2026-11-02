"""Bed client for the jargon CLI.

Every jargon command except --help is a single request to a running bed
daemon. The request is sent through bed's shared BedConnection, using
run_with_connection so the socket closes when the call ends.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from bed.client.connection import run_with_connection
from bed.client.exceptions import BedUnavailable
from bed.client.singleton import get_bed_connection


class JargonError(Exception):
    """A jargon request failed. The message is safe to print as-is."""


def _token_path(args: Any) -> str:
    """Where the bed login token lives: --token-file, else $XDG_RUNTIME_DIR/bed.token (bed's own default)."""
    explicit = getattr(args, "token_file", None)
    if explicit:
        return explicit
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    return os.path.join(runtime, "bed.token") if runtime else ""


def _read_token(args: Any) -> str:
    """The bearer token from the login file, or "" when there is none or it cannot be read."""
    path = _token_path(args)
    if not path:
        return ""
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def request(args: Any, message: Dict[str, Any]) -> Dict[str, Any]:
    """Send one jargon request to bed and return the reply.

    A write carries the login token so bed can verify the caller. Jargon never makes up a token; with no
    readable token the write is sent without one and bed refuses it as unauthenticated.

    Raises JargonError if bed is unreachable or the reply is an error.
    """
    if message.get("type") in ("jargon_create", "jargon_update"):
        token = _read_token(args)
        if token:
            message = {**message, "token": token}
    connection = get_bed_connection(args)
    try:
        reply = run_with_connection(connection, lambda: connection.send(message))
    except BedUnavailable as exc:
        raise JargonError(
            f"bed is not available ({exc}). Start bed and try again."
        ) from exc

    if reply.get("type") == "error" or reply.get("ok") is False:
        raise JargonError(reply.get("error") or reply.get("message") or "request failed")
    return reply


def lookup(args: Any, slug: str) -> Dict[str, Any]:
    return request(args, {"type": "jargon_lookup", "slug": slug})


def create(
    args: Any,
    slug: str,
    term: str,
    definition: str,
    origin: Optional[str] = None,
    nsfw: Optional[bool] = None,
) -> Dict[str, Any]:
    message: Dict[str, Any] = {
        "type": "jargon_create",
        "slug": slug,
        "term": term,
        "definition": definition,
    }
    if origin is not None:
        message["origin"] = origin
    if nsfw is not None:
        message["nsfw"] = nsfw
    return request(args, message)


def update(args: Any, slug: str, **fields: Any) -> Dict[str, Any]:
    """Update only the fields passed. Pass origin=None explicitly to clear it."""
    message: Dict[str, Any] = {"type": "jargon_update", "slug": slug}
    message.update(fields)
    return request(args, message)


def install(args: Any) -> Dict[str, Any]:
    return request(args, {"type": "jargon_install"})


def startup(args: Any) -> Dict[str, Any]:
    return request(args, {"type": "jargon_startup"})
