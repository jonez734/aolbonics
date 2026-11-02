"""zoid6 sub-router for jargon.

zoid6 loads this module from ``services.jargon.modulepath`` and calls
``MessageRouter(args, **auth_kwargs).register_all(server)``. Each handler
answers one request type with a ``<type>_result`` message.

Request types:
    jargon_lookup    {"slug": str}                                -> {"term": {...} | None}
    jargon_create    {"slug", "term", "definition", "origin"?}    -> {"term": {...}}
    jargon_update    {"slug", "term"?, "definition"?, "origin"?}  -> {"term": {...}}
    jargon_install   {}                                           -> {"message": str}
    jargon_startup   {}                                           -> {"status", "present", "total", "missing"}
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any, Dict, Optional

from bbsengine6 import database, io
from bbsengine6.backend import objects

from jargon.access import access

MSG_LOOKUP = "jargon_lookup"
MSG_CREATE = "jargon_create"
MSG_UPDATE = "jargon_update"
MSG_INSTALL = "jargon_install"
MSG_STARTUP = "jargon_startup"
MESSAGE_TYPES = [MSG_LOOKUP, MSG_CREATE, MSG_UPDATE, MSG_INSTALL, MSG_STARTUP]

_TERM_COLUMNS = (
    "slug, term, definition, origin, datecreatedlocal, dateupdatedlocal"
)

PACKAGE = "jargon"
GRANTS_NOTE = "the database owner or zoid6_role_migration.sql (see sql/grants.sql)"

# Privileges the bed's role needs for jargon (see sql/grants.sql). Checked read-only with the
# has_*_privilege functions, so a missing grant is reported, not silently failed later.
_REQUIRED_GRANTS = (
    ("database CREATE on zoid6", "select has_database_privilege(current_user, current_database(), 'CREATE')"),
    ("schema usage on engine", "select has_schema_privilege(current_user, 'engine', 'USAGE')"),
    ("select on engine.__member", "select has_table_privilege(current_user, 'engine.__member', 'SELECT')"),
)


def _missing_grants(conn: Any) -> list:
    """Return the labels of required privileges the connected role does not have."""
    missing = []
    for label, query in _REQUIRED_GRANTS:
        row = conn.execute(query).fetchone()
        value = row[0] if isinstance(row, (tuple, list)) else row.get(next(iter(row)))
        if not value:
            missing.append(label)
    return missing


def _iso(value: Any) -> Optional[str]:
    """ISO text for a timestamp, or None when the value is NULL."""
    return value.isoformat() if value is not None else None


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
            if msg_type == MSG_CREATE:
                return self._create(message, request_id)
            if msg_type == MSG_UPDATE:
                return self._update(message, request_id)
            if msg_type == MSG_INSTALL:
                return self._install(request_id)
            if msg_type == MSG_STARTUP:
                return self._startup(request_id)
        except Exception as exc:  # noqa: BLE001 - report to the client, keep the daemon up
            io.echo_traceback(f"jargon.api.handler.{msg_type}: {exc}")
            return _error(request_id, f"{msg_type} failed: {exc}")
        return None

    @staticmethod
    def _term_dict(row: Any) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return {
            "slug": row["slug"],
            "term": row["term"],
            "definition": row["definition"],
            "origin": row["origin"],
            # Local times are NULL for a member with no time zone (the engine's views behave the same way).
            "datecreated": _iso(row["datecreatedlocal"]),
            "dateupdated": _iso(row["dateupdatedlocal"]),
        }

    @staticmethod
    def _slug(message: Dict[str, Any], request_id: Any, who: str) -> Any:
        """Return (slug, None) or (None, error reply)."""
        slug = message.get("slug")
        if not isinstance(slug, str) or not slug.strip():
            return None, _error(request_id, f"{who} requires a slug")
        return slug.strip().lower(), None

    @staticmethod
    def _text(message: Dict[str, Any], key: str) -> Optional[str]:
        value = message.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        return value.strip()

    def _lookup(self, message: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        slug, err = self._slug(message, request_id, "jargon_lookup")
        if err:
            return err
        with database.connect(self.args) as conn:
            with database.cursor(conn=conn) as cur:
                cur.execute(f"select {_TERM_COLUMNS} from jargon.terms where slug = %s", (slug,))
                row = cur.fetchone()
        return _reply(MSG_LOOKUP, request_id, {"term": self._term_dict(row)})

    def _caller(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """The authenticated caller bed attaches to the message. Never read from the body alone.

        bed does not attach an identity yet, so this returns an empty caller and every write is refused.
        """
        return message.get("_caller") or {}

    def _authorized(self, op: str, message: Dict[str, Any], request_id: Any) -> Optional[Dict[str, Any]]:
        """Return an error reply when the caller may not perform ``op``; None when allowed."""
        caller = self._caller(message)
        if access(self.args, op, caller.get("moniker")):
            return None
        return _error(request_id, f"jargon_{op}: not permitted for this caller")

    def _create(self, message: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        denied = self._authorized("create", message, request_id)
        if denied:
            return denied
        slug, err = self._slug(message, request_id, "jargon_create")
        if err:
            return err
        term = self._text(message, "term")
        definition = self._text(message, "definition")
        origin = self._text(message, "origin")
        if not term or not definition:
            return _error(request_id, "jargon_create requires term and definition")
        with database.connect(self.args) as conn:
            with database.cursor(conn=conn) as cur:
                cur.execute(
                    "insert into jargon.__terms (slug, term, definition, origin) "
                    "values (%s, %s, %s, %s) "
                    "on conflict (slug) do nothing "
                    "returning slug",
                    (slug, term, definition, origin or None),
                )
                if cur.fetchone() is None:
                    return _error(request_id, f"term {slug!r} already exists")
                cur.execute(f"select {_TERM_COLUMNS} from jargon.terms where slug = %s", (slug,))
                row = cur.fetchone()
        return _reply(MSG_CREATE, request_id, {"term": self._term_dict(row)})

    def _update(self, message: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        denied = self._authorized("update", message, request_id)
        if denied:
            return denied
        slug, err = self._slug(message, request_id, "jargon_update")
        if err:
            return err
        # Only the fields present in the request change. A null origin clears it.
        changes = {}
        for key in ("term", "definition", "origin"):
            if key in message:
                value = self._text(message, key)
                if key in ("term", "definition") and not value:
                    return _error(request_id, f"{key} cannot be empty")
                if key == "origin":
                    changes[key] = value or None
                else:
                    changes[key] = value
        if not changes:
            return _error(request_id, "jargon_update needs at least one of term, definition, origin")
        assignments = ", ".join(f"{col} = %s" for col in changes)
        params = list(changes.values()) + [slug]
        with database.connect(self.args) as conn:
            with database.cursor(conn=conn) as cur:
                cur.execute(
                    f"update jargon.__terms set {assignments}, dateupdated = now() "
                    "where slug = %s returning slug",
                    params,
                )
                if cur.fetchone() is None:
                    return _error(request_id, f"no term {slug!r}")
                cur.execute(f"select {_TERM_COLUMNS} from jargon.terms where slug = %s", (slug,))
                row = cur.fetchone()
        return _reply(MSG_UPDATE, request_id, {"term": self._term_dict(row)})

    def _install(self, request_id: Any) -> Dict[str, Any]:
        # importsql returns False on failure instead of raising, and needs an explicit connection.
        # Run both files on one connection and report any failure rather than claiming success.
        with database.connect(self.args) as conn:
            missing = _missing_grants(conn)
            if missing:
                return _error(
                    request_id,
                    f"jargon_install: the database role lacks {', '.join(missing)}. "
                    f"Ask {GRANTS_NOTE} to grant them, then retry.",
                )
            for filename in ("schema.sql", "seed.sql"):
                if database.importsql(self.args, filename, conn=conn, package=PACKAGE) is False:
                    return _error(request_id, f"jargon_install failed while loading {filename}")
        return _reply(MSG_INSTALL, request_id, {"message": "jargon installed"})

    def _startup(self, request_id: Any) -> Dict[str, Any]:
        text = resources.files(PACKAGE).joinpath("sql/objects.json").read_text(encoding="utf-8")
        manifest = objects.load_manifest(json.loads(text))
        with database.connect(self.args) as conn:
            report = objects.check_objects(self.args, manifest, conn=conn)
            missing_grants = _missing_grants(conn)
        missing = [obj.label() for obj in report.missing] + [f"grant {g}" for g in missing_grants]
        status = report.status if not missing_grants else "partial"
        return _reply(
            MSG_STARTUP,
            request_id,
            {
                "status": status,
                "present": len(report.present),
                "total": len(manifest.objects),
                "missing": missing,
                "grants_file": "sql/grants.sql" if missing_grants else None,
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
