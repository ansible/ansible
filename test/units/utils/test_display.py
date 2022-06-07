# -*- coding: utf-8 -*-
# (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock

import pytest

from ansible.module_utils.six import PY3
from ansible.utils.display import Display, get_text_width, initialize_locale
from ansible.utils.multiprocessing import context as multiprocessing_context


def test_get_text_width():
    initialize_locale()
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


@pytest.mark.skipif(PY3, reason='Fallback only happens reliably on py2')
def test_get_text_width_no_locale():
    pytest.raises(EnvironmentError, get_text_width, u'🚀🐮')


def test_Display_banner_get_text_width(monkeypatch):
    initialize_locale()
    display = Display()
    display_mock = MagicMock()
    monkeypatch.setattr(display, 'display', display_mock)

    display.banner(u'🚀🐮', color=False, cows=False)
    args, kwargs = display_mock.call_args
    msg = args[0]
    stars = u' %s' % (75 * u'*')
    assert msg.endswith(stars)


@pytest.mark.skipif(PY3, reason='Fallback only happens reliably on py2')
def test_Display_banner_get_text_width_fallback(monkeypatch):
    display = Display()
    display_mock = MagicMock()
    monkeypatch.setattr(display, 'display', display_mock)

    display.banner(u'🚀🐮', color=False, cows=False)
    args, kwargs = display_mock.call_args
    msg = args[0]
    stars = u' %s' % (77 * u'*')
    assert msg.endswith(stars)


def test_Display_set_queue_parent():
    display = Display()
    pytest.raises(RuntimeError, display.set_queue, 'foo')


def test_Display_set_queue_fork():
    def test():
        display = Display()
        display.set_queue('foo')
        assert display._final_q == 'foo'
    p = multiprocessing_context.Process(target=test)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_Display_display_fork():
    def test():
        queue = MagicMock()
        display = Display()
        display.set_queue(queue)
        display.display('foo')
        queue.send_display.assert_called_once_with(
            'foo', color=None, stderr=False, screen_only=False, log_only=False, newline=True
        )

    p = multiprocessing_context.Process(target=test)
    p.start()
    p.join()
    assert p.exitcode == 0


def test_Display_display_lock(monkeypatch):
    lock = MagicMock()
    display = Display()
    monkeypatch.setattr(display, '_lock', lock)
    display.display('foo')
    lock.__enter__.assert_called_once_with()


def test_Display_display_lock_fork(monkeypatch):
    lock = MagicMock()
    display = Display()
    monkeypatch.setattr(display, '_lock', lock)
    monkeypatch.setattr(display, '_final_q', MagicMock())
    display.display('foo')
    lock.__enter__.assert_not_called()
