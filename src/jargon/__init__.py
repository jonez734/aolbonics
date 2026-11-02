"""jargon - glossary of BBS and internet slang.

bbsengine6's module loader (module.check) finds a module by its package and requires the contract below:
init, access, buildargs and main, with signatures that match bbsengine6.module's stubs. init registers the
module, so the registry knows jargon is loaded. Nothing in bed names jargon.
"""

import argparse

__version__ = "0.1.0"

MODULE_NAME = "jargon"
MODULE_PATH = "jargon.api.handler"


def init(args: argparse.Namespace, **kwargs: dict) -> bool | None:
    """Register jargon with bbsengine6 so the module registry reports it."""
    from bbsengine6 import register_module

    register_module(
        name=MODULE_NAME,
        module_path=MODULE_PATH,
        version=__version__,
        apis={},
    )
    return True


def buildargs(args: argparse.Namespace, **kwargs: dict) -> argparse.ArgumentParser | None:
    """jargon has no options of its own; bed's database flags apply."""
    return None


def main(args: argparse.Namespace, **kwargs: dict) -> bool | None:
    """Module entry point. jargon's work runs in the zoid6 sub-router (MODULE_PATH); this has nothing to run."""
    return True


def access(args: argparse.Namespace, op: str, **kwargs: dict) -> bool | None:
    """Per-request and load access (the module contract). The rule lives in jargon.rules."""
    from jargon.rules import access as _rule

    return _rule(args, op, **kwargs)
