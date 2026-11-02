"""zoid6 sub-router for jargon.

zoid6 loads this module from ``services.jargon.modulepath`` and calls
``MessageRouter(args, **auth_kwargs).register_all(server)``. Each handler
answers one request type with a ``<type>_result`` message.

Request types:
    jargon_lookup    {"slug": str}          -> {"term": {...} | None}
    jargon_install   {}                     -> {"message": str}
    jargon_startup   {}                     -> {"status", "present", "total", "missing"}
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any, Dict, Optional

from bbsengine6 import database, io
from bbsengine6.backend import objects

MSG_LOOKUP = "jargon_lookup"
MSG_INSTALL = "jargon_install"
MSG_STARTUP = "jargon_startup"
MESSAGE_TYPES = [MSG_LOOKUP, MSG_INSTALL, MSG_STARTUP]

PACKAGE = "jargon"


def _error(request_id: Any, message: str) -> Dict[str, Any]:
    reply: Dict[str, Any] = {"type": "error", "message": message}
    if request_id is not None:
        reply["request_id"] = request_id
    return reply


def _reply(message_type: str, request_id: Any, body: Dict[str, Any]) -> Dict[str, Any]:
    reply: Dict[str, Any] = {"type": f"{message_type}_result", **body}
    if request_id is not None:
        reply["request_id"] = request_id
    return reply


class JargonService:
    """Handles every jargon_* message for one bed server."""

    def __init__(self, args: Any) -> None:
        self.args = args

    async def handle_message(
        self, server: Any, websocket: Any, path: str, message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        msg_type = message.get("type")
        request_id = message.get("request_id")
        try:
            if msg_type == MSG_LOOKUP:
                return self._lookup(message, request_id)
            if msg_type == MSG_INSTALL:
                return self._install(request_id)
            if msg_type == MSG_STARTUP:
                return self._startup(request_id)
        except Exception as exc:  # noqa: BLE001 - report to the client, keep the daemon up
            io.echo_traceback(f"jargon.api.handler.{msg_type}: {exc}")
            return _error(request_id, f"{msg_type} failed: {exc}")
        return None

    def _lookup(self, message: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        slug = message.get("slug")
        if not isinstance(slug, str) or not slug.strip():
            return _error(request_id, "jargon_lookup requires a slug")
        slug = slug.strip().lower()
        with database.connect(self.args) as conn:
            with database.cursor(conn=conn) as cur:
                cur.execute(
                    "select slug, term, definition, origin, datecreatedlocal, dateupdatedlocal "
                    "from jargon.terms where slug = %s",
                    (slug,),
                )
                row = cur.fetchone()
        term = None
        if row is not None:
            term = {
                "slug": row["slug"],
                "term": row["term"],
                "definition": row["definition"],
                "origin": row["origin"],
                "datecreated": row["datecreatedlocal"].isoformat(),
                "dateupdated": row["dateupdatedlocal"].isoformat(),
            }
        return _reply(MSG_LOOKUP, request_id, {"term": term})

    def _install(self, request_id: Any) -> Dict[str, Any]:
        database.importsql(self.args, "schema.sql", package=PACKAGE)
        database.importsql(self.args, "seed.sql", package=PACKAGE)
        return _reply(MSG_INSTALL, request_id, {"message": "jargon installed"})

    def _startup(self, request_id: Any) -> Dict[str, Any]:
        text = resources.files(PACKAGE).joinpath("sql/objects.json").read_text(encoding="utf-8")
        manifest = objects.load_manifest(json.loads(text))
        with database.connect(self.args) as conn:
            report = objects.check_objects(self.args, manifest, conn=conn)
        return _reply(
            MSG_STARTUP,
            request_id,
            {
                "status": report.status,
                "present": len(report.present),
                "total": len(manifest.objects),
                "missing": [obj.label() for obj in report.missing],
            },
        )


class MessageRouter:
    """zoid6 sub-router entry point. Accepts the optional auth kwargs zoid6 forwards."""

    def __init__(
        self,
        args: Any,
        *,
        session_registry: Any = None,
        secret: Any = None,
        token_store: Any = None,
        instance_id: Any = None,
        clock: Any = None,
        **_unused: Any,
    ) -> None:
        self.args = args
        self.service = JargonService(args)

    def register_all(self, server: Any) -> None:
        server.register_service(self.service, MESSAGE_TYPES)
