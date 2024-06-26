# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Hold command line arguments for use in other modules
"""
from __future__ import annotations

from abc import ABCMeta
from collections.abc import Container, Mapping, Sequence, Set

from ansible.module_utils.common.collections import ImmutableDict
from ansible.module_utils.six import add_metaclass, binary_type, text_type
from ansible.utils.singleton import Singleton


def _make_immutable(obj):
    """Recursively convert a container and objects inside of it into immutable data types"""
    if isinstance(obj, (text_type, binary_type)):
        # Strings first because they are also sequences
        return obj
    elif isinstance(obj, Mapping):
        temp_dict = {}
        for key, value in obj.items():
            if isinstance(value, Container):
                temp_dict[key] = _make_immutable(value)
            else:
                temp_dict[key] = value
        return ImmutableDict(temp_dict)
    elif isinstance(obj, Set):
        temp_set = set()
        for value in obj:
            if isinstance(value, Container):
                temp_set.add(_make_immutable(value))
            else:
                temp_set.add(value)
        return frozenset(temp_set)
    elif isinstance(obj, Sequence):
        temp_sequence = []
        for value in obj:
            if isinstance(value, Container):
                temp_sequence.append(_make_immutable(value))
            else:
                temp_sequence.append(value)
        return tuple(temp_sequence)

    return obj


class _ABCSingleton(Singleton, ABCMeta):
    """
    Combine ABCMeta based classes with Singleton based classes

    Combine Singleton and ABCMeta so we have a metaclass that unambiguously knows which can override
    the other.  Useful for making new types of containers which are also Singletons.
    """
    pass


class CLIArgs(ImmutableDict):
    """
    Hold a parsed copy of cli arguments

    We have both this non-Singleton version and the Singleton, GlobalCLIArgs, version to leave us
    room to implement a Context object in the future.  Whereas there should only be one set of args
    in a global context, individual Context objects might want to pretend that they have different
    command line switches to trigger different behaviour when they run.  So if we support Contexts
    in the future, they would use CLIArgs instead of GlobalCLIArgs to store their version of command
    line flags.
    """
    def __init__(self, mapping):
        toplevel = {}
        for key, value in mapping.items():
            toplevel[key] = _make_immutable(value)
        super(CLIArgs, self).__init__(toplevel)

    @classmethod
    def from_options(cls, options):
        return cls(vars(options))


@add_metaclass(_ABCSingleton)
class GlobalCLIArgs(CLIArgs):
    """
    Globally hold a parsed copy of cli arguments.

    Only one of these exist per program as it is for global context
    """
    pass
