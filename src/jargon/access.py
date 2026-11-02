"""Who may do what in jargon.

The rule lives here. ``access`` takes the operation and the caller's moniker, reads that member's
flags from the engine (the same record bbsengine6's member module builds), and decides. Jargon
owns the rule, so it can check whatever flags it needs without the engine defining them.

Operations:
    run      load the module         module.check's load gate; no caller, so no moniker needed
    lookup   read a term             anyone who reaches the bed
    create   add a term              the sysop, or a member with the JARGON flag
    update   change a term           the sysop, or a member with the JARGON flag

No moniker means no identity, so every write is refused. Reads and the load gate stay open.
"""

from __future__ import annotations

from typing import Any, Optional

LOAD_OPS = frozenset({"run"})
READ_OPS = frozenset({"lookup"})
WRITE_OPS = frozenset({"create", "update"})

# The flags that decide a write. SYSOP is the engine's sysop flag; JARGON grants jargon writes.
SYSOP_FLAG = "SYSOP"
WRITE_FLAG = "JARGON"


def member_flags(args: Any, moniker: str, **kwargs: Any) -> set[str]:
    """The flag names set on ``moniker``'s member record, as upper-case names.

    Loads the record with bbsengine6's ``member.getbymoniker``. ``member.getcurrent`` is not used: it
    resolves the moniker from the process's OS login, which in the zoid6 daemon is the daemon's own
    account, not the bed client. The caller's moniker comes from bed's session. A pool is needed for
    the load; jargon takes one from ``database.getpool``. Imported here so the module loads without a
    database.
    """
    from bbsengine6 import database
    from bbsengine6 import member as libmember

    pool = kwargs.get("pool") or database.getpool(args)
    rec = libmember.getbymoniker(args, moniker, pool=pool)
    if not rec:
        return set()
    flags = rec.get("flags") or {}
    return {name.upper() for name, data in flags.items() if (data or {}).get("value") is True}


def access(args: Any, op: str, *, moniker: Optional[str] = None, **kwargs: Any) -> bool:
    """Return True when ``moniker`` may perform ``op``.

    The caller passes only the operation and the moniker. Flags are read from the engine. ``run`` is
    module.check's load gate: it has no caller, so it needs no moniker. Writes require one.
    """
    if op in LOAD_OPS or op in READ_OPS:
        return True
    if op not in WRITE_OPS:
        return False
    if not moniker:
        return False
    flags = member_flags(args, moniker, **kwargs)
    return SYSOP_FLAG in flags or WRITE_FLAG in flags
