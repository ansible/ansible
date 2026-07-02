from __future__ import annotations

import inspect
import sys

from ... import basic
from . import _respawn_wrapper


def create_payload() -> str:
    """Create and return an AnsiballZ payload for respawning a module."""
    main = sys.modules['__main__']
    code = inspect.getsource(_respawn_wrapper)

    args = dict(
        module_fqn=main._module_fqn,
        modlib_path=main._modlib_path,
        profile=basic._ANSIBLE_PROFILE,
        json_params=basic._ANSIBLE_ARGS,
    )

    args_string = '\n'.join(f'{key}={value!r},' for key, value in args.items())

    wrapper = f"""{code}

if __name__ == "__main__":
    _respawn_main(
{args_string}
)
"""

    return wrapper
