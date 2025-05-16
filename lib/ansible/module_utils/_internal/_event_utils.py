from __future__ import annotations as _annotations

import typing as _t

from ansible.module_utils._internal import _text_utils, _messages


def deduplicate_message_parts(message_parts: list[str]) -> str:
    """Format the given list of messages into a brief message, while deduplicating repeated elements."""
    message_parts = list(reversed(message_parts))

    message = message_parts.pop(0)

    for message_part in message_parts:
        # avoid duplicate messages where the cause was already concatenated to the exception message
        if message_part.endswith(message):
            message = message_part
        else:
            message = _text_utils.concat_message(message_part, message)

    return message


def format_event_brief_message(event: _messages.Event) -> str:
    """
    Format an event into a brief message.
    Help text, contextual information and sub-events will be omitted.
    """
    message_parts: list[str] = []

    while True:
        message_parts.append(event.msg)

        if not event.chain or not event.chain.follow:
            break

        event = event.chain.event

    return deduplicate_message_parts(message_parts)


def deprecation_as_dict(deprecation: _messages.DeprecationSummary) -> _t.Dict[str, _t.Any]:
    """Returns a dictionary representation of the deprecation object in the format exposed to playbooks."""
    from ansible.module_utils._internal._deprecator import INDETERMINATE_DEPRECATOR  # circular import from messages

    if deprecation.deprecator and deprecation.deprecator != INDETERMINATE_DEPRECATOR:
        collection_name = '.'.join(deprecation.deprecator.resolved_name.split('.')[:2])
    else:
        collection_name = None

    result = dict(
        msg=format_event_brief_message(deprecation.event),
        collection_name=collection_name,
    )

    if deprecation.date:
        result.update(date=deprecation.date)
    else:
        result.update(version=deprecation.version)

    return result
