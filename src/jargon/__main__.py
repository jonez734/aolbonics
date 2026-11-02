"""jargon command line.

    jargon --help        show usage (does not need bed)
    jargon --install     create the jargon schema and load seed terms
    jargon --startup     check that every object in sql/objects.json exists
    jargon <term>        print one term
    jargon               print usage

Everything except --help talks to a running bed daemon. The database is
configured by bed (zoid6.json), not by this command.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from jargon import __version__
from jargon import client
from jargon.client import JargonError


def buildparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jargon",
        description="Glossary of BBS and internet slang, served through bed.",
    )
    parser.add_argument("--version", action="version", version=f"jargon {__version__}")
    parser.add_argument("--install", action="store_true", help="create the jargon schema and load seed terms")
    parser.add_argument(
        "--startup",
        action="store_true",
        help="check that every jargon object exists; exit 1 if not installed or partial",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="create a term; requires --slug, --term, --definition (--origin optional)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="update a term; requires --slug and at least one of --term, --definition, --origin",
    )
    parser.add_argument("--slug", help="term slug, e.g. wtf")
    parser.add_argument("--term", dest="term_field", metavar="TERM", help="display name for --create/--update")
    parser.add_argument("--definition", help="definition for --create/--update")
    parser.add_argument("--origin", help="origin for --create/--update (use an empty string to clear)")
    parser.add_argument("term", nargs="?", help="term to look up, e.g. wtf")
    return parser


def _print_usage(parser: argparse.ArgumentParser) -> None:
    parser.print_help()


def _run(argv: Optional[List[str]], parser: argparse.ArgumentParser) -> int:
    args = parser.parse_args(argv)

    modes = [m for m in ("install", "startup", "create", "update") if getattr(args, m)]
    if len(modes) > 1:
        parser.error(f"--{modes[0]} and --{modes[1]} cannot be used together")
    if modes and args.term:
        parser.error(f"a term cannot be given with --{modes[0]}")

    if args.create:
        if not args.slug or not args.term_field or not args.definition:
            parser.error("--create requires --slug, --term and --definition")
        reply = client.create(args, args.slug, args.term_field, args.definition, args.origin)
        print(f"created {reply['term']['slug']}")
        return 0

    if args.update:
        if not args.slug:
            parser.error("--update requires --slug")
        fields = {}
        if args.term_field is not None:
            fields["term"] = args.term_field
        if args.definition is not None:
            fields["definition"] = args.definition
        if args.origin is not None:
            fields["origin"] = args.origin or None
        if not fields:
            parser.error("--update needs at least one of --term, --definition, --origin")
        reply = client.update(args, args.slug, **fields)
        print(f"updated {reply['term']['slug']}")
        return 0

    if args.install:
        reply = client.install(args)
        print(reply.get("message", "jargon installed"))
        return 0

    if args.startup:
        reply = client.startup(args)
        status = reply.get("status", "unknown")
        print(f"jargon objects: {status} ({reply.get('present', '?')}/{reply.get('total', '?')})")
        for label in reply.get("missing", []):
            print(f"  missing: {label}", file=sys.stderr)
        return 0 if status == "installed" else 1

    if args.term:
        reply = client.lookup(args, args.term)
        term = reply.get("term")
        if not term:
            print(f"jargon: no entry for {args.term!r}", file=sys.stderr)
            return 1
        print(f"{term['term']}: {term['definition']}")
        if term.get("origin"):
            print(f"  origin: {term['origin']}")
        return 0

    _print_usage(parser)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = buildparser()
    try:
        return _run(argv, parser)
    except JargonError as exc:
        print(f"jargon: {exc}", file=sys.stderr)
        return 1


def _main() -> None:
    sys.exit(main())


if __name__ == "__main__":
    _main()
