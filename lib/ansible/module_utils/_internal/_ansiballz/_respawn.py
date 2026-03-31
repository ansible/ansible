from __future__ import annotations

import sys

from ... import basic


def create_payload() -> str:
    """Create and return an AnsiballZ payload for respawning a module."""
    main = sys.modules['__main__']
    wrapper_code = main._ansiballz_wrapper_source

    zip_bytes = main._ansiballz_zip_data
    encoded_params = basic._ANSIBLE_ARGS

    payload = f'''{wrapper_code}

if __name__ == '__main__':
    zip_data = {zip_bytes!r}
    encoded_params = {encoded_params!r}

    import sys
    sys.modules['__main__']._respawned = True
    sys.modules['__main__']._module_fqn = {main._module_fqn!r}
    sys.modules['__main__']._modlib_path = '<ansiballz>'

    invoke_module(zip_data, encoded_params)
'''

    return payload
