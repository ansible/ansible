from __future__ import annotations

import abc
import collections.abc as _c
import dataclasses
import itertools
import pathlib
import textwrap
import typing as t

from ansible._internal._datatag._tags import Origin
from ansible._internal._errors import _error_factory
from ansible.module_utils._internal import _ambient_context, _event_utils, _messages, _traceback


class ContributesToTaskResult(metaclass=abc.ABCMeta):
    """Exceptions may include this mixin to contribute task result dictionary data directly to the final result."""

    @property
    @abc.abstractmethod
    def result_contribution(self) -> _c.Mapping[str, object]:
        """Mapping of results to apply to the task result."""

    @property
    def omit_exception_key(self) -> bool:
        """Non-error exceptions (e.g., `AnsibleActionSkip`) must return `True` to ensure omission of the `exception` key."""
        return False

    @property
    def omit_failed_key(self) -> bool:
        """Exceptions representing non-failure scenarios (e.g., `skipped`, `unreachable`) must return `True` to ensure omisson of the `failed` key."""
        return False


class RedactAnnotatedSourceContext(_ambient_context.AmbientContextBase):
    """When active, this context will redact annotated source lines, showing only the origin."""


@dataclasses.dataclass(kw_only=True, frozen=True)
class SourceContext:
    origin: Origin
    annotated_source_lines: list[str]
    target_line: str | None

    def __str__(self) -> str:
        msg_lines = [f'Origin: {self.origin}']

        if self.annotated_source_lines:
            msg_lines.append('')
            msg_lines.extend(self.annotated_source_lines)

        return '\n'.join(msg_lines)

    @classmethod
    def from_value(cls, value: t.Any) -> SourceContext | None:
        """Attempt to retrieve source and render a contextual indicator from the value's origin (if any)."""
        if value is None:
            return None

        if isinstance(value, Origin):
            origin = value
            value = None
        else:
            origin = Origin.get_tag(value)

        if RedactAnnotatedSourceContext.current(optional=True):
            return cls.error('content redacted')

        if origin and origin.path:
            return cls.from_origin(origin)

        if value is None:
            truncated_value = None
            annotated_source_lines = []
        else:
            # DTFIX-FUTURE: cleanup/share width
            try:
                value = str(value)
            except Exception as ex:
                value = f'<< context unavailable: {ex} >>'

            truncated_value = textwrap.shorten(value, width=120)
            annotated_source_lines = [truncated_value]

        return SourceContext(
            origin=origin or Origin.UNKNOWN,
            annotated_source_lines=annotated_source_lines,
            target_line=truncated_value,
        )

    @staticmethod
    def error(message: str | None, origin: Origin | None = None) -> SourceContext:
        return SourceContext(
            origin=origin,
            annotated_source_lines=[f'(source not shown: {message})'] if message else [],
            target_line=None,
        )

    @classmethod
    def from_origin(cls, origin: Origin) -> SourceContext:
        """Attempt to retrieve source and render a contextual indicator of an error location."""
        from ansible.parsing.vault import is_encrypted  # avoid circular import

        # DTFIX-FUTURE: support referencing the column after the end of the target line, so we can indicate where a missing character (quote) needs to be added
        #               this is also useful for cases like end-of-stream reported by the YAML parser

        # DTFIX-FUTURE: Implement line wrapping and match annotated line width to the terminal display width.

        context_line_count: t.Final = 2
        max_annotated_line_width: t.Final = 120
        truncation_marker: t.Final = '...'

        target_line_num = origin.line_num

        if RedactAnnotatedSourceContext.current(optional=True):
            return cls.error('content redacted', origin)

        if not target_line_num or target_line_num < 1:
            return cls.error(None, origin)  # message omitted since lack of line number is obvious from pos

        start_line_idx = max(0, (target_line_num - 1) - context_line_count)  # if near start of file
        target_col_num = origin.col_num

        try:
            with pathlib.Path(origin.path).open() as src:
                first_line = src.readline()
                lines = list(itertools.islice(itertools.chain((first_line,), src), start_line_idx, target_line_num))
        except Exception as ex:
            return cls.error(type(ex).__name__, origin)

        if is_encrypted(first_line):
            return cls.error('content encrypted', origin)

        if len(lines) != target_line_num - start_line_idx:
            return cls.error('file truncated', origin)

        annotated_source_lines = []

        line_label_width = len(str(target_line_num))
        max_src_line_len = max_annotated_line_width - line_label_width - 1

        usable_line_len = max_src_line_len

        for line_num, line in enumerate(lines, start_line_idx + 1):
            line = line.rstrip('\n')  # universal newline default mode on `open` ensures we'll never see anything but \n
            line = line.replace('\t', ' ')  # mixed tab/space handling is intentionally disabled since we're both format and display config agnostic

            if len(line) > max_src_line_len:
                line = line[: max_src_line_len - len(truncation_marker)] + truncation_marker
                usable_line_len = max_src_line_len - len(truncation_marker)

            annotated_source_lines.append(f'{str(line_num).rjust(line_label_width)}{" " if line else ""}{line}')

        if target_col_num and usable_line_len >= target_col_num >= 1:
            column_marker = f'column {target_col_num}'

            target_col_idx = target_col_num - 1

            if target_col_idx + 2 + len(column_marker) > max_src_line_len:
                column_marker = f'{" " * (target_col_idx - len(column_marker) - 1)}{column_marker} ^'
            else:
                column_marker = f'{" " * target_col_idx}^ {column_marker}'

            column_marker = f'{" " * line_label_width} {column_marker}'

            annotated_source_lines.append(column_marker)
        elif target_col_num is None:
            underline_length = len(annotated_source_lines[-1]) - line_label_width - 1
            annotated_source_lines.append(f'{" " * line_label_width} {"^" * underline_length}')

        return SourceContext(
            origin=origin,
            annotated_source_lines=annotated_source_lines,
            target_line=lines[-1].rstrip('\n'),  # universal newline default mode on `open` ensures we'll never see anything but \n
        )


