# Copyright (c) 2020 Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

from ansible.module_utils.common.warnings import deprecate


def __getattr__(importable_name):
    """Inject import-time deprecation warnings.

    Specifically, for ``import_module()``.
    """
    if importable_name == 'import_module':
        deprecate(
            msg=f'The `ansible.module_utils.compat.importlib.'
            f'{importable_name}` function is deprecated.',
            version='2.19',
        )
        from importlib import import_module
        return import_module

    raise AttributeError(
        f'cannot import name {importable_name !r} '
        f'has no attribute ({__file__ !s})',
    )
