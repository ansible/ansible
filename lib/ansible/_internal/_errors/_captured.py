from __future__ import annotations

import dataclasses
import typing as t

from ansible.errors import AnsibleRuntimeError
from ansible.module_utils.common.messages import ErrorSummary, Detail, _dataclass_kwargs


class AnsibleCapturedError(AnsibleRuntimeError):
    """An exception representing error detail captured in another context where the error detail must be serialized to be preserved."""

    context: t.ClassVar[str]  # DTFIX-MERGE: rename this and make it private since derived types may not be internal?

    def __init__(
        self,
        *,
        obj: t.Any = None,
        error_summary: ErrorSummary,
    ) -> None:
        super().__init__(
            obj=obj,
        )

        self._error_summary = error_summary

    @property
    def error_summary(self) -> ErrorSummary:
        return self._error_summary


class AnsibleResultCapturedError(AnsibleCapturedError):
    """An exception representing error detail captured in a foreign context where an action/module result dictionary is involved."""

    def __init__(self, error_summary: ErrorSummary, result: dict[str, t.Any]) -> None:
        super().__init__(error_summary=error_summary)

        self._result = result

    @classmethod
    def maybe_raise_on_result(cls, result: dict[str, t.Any]) -> None:
        """Normalize the result and raise an exception if the result indicated failure."""
        if error_summary := cls.normalize_result_exception(result):
            raise error_summary.error_type(error_summary, result)

    @classmethod
    def find_first_remoted_error(cls, exception: BaseException) -> t.Self | None:
        """Find the first captured module error in the cause chain, starting with the given exception, returning None if not found."""
        while exception:
            if isinstance(exception, cls):
                return exception

            exception = exception.__cause__

        return None

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
        elif isinstance(exception, ErrorSummary):
            error_summary = CapturedErrorSummary(
                details=exception.details,
                formatted_traceback=cls._normalize_traceback(exception.formatted_traceback),
                error_type=cls,
            )
        else:
            # translate non-ErrorDetail errors
            error_summary = CapturedErrorSummary(
                details=(Detail(msg=str(result.get('msg', 'Unknown error.'))),),
                formatted_traceback=cls._normalize_traceback(exception),
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

    default_message = 'Action failed.'
    context = 'action'


class AnsibleModuleCapturedError(AnsibleResultCapturedError):
    """An exception representing error detail captured in a module context and returned from an action's result dictionary."""

    default_message = 'Module failed.'
    context = 'target'


@dataclasses.dataclass(**_dataclass_kwargs)
class CapturedErrorSummary(ErrorSummary):
    # DTFIX-MERGE: where to put this, name, etc. since it shows up in results, it's not exactly private (and contains a type ref to an internal type)
    error_type: type[AnsibleResultCapturedError] | None = None