def format_exception_message(exception: BaseException) -> str:
    """Return the full chain of exception messages by concatenating the cause(s) until all are exhausted."""
    return _event_utils.format_event_brief_message(_error_factory.ControllerEventFactory.from_exception(exception, False))


def result_dict_from_exception(exception: BaseException, accept_result_contribution: bool = False) -> dict[str, object]:
    """Return a failed task result dict from the given exception."""
    event = _error_factory.ControllerEventFactory.from_exception(exception, _traceback.is_traceback_enabled(_traceback.TracebackEvent.ERROR))

    result: dict[str, object] = {}
    omit_failed_key = False
    omit_exception_key = False

    if accept_result_contribution:
        while exception:
            if isinstance(exception, ContributesToTaskResult):
                result = dict(exception.result_contribution)
                omit_failed_key = exception.omit_failed_key
                omit_exception_key = exception.omit_exception_key
                break

            exception = exception.__cause__

    if omit_failed_key:
        result.pop('failed', None)
    else:
        result.update(failed=True)

    if omit_exception_key:
        result.pop('exception', None)
    else:
        result.update(exception=_messages.ErrorSummary(event=event))

    if 'msg' not in result:
        # if nothing contributed `msg`, generate one from the exception messages
        result.update(msg=_event_utils.format_event_brief_message(event))

    return result


def result_dict_from_captured_errors(
    msg: str,
    *,
    errors: list[_messages.ErrorSummary] | None = None,
) -> dict[str, object]:
    """Return a failed task result dict from the given error message and captured errors."""
    _skip_stackwalk = True

    event = _messages.Event(
        msg=msg,
        formatted_traceback=_traceback.maybe_capture_traceback(msg, _traceback.TracebackEvent.ERROR),
        events=tuple(error.event for error in errors) if errors else None,
    )

    result = dict(
        failed=True,
        exception=_messages.ErrorSummary(
            event=event,
        ),
        msg=_event_utils.format_event_brief_message(event),
    )

    return result
