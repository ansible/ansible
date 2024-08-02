# -*- coding: utf-8 -*-
# (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import locale
import sys
import unicodedata
from unittest.mock import MagicMock

import pytest

from ansible.utils.display import _LIBC, _MAX_INT, Display, get_text_width
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
        queue.send_display.assert_called_once_with('warning', 'foo')

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
