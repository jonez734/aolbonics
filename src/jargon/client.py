"""Bed client for the jargon CLI.

Every jargon command except --help is a single request to a running bed
daemon. The request is sent through bed's shared BedConnection, using
run_with_connection so the socket closes when the call ends.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from bed.client.connection import run_with_connection
from bed.client.exceptions import BedUnavailable
from bed.client.singleton import get_bed_connection


class JargonError(Exception):
    """A jargon request failed. The message is safe to print as-is."""


def request(args: Any, message: Dict[str, Any]) -> Dict[str, Any]:
    """Send one jargon request to bed and return the reply.

    Raises JargonError if bed is unreachable or the reply is an error.
    """
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
