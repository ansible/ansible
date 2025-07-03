from __future__ import annotations

import collections.abc as _c
import dataclasses
import typing as t

from ansible._internal._errors import _error_utils
from ansible.errors import AnsibleRuntimeError
from ansible.module_utils._internal import _messages


class AnsibleCapturedError(AnsibleRuntimeError):
    """An exception representing error detail captured in another context where the error detail must be serialized to be preserved."""

    context: t.ClassVar[str]

    def __init__(
        self,
        *,
        obj: t.Any = None,
        event: _messages.Event,
    ) -> None:
        super().__init__(
            obj=obj,
        )

        self._event = event


class AnsibleResultCapturedError(AnsibleCapturedError, _error_utils.ContributesToTaskResult):
    """
    An exception representing error detail captured in a foreign context where an action/module result dictionary is involved.

    This exception provides a result dictionary via the ContributesToTaskResult mixin.
    """

    def __init__(self, event: _messages.Event, result: dict[str, t.Any]) -> None:
        super().__init__(event=event)

        self._result = result

    @property
    def result_contribution(self) -> _c.Mapping[str, object]:
        return self._result

    @classmethod
    def maybe_raise_on_result(cls, result: dict[str, t.Any]) -> None:
        """Normalize the result and raise an exception if the result indicated failure."""
        if error_summary := cls.normalize_result_exception(result):
            raise error_summary.error_type(error_summary.event, result)

    @classmethod
    def normalize_result_exception(cls, result: dict[str, t.Any]) -> CapturedErrorSummary | None:
        """
        Normalize the result `exception`, if any, to be a `CapturedErrorSummary` instance.
        If a new `CapturedErrorSummary` was created, the `error_type` will be `cls`.
        The `exception` key will be removed if falsey.
        A `CapturedErrorSummary` instance will be returned if `failed` is truthy.
        """
        if type(cls) is AnsibleResultCapturedError:  # pylint: disable=unidiomatic-typecheck
            raise TypeError('The normalize_result_exception method cannot be called on the AnsibleCapturedError base type, use a derived type.')

        if not isinstance(result, dict):
            raise TypeError(f'Malformed result. Received {type(result)} instead of {dict}.')

        failed = result.get('failed')  # DTFIX-FUTURE: warn if failed is present and not a bool, or exception is present without failed being True
        exception = result.pop('exception', None)

        if not failed and not exception:
            return None

        if isinstance(exception, CapturedErrorSummary):
            error_summary = exception
        elif isinstance(exception, _messages.ErrorSummary):
            error_summary = CapturedErrorSummary(
                event=exception.event,
                error_type=cls,
            )
        else:
            # translate non-ErrorDetail errors
            error_summary = CapturedErrorSummary(
                event=_messages.Event(
                    msg=str(result.get('msg', 'Unknown error.')),
                    formatted_traceback=cls._normalize_traceback(exception),
                ),
                error_type=cls,
            )

        result.update(exception=error_summary)

        return error_summary if failed else None  # even though error detail was normalized, only return it if the result indicated failure

    @classmethod
    def _normalize_traceback(cls, value: object | None) -> str | None:
        """Normalize the provided traceback value, returning None if it is falsey."""
        if not value:
            return None

        value = str(value).rstrip()

        if not value:
            return None

        return value + '\n'


class AnsibleActionCapturedError(AnsibleResultCapturedError):
    """An exception representing error detail sourced directly by an action in its result dictionary."""

    _default_message = 'Action failed.'
    context = 'action'


class AnsibleModuleCapturedError(AnsibleResultCapturedError):
    """An exception representing error detail captured in a module context and returned from an action's result dictionary."""

    _default_message = 'Module failed.'
    context = 'target'


@dataclasses.dataclass(**_messages._dataclass_kwargs)
class CapturedErrorSummary(_messages.ErrorSummary):
    error_type: type[AnsibleResultCapturedError] | None = None
