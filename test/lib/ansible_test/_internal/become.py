"""Become abstraction for interacting with test hosts."""

from __future__ import annotations

import abc
import shlex

from .util import (
    get_subclasses,
)


class Become(metaclass=abc.ABCMeta):
    """Base class for become implementations."""

    @classmethod
    def name(cls) -> str:
        """The name of this plugin."""
        return cls.__name__.lower()

    @property
    @abc.abstractmethod
    def method(self) -> str:
        """The name of the Ansible become plugin that is equivalent to this."""

    @abc.abstractmethod
    def prepare_command(self, command: list[str]) -> list[str]:
        """Return the given command, if any, with privilege escalation."""


class Doas(Become):
    """Become using 'doas'."""

    @property
    def method(self) -> str:
        """The name of the Ansible become plugin that is equivalent to this."""
        raise NotImplementedError('Ansible has no built-in doas become plugin.')

    def prepare_command(self, command: list[str]) -> list[str]:
        """Return the given command, if any, with privilege escalation."""
        become = ['doas', '-n']

        if command:
            become.extend(['sh', '-c', shlex.join(command)])
        else:
            become.extend(['-s'])

        return become


class DoasSudo(Doas):
    """Become using 'doas' in ansible-test and then after bootstrapping use 'sudo' for other ansible commands."""

    @classmethod
    def name(cls) -> str:
        """The name of this plugin."""
        return 'doas_sudo'

    @property
    def method(self) -> str:
        """The name of the Ansible become plugin that is equivalent to this."""
        return 'sudo'


class Su(Become):
    """Become using 'su'."""

    @property
    def method(self) -> str:
        """The name of the Ansible become plugin that is equivalent to this."""
        return 'su'

    def prepare_command(self, command: list[str]) -> list[str]:
        """Return the given command, if any, with privilege escalation."""
        become = ['su', '-l', 'root']

        if command:
            become.extend(['-c', shlex.join(command)])

        return become


class SuSudo(Su):
    """Become using 'su' in ansible-test and then after bootstrapping use 'sudo' for other ansible commands."""

    @classmethod
    def name(cls) -> str:
        """The name of this plugin."""
        return 'su_sudo'

    @property
    def method(self) -> str:
        """The name of the Ansible become plugin that is equivalent to this."""
        return 'sudo'


class Sudo(Become):
    """Become using 'sudo'."""

    @property
    def method(self) -> str:
        """The name of the Ansible become plugin that is equivalent to this."""
        return 'sudo'

    def prepare_command(self, command: list[str]) -> list[str]:
        """Return the given command, if any, with privilege escalation."""
        become = ['sudo', '-in']

        if command:
            become.extend(['sh', '-c', shlex.join(command)])

        return become


SUPPORTED_BECOME_METHODS = {cls.name(): cls for cls in get_subclasses(Become)}
