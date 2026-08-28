from __future__ import annotations

import inspect
import sys

from ... import basic
from ..._internal import _secrets
from . import _respawn_wrapper


def create_payload() -> str:
    """Create and return an AnsiballZ payload for respawning a module."""
    main = sys.modules['__main__']
    code = inspect.getsource(_respawn_wrapper)

    ansible_args = basic._ANSIBLE_ARGS

    # This works on the assumption that the respawned process is in charge or
    # all output sent back to the controller. It'll take over registering of
    # new secrets and masking any output based on the input provided to it.
    secrets = _secrets._secret_masker.secrets_in(ansible_args.decode())

    args = dict(
        module_fqn=main._module_fqn,
        modlib_path=main._modlib_path,
        profile=basic._ANSIBLE_PROFILE,
        json_params=ansible_args,
        secrets=secrets,
    )

    args_string = '\n'.join(f'{key}={value!r},' for key, value in args.items())

    wrapper = f"""{code}

if __name__ == "__main__":
    _respawn_main(
{args_string}
)
"""

    return wrapper
