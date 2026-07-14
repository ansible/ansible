"""Patches for builtin socket module."""

from __future__ import annotations

import contextlib
import socket
import typing as t

from . import CallablePatch


class _CustomInt(int):
    """Wrapper around `int` to test if subclasses are accepted."""


class GetAddrInfoPatch(CallablePatch):
    """Patch `socket.getaddrinfo` so that its `port` arg works with `int` subclasses."""

    target_container: t.ClassVar = socket
    target_attribute = 'getaddrinfo'

    @classmethod
    def is_patch_needed(cls) -> bool:
        with contextlib.suppress(OSError):
            socket.getaddrinfo('127.0.0.1', _CustomInt(22))
            return False

        return True

    def __call__(self, host, port, *args, **kwargs) -> t.Any:
        if type(port) is not int and isinstance(port, int):  # pylint: disable=unidiomatic-typecheck
            port = int(port)

        return type(self).unpatched_implementation(host, port, *args, **kwargs)
