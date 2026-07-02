from __future__ import annotations

import abc
import typing as t

from contextvars import ContextVar

from ansible.module_utils._internal._datatag import AnsibleTagHelper


class NotifiableAccessContextBase(metaclass=abc.ABCMeta):
    """Base class for a context manager that, when active, receives notification of managed access for types/tags in which it has registered an interest."""

    _type_interest: t.FrozenSet[type] = frozenset()
    """Set of types (including tag types) for which this context will be notified upon access."""

    _mask: t.ClassVar[bool] = False
    """When true, only the innermost (most recently created) context of this type will be notified."""

    def __enter__(self):
        # noinspection PyProtectedMember
        AnsibleAccessContext.current()._register_interest(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # noinspection PyProtectedMember
        AnsibleAccessContext.current()._unregister_interest(self)
        return None

    @abc.abstractmethod
    def _notify(self, o: t.Any) -> t.Any:
        """Derived classes implement custom notification behavior when a registered type or tag is accessed."""


class AnsibleAccessContext:
    """
    Broker object for managed access registration and notification.
    Each thread or other logical callstack has a dedicated `AnsibleAccessContext` object with which `NotifiableAccessContext` objects can register interest.
    When a managed access occurs on an object, each active `NotifiableAccessContext` within the current callstack that has registered interest in that
    object's type or a tag present on it will be notified.
    """

    _contextvar: t.ClassVar[ContextVar[AnsibleAccessContext]] = ContextVar('AnsibleAccessContext')

    @staticmethod
    def current() -> AnsibleAccessContext:
        """Creates or retrieves an `AnsibleAccessContext` for the current logical callstack."""
        try:
            ctx: AnsibleAccessContext = AnsibleAccessContext._contextvar.get()
        except LookupError:
            # didn't exist; create it
            ctx = AnsibleAccessContext()
            AnsibleAccessContext._contextvar.set(ctx)  # we ignore the token, since this should live for the life of the thread/async ctx

        return ctx

    def __init__(self) -> None:
        self._notify_contexts: list[NotifiableAccessContextBase] = []

    def _register_interest(self, context: NotifiableAccessContextBase) -> None:
        self._notify_contexts.append(context)

    def _unregister_interest(self, context: NotifiableAccessContextBase) -> None:
        ctx = self._notify_contexts.pop()

        if ctx is not context:
            raise RuntimeError(f'Out-of-order context deactivation detected. Found {ctx} instead of {context}.')

    def access(self, value: t.Any) -> None:
        """Notify all contexts which have registered interest in the given value that it is being accessed."""
        if not self._notify_contexts:
            return

        value_types = AnsibleTagHelper.tag_types(value) | frozenset((type(value),))
        masked: set[type] = set()

        for ctx in reversed(self._notify_contexts):
            if ctx._mask:
                if (ctx_type := type(ctx)) in masked:
                    continue

                masked.add(ctx_type)

            # noinspection PyProtectedMember
            if ctx._type_interest.intersection(value_types):
                ctx._notify(value)
