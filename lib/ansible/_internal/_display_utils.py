from __future__ import annotations

import dataclasses

from ansible.module_utils._internal import _ambient_context, _messages
from . import _event_formatting


class DeferredWarningContext(_ambient_context.AmbientContextBase):
    """
    Calls to `Display.warning()` and `Display.deprecated()` within this context will cause the resulting warnings to be captured and not displayed.
    The intended use is for task-initiated warnings to be recorded with the task result, which makes them visible to registered results, callbacks, etc.
    The active display callback is responsible for communicating any warnings to the user.
    """

    # DTFIX-FUTURE: once we start implementing nested scoped contexts for our own bookkeeping, this should be an interface facade that forwards to the nearest
    #               context that actually implements the warnings collection capability

    def __init__(self, *, variables: dict[str, object]) -> None:
        self._variables = variables  # DTFIX-FUTURE: move this to an AmbientContext-derived TaskContext (once it exists)
        self._deprecation_warnings: list[_messages.DeprecationSummary] = []
        self._warnings: list[_messages.WarningSummary] = []
        self._seen: set[_messages.WarningSummary] = set()

    def capture(self, warning: _messages.WarningSummary) -> None:
        """Add the warning/deprecation to the context if it has not already been seen by this context."""
        if warning in self._seen:
            return

        self._seen.add(warning)

        if isinstance(warning, _messages.DeprecationSummary):
            self._deprecation_warnings.append(warning)
        else:
            self._warnings.append(warning)

    def get_warnings(self) -> list[_messages.WarningSummary]:
        """Return a list of the captured non-deprecation warnings."""
        # DTFIX-FUTURE: return a read-only list proxy instead
        return self._warnings

    def get_deprecation_warnings(self) -> list[_messages.DeprecationSummary]:
        """Return a list of the captured deprecation warnings."""
        # DTFIX-FUTURE: return a read-only list proxy instead
        return self._deprecation_warnings


def format_message(summary: _messages.SummaryBase, include_traceback: bool) -> str:
    if isinstance(summary, _messages.DeprecationSummary):
        deprecation_message = get_deprecation_message_with_plugin_info(
            msg=summary.event.msg,
            version=summary.version,
            date=summary.date,
            deprecator=summary.deprecator,
        )

        event = dataclasses.replace(summary.event, msg=deprecation_message)
    else:
        event = summary.event

    return _event_formatting.format_event(event, include_traceback)


def get_deprecation_message_with_plugin_info(
    *,
    msg: str,
    version: str | None,
    removed: bool = False,
    date: str | None,
    deprecator: _messages.PluginInfo | None,
) -> str:
    """Internal use only. Return a deprecation message and help text for display."""
    # DTFIX-FUTURE: the logic for omitting date/version doesn't apply to the payload, so it shows up in vars in some cases when it should not

    if removed:
        removal_fragment = 'This feature was removed'
    else:
        removal_fragment = 'This feature will be removed'

    if not deprecator or not deprecator.type:
        # indeterminate has no resolved_name or type
        # collections have a resolved_name but no type
        collection = deprecator.resolved_name if deprecator else None
        plugin_fragment = ''
    elif deprecator.resolved_name == 'ansible.builtin':
        # core deprecations from base classes (the API) have no plugin name, only 'ansible.builtin'
        plugin_type_name = str(deprecator.type) if deprecator.type is _messages.PluginType.MODULE else f'{deprecator.type} plugin'

        collection = deprecator.resolved_name
        plugin_fragment = f'the {plugin_type_name} API'
    else:
        parts = deprecator.resolved_name.split('.')
        plugin_name = parts[-1]
        plugin_type_name = str(deprecator.type) if deprecator.type is _messages.PluginType.MODULE else f'{deprecator.type} plugin'

        collection = '.'.join(parts[:2]) if len(parts) > 2 else None
        plugin_fragment = f'{plugin_type_name} {plugin_name!r}'

    if collection and plugin_fragment:
        plugin_fragment += ' in'

    if collection == 'ansible.builtin':
        collection_fragment = 'ansible-core'
    elif collection:
        collection_fragment = f'collection {collection!r}'
    else:
        collection_fragment = ''

    if not collection:
        when_fragment = 'in the future' if not removed else ''
    elif date:
        when_fragment = f'in a release after {date}'
    elif version:
        when_fragment = f'version {version}'
    else:
        when_fragment = 'in a future release' if not removed else ''

    if plugin_fragment or collection_fragment:
        from_fragment = 'from'
    else:
        from_fragment = ''

    deprecation_msg = ' '.join(f for f in [removal_fragment, from_fragment, plugin_fragment, collection_fragment, when_fragment] if f) + '.'

    return join_sentences(msg, deprecation_msg)


def join_sentences(first: str | None, second: str | None) -> str:
    """Join two sentences together."""
    first = (first or '').strip()
    second = (second or '').strip()

    if first and first[-1] not in ('!', '?', '.'):
        first += '.'

    if second and second[-1] not in ('!', '?', '.'):
        second += '.'

    if first and not second:
        return first

    if not first and second:
        return second

    return ' '.join((first, second))
