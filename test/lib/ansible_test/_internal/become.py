"""Become abstraction for interacting with test hosts."""
from __future__ import annotations

import abc
import shlex
import typing as t


class Become(metaclass=abc.ABCMeta):
    """Base class for become implementations."""
    @abc.abstractmethod
    def prepare_command(self, command):  # type: (t.List[str]) -> t.List[str]
        """Return the given command, if any, with privilege escalation."""


class Su(Become):
    """Become using 'su'."""
    def prepare_command(self, command):  # type: (t.List[str]) -> t.List[str]
        """Return the given command, if any, with privilege escalation."""
        become = ['su', '-l', 'root']

        if command:
            become.extend(['-c', ' '.join(shlex.quote(c) for c in command)])

        return become


class Sudo(Become):
    """Become using 'sudo'."""
    def prepare_command(self, command):  # type: (t.List[str]) -> t.List[str]
        """Return the given command, if any, with privilege escalation."""
        become = ['sudo', '-in']

        if command:
            become.extend(['sh', '-c', ' '.join(shlex.quote(c) for c in command)])

        return become
