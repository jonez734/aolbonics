"""Who may do what in jargon.

The rule lives here, not in the database or the engine. ``access`` decides from the caller's
moniker and sysop status, and may consult anything jargon needs (a member flag, a list, a file).

Operations:
    lookup   read a term            anyone who reaches the bed
    create   add a term             sysop, or a member granted write access
    update   change a term          sysop, or a member granted write access

A caller with no moniker (not authenticated) is refused every write. Reads stay open.
"""

from __future__ import annotations

from typing import Any, Optional

READ_OPS = frozenset({"lookup"})
WRITE_OPS = frozenset({"create", "update"})

# The member flag that grants write access to jargon. Read by jargon, not defined in the engine.
WRITE_FLAG = "JARGON"


def _member_has_write_flag(args: Any, moniker: str) -> bool:
    """True when ``moniker`` holds the JARGON member flag. Imported lazily so the module loads
    without a database."""
    from bbsengine6 import member as libmember

    return libmember.checkflag(args, WRITE_FLAG, moniker=moniker) is True


def access(
    args: Any,
    op: str,
    *,
    moniker: Optional[str],
    is_sysop: bool = False,
    has_write_flag: Optional[bool] = None,
) -> bool:
    """Return True when ``moniker`` may perform ``op``.

    ``is_sysop`` is the authenticated sysop bit from bed's session. ``has_write_flag`` lets a caller
    (or a test) supply the flag result; when None, the JARGON flag is read from the database.
    """
    if op in READ_OPS:
        return True
    if op not in WRITE_OPS:
        return False
    if not moniker:
        return False
    if is_sysop:
        return True
    if has_write_flag is None:
        has_write_flag = _member_has_write_flag(args, moniker)
    return bool(has_write_flag)
