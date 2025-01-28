# DTFIX-MERGE: this is part of the new DT changes, the API needs additional cleanup before releasing

from __future__ import annotations

import dataclasses
import itertools
import pathlib
import sys
import textwrap
import typing as t

from ..module_utils.common.messages import Detail, ErrorSummary
from ..utils.datatag.tags import AnsibleSourcePosition
from ..module_utils._internal import _ambient_context, _traceback

if t.TYPE_CHECKING:
    from ..utils.display import Display


class RedactAnnotatedSourceContext(_ambient_context.AmbientContextBase):
    """
    When active, this context will redact annotated source lines, showing only source position.
    """


def _dedupe_and_concat_message_chain(message_parts: list[str]) -> str:
    message_parts = list(reversed(message_parts))

    message = message_parts.pop(0)

    for message_part in message_parts:
        # avoid duplicate messages where the cause was already concatenated to the exception message
        if message_part.endswith(message):
            message = message_part
        else:
            message = concat_message(message_part, message)

    return message


def _collapse_error_details(error_details: t.Sequence[Detail]) -> list[Detail]:
    """
    Return a potentially modified error chain, with redundant errors collapsed into previous error(s) in the chain.
    This reduces the verbosity of messages by eliminating repetition when multiple errors in the chain share the same contextual information.
    """
    previous_error = error_details[0]
    previous_warnings: list[str] = []
    collapsed_error_details: list[tuple[Detail, list[str]]] = [(previous_error, previous_warnings)]

    for error in error_details[1:]:
        details_present = error.formatted_source_context or error.help_text
        details_changed = error.formatted_source_context != previous_error.formatted_source_context or error.help_text != previous_error.help_text

        if details_present and details_changed:
            previous_error = error
            previous_warnings = []
            collapsed_error_details.append((previous_error, previous_warnings))
        else:
            previous_warnings.append(error.msg)

    final_error_details: list[Detail] = []

    for error, messages in collapsed_error_details:
        final_error_details.append(dataclasses.replace(error, msg=_dedupe_and_concat_message_chain([error.msg] + messages)))

    return final_error_details


def _get_cause(exception: BaseException) -> BaseException | None:
    # deprecated: description='remove support for orig_exc (should have been deprecated in 2.22)' core_version='2.26'

    from . import AnsibleError

    if not isinstance(exception, AnsibleError):
        return exception.__cause__

    if exception.__cause__:
        if exception.orig_exc and exception.orig_exc is not exception.__cause__:
            _get_display().warning(
                msg=f"The `orig_exc` argument to `{type(exception).__name__}` was given, but differed from the cause given by `raise ... from`.",
            )

        return exception.__cause__

    if exception.orig_exc:
        # encourage the use of `raise ... from` before deprecating `orig_exc`
        _get_display().warning(msg=f"The `orig_exc` argument to `{type(exception).__name__}` was given without using `raise ... from orig_exc`.")

        return exception.orig_exc

    return None


class _TemporaryDisplay:
    # DTFIX-FUTURE: generalize this and hide it in the display module so all users of Display can benefit

    @staticmethod
    def warning(*args, **kwargs):
        print(f'FALLBACK WARNING: {args} {kwargs}', file=sys.stderr)

    @staticmethod
    def deprecated(*args, **kwargs):
        print(f'FALLBACK DEPRECATION: {args} {kwargs}', file=sys.stderr)


def _get_display() -> Display | _TemporaryDisplay:
    try:
        from ..utils.display import Display
    except ImportError:
        return _TemporaryDisplay()

    return Display()


def _create_error_summary(exception: BaseException, event: _traceback.TracebackEvent | None = None) -> ErrorSummary:
    # DTFIX-MERGE: can this be moved to _internal._errors?
    from . import AnsibleError
    from .._internal import _errors

    current_exception: BaseException | None = exception
    error_details: list[Detail] = []

    if event:
        formatted_traceback = _traceback.maybe_extract_traceback(exception, event)
    else:
        formatted_traceback = None

    while current_exception:
        if isinstance(current_exception, AnsibleError):
            include_cause_message = current_exception.include_cause_message
            edc = Detail(
                msg=current_exception.original_message.strip(),
                formatted_source_context=current_exception.formatted_source_context,
                help_text=current_exception.help_text,
            )
        else:
            include_cause_message = True
            edc = Detail(
                msg=str(current_exception).strip(),
            )

        error_details.append(edc)

        if isinstance(current_exception, _errors.AnsibleCapturedError):
            detail = current_exception.error_summary
            error_details.extend(detail.details)

            if formatted_traceback and detail.formatted_traceback:
                formatted_traceback = (
                    f'{detail.formatted_traceback}\n'
                    f'The {current_exception.context} exception above was the direct cause of the following controller exception:\n\n'
                    f'{formatted_traceback}'
                )

        if not include_cause_message:
            break

        current_exception = _get_cause(current_exception)

    return ErrorSummary(details=tuple(error_details), formatted_traceback=formatted_traceback)


