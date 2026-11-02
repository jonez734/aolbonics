"""Who may do what in jargon.

The rule lives here. ``access`` takes the operation and the caller's moniker, reads that member's
flags from the engine (the same record bbsengine6's member module builds), and decides. Jargon
owns the rule, so it can check whatever flags it needs without the engine defining them.

Operations:
    lookup   read a term            anyone who reaches the bed
    create   add a term             the sysop, or a member with the JARGON flag
    update   change a term          the sysop, or a member with the JARGON flag

No moniker means no identity, so every write is refused. Reads stay open.
"""

from __future__ import annotations

from typing import Any, Optional

READ_OPS = frozenset({"lookup"})
WRITE_OPS = frozenset({"create", "update"})

# The flags that decide a write. SYSOP is the engine's sysop flag; JARGON grants jargon writes.
SYSOP_FLAG = "SYSOP"
WRITE_FLAG = "JARGON"


def member_flags(args: Any, moniker: str, **kwargs: Any) -> set[str]:
    """The flag names currently set for ``moniker``, as a set of upper-case names.

    Read from the engine through bbsengine6's member module (the same source ``member.build`` uses).
    Imported here so the module loads without a database.
    """
    from bbsengine6 import member as libmember

    flags = libmember.getflags(args, moniker, **kwargs) or {}
    return {name.upper() for name, data in flags.items() if (data or {}).get("value") is True}


def access(args: Any, op: str, moniker: Optional[str], **kwargs: Any) -> bool:
    """Return True when ``moniker`` may perform ``op``.

    The caller passes only the operation and the moniker. Flags are read from the engine.
    """
    if op in READ_OPS:
        return True
    if op not in WRITE_OPS:
        return False
    if not moniker:
        return False
    flags = member_flags(args, moniker, **kwargs)
    return SYSOP_FLAG in flags or WRITE_FLAG in flags
