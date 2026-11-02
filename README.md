# aolbonics

`jargon` is a glossary of BBS and internet slang (`wtf`, `lart`, ...).

It is a bed client: the `jargon` command talks to a running bed daemon,
and the server side is a zoid6 sub-router (`jargon.api.handler`). There
is no direct database access from the command line.

See [`handbook/README.md`](handbook/README.md) for usage.

## Layout

    bin/jargon                    shell wrapper: python -m jargon
    src/jargon/__main__.py        CLI (--install, --startup, --help, lookup)
    src/jargon/client.py          BedConnection wrapper
    src/jargon/api/handler.py     zoid6 sub-router (MessageRouter)
    src/jargon/sql/               schema.sql, seed.sql, objects.json
    handbook/spec/                specifications
    handbook/todo/                todo items

## License

GPL-3.0-or-later.
