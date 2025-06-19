# -*- coding: utf-8 -*-
# (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import datetime
import locale
import sys
import typing as t
import unicodedata

from unittest.mock import MagicMock

import pytest

from ansible.module_utils.datatag import deprecator_from_collection_name
from ansible.module_utils._internal import _deprecator, _errors, _messages
from ansible.utils.display import _LIBC, _MAX_INT, Display, get_text_width, _format_message
from ansible.utils.multiprocessing import context as multiprocessing_context


@pytest.fixture
def problematic_wcswidth_chars():
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')

    candidates = set(chr(c) for c in range(sys.maxunicode) if unicodedata.category(chr(c)) == 'Cf')
    problematic = [candidate for candidate in candidates if _LIBC.wcswidth(candidate, _MAX_INT) == -1]

    if not problematic:
        # Newer distributions (Ubuntu 22.04, Fedora 38) include a libc which does not report problematic characters.
        pytest.skip("no problematic wcswidth chars found")  # pragma: nocover

    return problematic


def test_get_text_width():
    locale.setlocale(locale.LC_ALL, '')
    assert get_text_width(u'コンニチハ') == 10
    assert get_text_width(u'abコcd') == 6
    assert get_text_width(u'café') == 4
    assert get_text_width(u'four') == 4
    assert get_text_width(u'\u001B') == 0
    assert get_text_width(u'ab\u0000') == 2
    assert get_text_width(u'abコ\u0000') == 4
    assert get_text_width(u'🚀🐮') == 4
    assert get_text_width(u'\x08') == 0
    assert get_text_width(u'\x08\x08') == 0
    assert get_text_width(u'ab\x08cd') == 3
    assert get_text_width(u'ab\x1bcd') == 3
    assert get_text_width(u'ab\x7fcd') == 3
    assert get_text_width(u'ab\x94cd') == 3

    pytest.raises(TypeError, get_text_width, 1)
    pytest.raises(TypeError, get_text_width, b'four')


def test_get_text_width_no_locale(problematic_wcswidth_chars):
    pytest.raises(EnvironmentError, get_text_width, problematic_wcswidth_chars[0])


def test_Display_banner_get_text_width(monkeypatch, display_resource):
    locale.setlocale(locale.LC_ALL, '')
    display = Display()
    display_mock = MagicMock()
    monkeypatch.setattr(display, 'display', display_mock)

    display.banner(u'🚀🐮', color=False, cows=False)
    args, kwargs = display_mock.call_args
    msg = args[0]
    stars = u' %s' % (75 * u'*')
    assert msg.endswith(stars)


def test_Display_banner_get_text_width_fallback(monkeypatch, display_resource):
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    display = Display()
    display_mock = MagicMock()
    monkeypatch.setattr(display, 'display', display_mock)

    display.banner(u'\U000110cd', color=False, cows=False)
    args, kwargs = display_mock.call_args
    msg = args[0]
    stars = u' %s' % (78 * u'*')
    assert msg.endswith(stars)


def test_Display_set_queue_parent(display_resource):
    display = Display()
    pytest.raises(RuntimeError, display.set_queue, 'foo')


def test_Display_set_queue_fork(display_resource):
    def test():
        display = Display()
        display.set_queue('foo')
        assert display._final_q == 'foo'
    p = multiprocessing_context.Process(target=test)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_Display_display_fork(display_resource):
    def test():
        queue = MagicMock()
        display = Display()
        display.set_queue(queue)
        display.display('foo')
        queue.send_display.assert_called_once_with('display', 'foo')

    p = multiprocessing_context.Process(target=test)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_Display_display_warn_fork(display_resource):
    def test():
        queue = MagicMock()
        display = Display()
        display.set_queue(queue)
        display.warning('foo')
        queue.send_display.assert_called_once_with('_warning', _messages.WarningSummary(event=_messages.Event(msg='foo')))

    p = multiprocessing_context.Process(target=test)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_Display_display_lock(monkeypatch, display_resource):
    lock = MagicMock()
    display = Display()
    monkeypatch.setattr(display, '_lock', lock)
    display.display('foo')
    lock.__enter__.assert_called_once_with()