def concat_message(left: str, right: str) -> str:
    """Normalize `left` by removing trailing punctuation and spaces before appending new punctuation and `right`."""
    return f'{left.rstrip(". ")}: {right}'


def get_chained_message(exception: BaseException) -> str:
    """
    Return the full chain of exception messages by concatenating the cause(s) until all are exhausted.
    """
    error_summary = _create_error_summary(exception)
    message_parts = [edc.msg for edc in error_summary.details]

    return _dedupe_and_concat_message_chain(message_parts)


@dataclasses.dataclass(kw_only=True, frozen=True)
class SourceContext:
    source_position: AnsibleSourcePosition
    annotated_source_lines: list[str]
    target_line: str | None

    def __str__(self) -> str:
        msg_lines = [f'Origin: {self.source_position}']

        if self.annotated_source_lines:
            msg_lines.append('')
            msg_lines.extend(self.annotated_source_lines)

        return '\n'.join(msg_lines)

    @classmethod
    def from_value(cls, value: t.Any) -> SourceContext | None:
        """Attempt to retrieve source and render a contextual indicator from the value's source position (if any)."""
        if value is None:
            return None

        if isinstance(value, AnsibleSourcePosition):
            position = value
            value = None
        else:
            position = AnsibleSourcePosition.get_tag(value)

        if RedactAnnotatedSourceContext.current(optional=True):
            return cls.error('content redacted')

        if position and position.src:
            return cls.from_source_position(position)

        # DTFIX-RELEASE: redaction context may not be sufficient to avoid secret disclosure without SensitiveData and other enhancements
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
            source_position=position or AnsibleSourcePosition.UNKNOWN,
            annotated_source_lines=annotated_source_lines,
            target_line=truncated_value,
        )

    @staticmethod
    def error(message: str | None, position: AnsibleSourcePosition | None = None) -> SourceContext:
        return SourceContext(
            source_position=position,
            annotated_source_lines=[f'(source not shown: {message})'] if message else [],
            target_line=None,
        )

    @classmethod
    def from_source_position(cls, position: AnsibleSourcePosition) -> SourceContext:
        """Attempt to retrieve source and render a contextual indicator of an error location."""
        from ..parsing.vault import is_encrypted

        # DTFIX-FUTURE: support referencing the column after the end of the target line, so we can indicate where a missing character (quote) needs to be added
        #               this is also useful for cases like end-of-stream reported by the YAML parser

        # DTFIX-FUTURE: Implement line wrapping and match annotated line width to the terminal display width.

        context_line_count: t.Final = 2
        max_annotated_line_width: t.Final = 120
        truncation_marker: t.Final = '...'

        target_line_num = position.line

        if RedactAnnotatedSourceContext.current(optional=True):
            return cls.error('content redacted', position)

        if not target_line_num or target_line_num < 1:
            return cls.error(None, position)  # message omitted since lack of line number is obvious from pos

        start_line_idx = max(0, (target_line_num - 1) - context_line_count)  # if near start of file
        target_col_num = position.col

        try:
            with pathlib.Path(position.src).open() as src:
                first_line = src.readline()
                lines = list(itertools.islice(itertools.chain((first_line,), src), start_line_idx, target_line_num))
        except Exception as ex:
            return cls.error(type(ex).__name__, position)

        if is_encrypted(first_line):
            return cls.error('content encrypted', position)

        if len(lines) != target_line_num - start_line_idx:
            return cls.error('file truncated', position)

        annotated_source_lines = []

        line_label_width = len(str(target_line_num))
        max_src_line_len = max_annotated_line_width - line_label_width - 1

        usable_line_len = max_src_line_len

        for line_num, line in enumerate(lines, start_line_idx + 1):
            line = line.rstrip('\n')  # universal newline default mode on `open` ensures we'll never see anything but \n
            line = line.replace('\t', ' ')  # mixed tab/space handling is intentionally disabled since we're both format and display config agnostic

            if len(line) > max_src_line_len:
                line = line[:max_src_line_len - len(truncation_marker)] + truncation_marker
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

        return SourceContext(
            source_position=position,
            annotated_source_lines=annotated_source_lines,
            target_line=lines[-1].rstrip('\n'),  # universal newline default mode on `open` ensures we'll never see anything but \n
        )
