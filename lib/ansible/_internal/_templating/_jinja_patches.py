"""Runtime patches for Jinja bugs affecting Ansible."""

from __future__ import annotations

import jinja2
import jinja2.utils


def _patch_jinja_undefined_slots() -> None:
    """
    Fix the broken __slots__ on Jinja's Undefined and StrictUndefined if they're missing in the current version.
    This will no longer be necessary once the fix is included in the minimum supported Jinja version.
    See: https://github.com/pallets/jinja/issues/2025
    """
    if not hasattr(jinja2.Undefined, '__slots__'):
        jinja2.Undefined.__slots__ = (
            "_undefined_hint",
            "_undefined_obj",
            "_undefined_name",
            "_undefined_exception",
        )

    if not hasattr(jinja2.StrictUndefined, '__slots__'):
        jinja2.StrictUndefined.__slots__ = ()


def _patch_jinja_missing_type() -> None:
    """
    Fix the `jinja2.utils.missing` type to support pickling while remaining a singleton.
    This will no longer be necessary once the fix is included in the minimum supported Jinja version.
    See: https://github.com/pallets/jinja/issues/2027
    """
    if getattr(jinja2.utils.missing, '__reduce__')() != 'missing':

        def __reduce__(*_args):
            return 'missing'

        type(jinja2.utils.missing).__reduce__ = __reduce__


def _patch_jinja() -> None:
    """Apply Jinja2 patches."""
    _patch_jinja_undefined_slots()
    _patch_jinja_missing_type()
