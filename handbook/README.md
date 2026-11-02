# jargon handbook

`jargon` is a glossary of slang and jargon. Terms are stored in the
`zoid6` database under the `jargon` schema.

## Commands

    jargon --help       show usage (works without bed)
    jargon --install    create the jargon schema and load seed terms
    jargon --startup    check that every object in sql/objects.json exists
                        exits 1 if the status is "not installed" or "partial"
    jargon <term>       print one term, e.g. `jargon wtf`
    jargon              print usage

All commands except `--help` require a running bed daemon. If bed is
not reachable, jargon exits nonzero with a message.

## Layout

    spec/   specifications
    todo/   todo items

## Database

The schema is `jargon`, created in the database configured for zoid6
(`zoid6.json` `database.name`). Terms are stored in `jargon.__terms`
with `datecreated` and `dateupdated` as `timestamptz`. The `jargon.terms`
view adds the same dates converted to the member's time zone.