def test_Display_display_lock_fork(monkeypatch, display_resource):
    lock = MagicMock()
    display = Display()
    monkeypatch.setattr(display, '_lock', lock)
    monkeypatch.setattr(display, '_final_q', MagicMock())
    display.display('foo')
    lock.__enter__.assert_not_called()


def test_format_message_deprecation_with_multiple_details() -> None:
    """
    Verify that a DeprecationSummary with multiple Detail entries can be formatted.
    No existing code generates deprecations with multiple details, but a future deprecation exception type would need to make use of this.
    """
    event = _messages.Event(
        msg='Ignoring ExceptionX.',
        help_text='Plugins must handle it internally.',
        chain=_messages.EventChain(
            msg_reason=_errors.MSG_REASON_DIRECT_CAUSE,
            traceback_reason='',  # not used in this test
            event=_messages.Event(
                msg='Something went wrong.',
                formatted_source_context='Origin: /some/path\n\n...',
            ),
        ),
    )

    result = _format_message(_messages.DeprecationSummary(event=event), False)

    assert result == '''Ignoring ExceptionX. This feature will be removed in the future: Something went wrong.

Ignoring ExceptionX. This feature will be removed in the future. Plugins must handle it internally.

<<< caused by >>>

Something went wrong.
Origin: /some/path

...

'''


A_DATE = datetime.date(2025, 1, 1)
CORE = deprecator_from_collection_name('ansible.builtin')
CORE_MODULE = _messages.PluginInfo(resolved_name='ansible.builtin.ping', type=_messages.PluginType.MODULE)
CORE_PLUGIN = _messages.PluginInfo(resolved_name='ansible.builtin.debug', type=_messages.PluginType.ACTION)
COLL = deprecator_from_collection_name('ns.col')
COLL_MODULE = _messages.PluginInfo(resolved_name='ns.col.ping', type=_messages.PluginType.MODULE)
COLL_PLUGIN = _messages.PluginInfo(resolved_name='ns.col.debug', type=_messages.PluginType.ACTION)
INDETERMINATE = _deprecator.INDETERMINATE_DEPRECATOR
LEGACY_MODULE = _messages.PluginInfo(resolved_name='ping', type=_messages.PluginType.MODULE)
LEGACY_PLUGIN = _messages.PluginInfo(resolved_name='debug', type=_messages.PluginType.ACTION)


