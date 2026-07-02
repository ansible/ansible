from __future__ import annotations as _annotations

from ansible.module_utils._internal import _errors, _messages


class ControllerEventFactory(_errors.EventFactory):
    """Factory for creating `Event` instances from `BaseException` instances on the controller."""

    def _get_msg(self, exception: BaseException) -> str | None:
        from ansible.errors import AnsibleError

        if not isinstance(exception, AnsibleError):
            return super()._get_msg(exception)

        return exception._original_message.strip()

    def _get_formatted_source_context(self, exception: BaseException) -> str | None:
        from ansible.errors import AnsibleError

        if not isinstance(exception, AnsibleError):
            return super()._get_formatted_source_context(exception)

        return exception._formatted_source_context

    def _get_help_text(self, exception: BaseException) -> str | None:
        from ansible.errors import AnsibleError

        if not isinstance(exception, AnsibleError):
            return super()._get_help_text(exception)

        return exception._help_text

    def _get_chain(self, exception: BaseException) -> _messages.EventChain | None:
        from ansible._internal._errors import _captured  # avoid circular import due to AnsibleError import

        if isinstance(exception, _captured.AnsibleCapturedError):
            # a captured error provides its own cause event, it never has a normal __cause__
            return _messages.EventChain(
                msg_reason=_errors.MSG_REASON_DIRECT_CAUSE,
                traceback_reason=f'The above {exception.context} exception was the direct cause of the following controller exception:',
                event=exception._event,
            )

        return super()._get_chain(exception)

    def _follow_cause(self, exception: BaseException) -> bool:
        from ansible.errors import AnsibleError

        return not isinstance(exception, AnsibleError) or exception._include_cause_message

    def _get_cause(self, exception: BaseException) -> BaseException | None:
        # deprecated: description='remove support for orig_exc (deprecated in 2.23)' core_version='2.27'

        cause = super()._get_cause(exception)

        from ansible.errors import AnsibleError

        if not isinstance(exception, AnsibleError):
            return cause

        try:
            from ansible.utils.display import _display
        except Exception:  # pylint: disable=broad-except  # if config is broken, this can raise things other than ImportError
            _display = None

        if cause:
            if exception.orig_exc and exception.orig_exc is not cause and _display:
                _display.warning(
                    msg=f"The `orig_exc` argument to `{type(exception).__name__}` was given, but differed from the cause given by `raise ... from`.",
                )

            return cause

        if exception.orig_exc:
            if _display:
                # encourage the use of `raise ... from` before deprecating `orig_exc`
                _display.warning(
                    msg=f"The `orig_exc` argument to `{type(exception).__name__}` was given without using `raise ... from orig_exc`.",
                )

            return exception.orig_exc

        return None

    def _get_events(self, exception: BaseException) -> tuple[_messages.Event, ...] | None:
        if isinstance(exception, BaseExceptionGroup):
            return tuple(self._convert_exception(ex) for ex in exception.exceptions)

        return None
