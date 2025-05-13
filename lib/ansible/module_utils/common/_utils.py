# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""
Modules in _utils are waiting to find a better home.  If you need to use them, be prepared for them
to move to a different location in the future.
"""

from __future__ import annotations

import inspect
import typing as t

_Type = t.TypeVar('_Type')


def get_all_subclasses(cls: type[_Type], *, include_abstract: bool = True, consider_self: bool = False) -> set[type[_Type]]:
    """Recursively find all subclasses of a given type, including abstract classes by default."""
    subclasses: set[type[_Type]] = {cls} if consider_self else set()
    queue: list[type[_Type]] = [cls]

    while queue:
        parent = queue.pop()

        for child in parent.__subclasses__():
            if child in subclasses:
                continue

            queue.append(child)
            subclasses.add(child)

    if not include_abstract:
        subclasses = {sc for sc in subclasses if not inspect.isabstract(sc)}

    return subclasses