@pytest.mark.parametrize('kwargs, expected', (
    # removed
    (dict(msg="Hi", removed=True), "Hi. This feature was removed."),
    (dict(msg="Hi", version="2.99", deprecator=CORE, removed=True), "Hi. This feature was removed from ansible-core version 2.99."),
    (dict(msg="Hi", date=A_DATE, deprecator=COLL_MODULE, removed=True),
     "Hi. This feature was removed from module 'ping' in collection 'ns.col' in a release after 2025-01-01."),
    # no deprecator or indeterminate
    (dict(msg="Hi"), "Hi. This feature will be removed in the future."),
    (dict(msg="Hi", version="2.99"), "Hi. This feature will be removed in the future."),
    (dict(msg="Hi", date=A_DATE), "Hi. This feature will be removed in the future."),
    (dict(msg="Hi", version="2.99", deprecator=INDETERMINATE), "Hi. This feature will be removed in the future."),
    (dict(msg="Hi", date=A_DATE, deprecator=INDETERMINATE), "Hi. This feature will be removed in the future."),
    # deprecator without plugin
    (dict(msg="Hi", deprecator=CORE), "Hi. This feature will be removed from ansible-core in a future release."),
    (dict(msg="Hi", deprecator=COLL), "Hi. This feature will be removed from collection 'ns.col' in a future release."),
    (dict(msg="Hi", version="2.99", deprecator=CORE), "Hi. This feature will be removed from ansible-core version 2.99."),
    (dict(msg="Hi", version="2.99", deprecator=COLL), "Hi. This feature will be removed from collection 'ns.col' version 2.99."),
    (dict(msg="Hi", date=A_DATE, deprecator=COLL), "Hi. This feature will be removed from collection 'ns.col' in a release after 2025-01-01."),
    # deprecator with module
    (dict(msg="Hi", deprecator=CORE_MODULE), "Hi. This feature will be removed from module 'ping' in ansible-core in a future release."),
    (dict(msg="Hi", deprecator=COLL_MODULE), "Hi. This feature will be removed from module 'ping' in collection 'ns.col' in a future release."),
    (dict(msg="Hi", deprecator=LEGACY_MODULE), "Hi. This feature will be removed from module 'ping' in the future."),
    (dict(msg="Hi", version="2.99", deprecator=CORE_MODULE), "Hi. This feature will be removed from module 'ping' in ansible-core version 2.99."),
    (dict(msg="Hi", version="2.99", deprecator=COLL_MODULE), "Hi. This feature will be removed from module 'ping' in collection 'ns.col' version 2.99."),
    (dict(msg="Hi", version="2.99", deprecator=LEGACY_MODULE), "Hi. This feature will be removed from module 'ping' in the future."),
    (dict(msg="Hi", date=A_DATE, deprecator=COLL_MODULE),
     "Hi. This feature will be removed from module 'ping' in collection 'ns.col' in a release after 2025-01-01."),
    (dict(msg="Hi", date=A_DATE, deprecator=LEGACY_MODULE), "Hi. This feature will be removed from module 'ping' in the future."),
    # deprecator with plugin
    (dict(msg="Hi", deprecator=CORE_PLUGIN), "Hi. This feature will be removed from action plugin 'debug' in ansible-core in a future release."),
    (dict(msg="Hi", deprecator=COLL_PLUGIN), "Hi. This feature will be removed from action plugin 'debug' in collection 'ns.col' in a future release."),
    (dict(msg="Hi", deprecator=LEGACY_PLUGIN), "Hi. This feature will be removed from action plugin 'debug' in the future."),
    (dict(msg="Hi", version="2.99", deprecator=CORE_PLUGIN), "Hi. This feature will be removed from action plugin 'debug' in ansible-core version 2.99."),
    (dict(msg="Hi", version="2.99", deprecator=COLL_PLUGIN),
     "Hi. This feature will be removed from action plugin 'debug' in collection 'ns.col' version 2.99."),
    (dict(msg="Hi", version="2.99", deprecator=LEGACY_PLUGIN), "Hi. This feature will be removed from action plugin 'debug' in the future."),
    (dict(msg="Hi", date=A_DATE, deprecator=COLL_PLUGIN),
     "Hi. This feature will be removed from action plugin 'debug' in collection 'ns.col' in a release after 2025-01-01."),
    (dict(msg="Hi", date=A_DATE, deprecator=LEGACY_PLUGIN), "Hi. This feature will be removed from action plugin 'debug' in the future."),
))
def test_get_deprecation_message_with_plugin_info(kwargs: dict[str, t.Any], expected: str) -> None:
    for kwarg in ('version', 'date', 'deprecator'):
        kwargs.setdefault(kwarg, None)

    msg = Display()._get_deprecation_message_with_plugin_info(**kwargs)

    assert msg == expected


@pytest.mark.parametrize("kw,expected", (
    (dict(msg="hi"), "[DEPRECATION WARNING]: hi. This feature will be removed in the future."),
    (dict(msg="hi", removed=True), "[DEPRECATED]: hi. This feature was removed."),
    (dict(msg="hi", version="1.23"), "[DEPRECATION WARNING]: hi. This feature will be removed in the future."),
    (dict(msg="hi", date="2025-01-01"), "[DEPRECATION WARNING]: hi. This feature will be removed in the future."),
    (dict(msg="hi", collection_name="foo.bar"), "[DEPRECATION WARNING]: hi. This feature will be removed from collection 'foo.bar' in a future release."),
    (dict(msg="hi", version="1.23", collection_name="foo.bar"),
     "[DEPRECATION WARNING]: hi. This feature will be removed from collection 'foo.bar' version 1.23."),
    (dict(msg="hi", date="2025-01-01", collection_name="foo.bar"),
     "[DEPRECATION WARNING]: hi. This feature will be removed from collection 'foo.bar' in a release after 2025-01-01."),
))
def test_get_deprecation_message(kw: dict[str, t.Any], expected: str) -> None:
    """Validate the deprecated public version of this function."""

    assert Display().get_deprecation_message(**kw) == expected
