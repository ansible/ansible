# Copyright (c) 2024 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Internal error handling logic for targets. Not for use on the controller."""

from __future__ import annotations as _annotations

import traceback as _sys_traceback
import typing as _t

from . import _messages

MSG_REASON_DIRECT_CAUSE: _t.Final[str] = '<<< caused by >>>'
MSG_REASON_HANDLING_CAUSE: _t.Final[str] = '<<< while handling >>>'

TRACEBACK_REASON_EXCEPTION_DIRECT_WARNING: _t.Final[str] = 'The above exception was the direct cause of the following warning:'


class EventFactory:
    """Factory for creating `Event` instances from `BaseException` instances on targets."""

    _MAX_DEPTH = 10
    """Maximum exception chain depth. Exceptions beyond this depth will be omitted."""

    @classmethod
    def from_exception(cls, exception: BaseException, include_traceback: bool) -> _messages.Event:
        return cls(include_traceback)._convert_exception(exception)

    def __init__(self, include_traceback: bool) -> None:
        self._include_traceback = include_traceback
        self._depth = 0

    def _convert_exception(self, exception: BaseException) -> _messages.Event:
        if self._depth > self._MAX_DEPTH:
            return _messages.Event(
                msg="Maximum depth exceeded, omitting further events.",
            )

        self._depth += 1

        try:
            return _messages.Event(
                msg=self._get_msg(exception),
                formatted_traceback=self._get_formatted_traceback(exception),
                formatted_source_context=self._get_formatted_source_context(exception),
                help_text=self._get_help_text(exception),
                chain=self._get_chain(exception),
                events=self._get_events(exception),
            )
        finally:
            self._depth -= 1

    def _get_msg(self, exception: BaseException) -> str | None:
        return str(exception).strip()

    def _get_formatted_traceback(self, exception: BaseException) -> str | None:
        if self._include_traceback:
            return ''.join(_sys_traceback.format_exception(type(exception), exception, exception.__traceback__, chain=False))

        return None

    def _get_formatted_source_context(self, exception: BaseException) -> str | None:
        return None

    def _get_help_text(self, exception: BaseException) -> str | None:
        return None

    def _get_chain(self, exception: BaseException) -> _messages.EventChain | None:
        if cause := self._get_cause(exception):
            return _messages.EventChain(
                msg_reason=MSG_REASON_DIRECT_CAUSE,
                traceback_reason='The above exception was the direct cause of the following exception:',
                event=self._convert_exception(cause),
                follow=self._follow_cause(exception),
            )

        if context := self._get_context(exception):
            return _messages.EventChain(
                msg_reason=MSG_REASON_HANDLING_CAUSE,
                traceback_reason='During handling of the above exception, another exception occurred:',
                event=self._convert_exception(context),
                follow=False,
            )

        return None

    def _follow_cause(self, exception: BaseException) -> bool:
        return True

    def _get_cause(self, exception: BaseException) -> BaseException | None:
        return exception.__cause__

    def _get_context(self, exception: BaseException) -> BaseException | None:
        if exception.__suppress_context__:
            return None

        return exception.__context__

    def _get_events(self, exception: BaseException) -> tuple[_messages.Event, ...] | None:
        # deprecated: description='move BaseExceptionGroup support here from ControllerEventFactory' python_version='3.10'
        return None
