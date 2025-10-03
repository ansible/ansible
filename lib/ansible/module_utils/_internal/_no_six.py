from __future__ import annotations

import sys
import types

from ansible.module_utils.common import warnings


# INLINED FROM THE SIX LIBRARY, see lib/ansible/module_utils/six/__init__.py
# Copyright (c) 2010-2024 Benjamin Peterson
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""

    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(type):

        def __new__(cls, name, this_bases, d):
            if sys.version_info[:2] >= (3, 7):
                # This version introduced PEP 560 that requires a bit
                # of extra care (we mimic what is done by __build_class__).
                resolved_bases = types.resolve_bases(bases)
                if resolved_bases is not bases:
                    d['__orig_bases__'] = bases
            else:
                resolved_bases = bases
            return meta(name, resolved_bases, d)

        @classmethod
        def __prepare__(cls, name, this_bases):
            return meta.__prepare__(name, bases)

    return type.__new__(metaclass, 'temporary_class', (), {})


def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""

    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        if hasattr(cls, '__qualname__'):
            orig_vars['__qualname__'] = cls.__qualname__
        return metaclass(cls.__name__, cls.__bases__, orig_vars)

    return wrapper


def iteritems(d, **kw):
    return iter(d.items(**kw))


_mini_six = {
    "PY2": False,
    "PY3": True,
    "text_type": str,
    "binary_type": bytes,
    "string_types": (str,),
    "integer_types": (int,),
    "iteritems": iteritems,
    "add_metaclass": add_metaclass,
    "with_metaclass": with_metaclass,
}
# INLINED SIX END


def deprecate(importable_name: str, module_name: str, *deprecated_args) -> object:
    """Inject import-time deprecation warnings."""
    if not (importable_name in deprecated_args and (importable := _mini_six.get(importable_name, ...) is not ...)):
        raise AttributeError(f"module {module_name!r} has no attribute {importable_name!r}")

    # TODO Inspect and remove all calls to this function in 2.24
    warnings.deprecate(
        msg=f"Importing {importable_name!r} from {module_name!r} is deprecated.",
        version="2.24",
    )

    return importable
