from __future__ import annotations as _annotations

import collections.abc as _c
import textwrap as _textwrap

from ansible.module_utils._internal import _event_utils, _messages


def format_event(event: _messages.Event, include_traceback: bool) -> str:
    """Format an event into a verbose message and traceback."""
    msg = format_event_verbose_message(event)

    if include_traceback:
        msg += '\n' + format_event_traceback(event)

    msg = msg.strip()

    if '\n' in msg:
        msg += '\n\n'
    else:
        msg += '\n'

    return msg


def format_event_traceback(event: _messages.Event) -> str:
    """Format an event into a traceback."""
    segments: list[str] = []

    while event:
        segment = event.formatted_traceback or '(traceback missing)\n'

        if event.events:
            child_tracebacks = [format_event_traceback(child) for child in event.events]
            segment += _format_event_children("Sub-Traceback", child_tracebacks)

        segments.append(segment)

        if event.chain:
            segments.append(f'\n{event.chain.traceback_reason}\n\n')

            event = event.chain.event
        else:
            event = None

    return ''.join(reversed(segments))


def format_event_verbose_message(event: _messages.Event) -> str:
    """
    Format an event into a verbose message.
    Help text, contextual information and sub-events will be included.
    """
    segments: list[str] = []
    original_event = event

    while event:
        messages = [event.msg]
        chain: _messages.EventChain = event.chain

        while chain and chain.follow:
            if chain.event.events:
                break  # do not collapse a chained event with sub-events, since they would be lost

            if chain.event.formatted_source_context or chain.event.help_text:
                if chain.event.formatted_source_context != event.formatted_source_context or chain.event.help_text != event.help_text:
                    break  # do not collapse a chained event with different details, since they would be lost

            if chain.event.chain and chain.msg_reason != chain.event.chain.msg_reason:
                break  # do not collapse a chained event which has a chain with a different msg_reason

            messages.append(chain.event.msg)

            chain = chain.event.chain

        msg = _event_utils.deduplicate_message_parts(messages)
        segment = '\n'.join(_get_message_lines(msg, event.help_text, event.formatted_source_context)) + '\n'

        if event.events:
            child_msgs = [format_event_verbose_message(child) for child in event.events]
            segment += _format_event_children("Sub-Event", child_msgs)

        segments.append(segment)

        if chain and chain.follow:
            segments.append(f'\n{chain.msg_reason}\n\n')

            event = chain.event
        else:
            event = None

    if len(segments) > 1:
        segments.insert(0, _event_utils.format_event_brief_message(original_event) + '\n\n')

    return ''.join(segments)


def _format_event_children(label: str, children: _c.Iterable[str]) -> str:
    """Format the given list of child messages into a single string."""
    items = list(children)
    count = len(items)
    lines = ['\n']

    for idx, item in enumerate(items):
        lines.append(f'+--[ {label} {idx + 1} of {count} ]---\n')
        lines.append(_textwrap.indent(f"\n{item}\n", "| ", lambda value: True))

    lines.append(f'+--[ End {label} ]---\n')

    return ''.join(lines)


def _get_message_lines(message: str, help_text: str | None, formatted_source_context: str | None) -> list[str]:
    """Return a list of message lines constructed from the given message, help text and formatted source context."""
    if help_text and not formatted_source_context and '\n' not in message and '\n' not in help_text:
        return [f'{message} {help_text}']  # prefer a single-line message with help text when there is no source context

    message_lines = [message]

    if formatted_source_context:
        message_lines.append(formatted_source_context)

    if help_text:
        message_lines.append('')
        message_lines.append(help_text)

    return message_lines
