from __future__ import annotations

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    """Specialized config lookup that applies data transformations on values that config cannot."""

    def run(self, terms, variables=None, **kwargs):
        if not terms or not (config_name := terms[0]):
            raise ValueError("config name is required")

        match config_name:
            case 'DISPLAY_TRACEBACK':
                # since config can't expand this yet, we need the post-processed version
                from ansible.module_utils._internal._traceback import traceback_for

                return traceback_for()
            # DTFIX-FUTURE: plumb through normal config fallback
            case _:
                raise ValueError(f"Unknown config name {config_name!r}.")
