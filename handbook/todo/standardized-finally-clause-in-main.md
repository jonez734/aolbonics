# standardized finally clause in main — aolbonics

Every program's `finally` on exit should call `bottombar.shutdown()`, and every program's setup
should call `bottombar.init()`. Neither should use the deprecated `screen.init()` shim or a private
once-per-process flag.

Contract (bbsengine6 `bottombar`):
- `init()` runs once per process, and sets the scroll region on a tty only.
- `shutdown()` shuts down object fragments first, then, only if `init()` ran, clears the bottom bar line,
  resets colors and margins (`{reset}`), and restores the cursor. It never raises and does nothing without
  a tty.
- Interrupt and EOF messages print `{/all}*INTR*` / `{/all}*EOF*` with no cursor restore in the text, so
  `shutdown()` restores the cursor after the message.

Verify by driving the program under a pty, interrupting it, and checking that the exit bytes end in this
order: color reset, message, bar-line clear, color reset, margin reset, cursor restore.

## Open

- [ ] The `jargon` CLI (`src/jargon/__main__.py`) prints plain output and never calls `bottombar.init()`. Confirm it needs no screen setup. Record that as the result, or add a `finally` with `bottombar.shutdown()` if an interactive path is added later.
- [ ] Confirm the `auth` interactive prompt used by `jargon` (through `bed.tools.auth`) is covered by bed's `finally`, not duplicated here.
