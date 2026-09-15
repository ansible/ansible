# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import locale
import re

from ansible.utils.color import hostcolor
from ansible.utils.display import get_text_width

OK_STATS = {
    'ok': 4,
    'changed': 0,
    'unreachable': 0,
    'failures': 0,
    'skipped': 0,
    'rescued': 0,
    'ignored': 0,
}

HOSTS = [
    'eic-guacamole-desktop-test-target',
    'ext-korcsmaros-slk',
    'short',
]
CJK_HOST = '零一二三四五六七八九'

_ANSI_SGR = re.compile(r'\033\[[0-9;]*m')


def _strip_ansi(text):
    return _ANSI_SGR.sub('', text)


def _recap_line(host, width, color=False):
    return u'%s : ok=4' % hostcolor(host, OK_STATS, color=color, width=width)


def _ok_column(line):
    return get_text_width(_strip_ansi(line)[:_strip_ansi(line).index('ok=')])


def _width_for(hosts):
    return max(26, max(get_text_width(h) for h in hosts))


def test_hostcolor_default_width_is_26():
    field = hostcolor('short', OK_STATS, color=False)
    assert get_text_width(field) == 26


def test_hostcolor_pads_short_hostname_to_longest():
    locale.setlocale(locale.LC_ALL, '')
    width = _width_for(HOSTS)
    field = hostcolor('short', OK_STATS, color=False, width=width)
    assert get_text_width(field) == width
    assert field.startswith('short')


def test_play_recap_lines_align_for_mixed_ascii_hostnames():
    locale.setlocale(locale.LC_ALL, '')
    width = _width_for(HOSTS)
    columns = [_ok_column(_recap_line(h, width)) for h in HOSTS]
    assert len(set(columns)) == 1


def test_longest_host_is_unpadded():
    locale.setlocale(locale.LC_ALL, '')
    width = _width_for(HOSTS)
    longest = max(HOSTS, key=get_text_width)
    field = hostcolor(longest, OK_STATS, color=False, width=width)
    assert field == longest


def test_cjk_hostname_display_width():
    locale.setlocale(locale.LC_ALL, '')
    assert len(CJK_HOST) == 10
    assert get_text_width(CJK_HOST) == 20


def test_play_recap_lines_align_with_cjk_hostname():
    locale.setlocale(locale.LC_ALL, '')
    hosts = [CJK_HOST, 'short']
    width = _width_for(hosts)
    columns = [_ok_column(_recap_line(h, width)) for h in hosts]
    assert len(set(columns)) == 1


def test_short_only_inventory_keeps_26_column_floor():
    hosts = ['a', 'bb']
    width = _width_for(hosts)
    assert width == 26
    assert get_text_width(hostcolor('a', OK_STATS, color=False, width=width)) == 26


def test_colored_path_aligns_visible_ok_column(monkeypatch):
    locale.setlocale(locale.LC_ALL, '')
    monkeypatch.setattr('ansible.utils.color.ANSIBLE_COLOR', True)
    width = _width_for(HOSTS)
    columns = [_ok_column(_recap_line(h, width, color=True)) for h in HOSTS]
    assert len(set(columns)) == 1


def test_colored_path_does_not_color_padding(monkeypatch):
    monkeypatch.setattr('ansible.utils.color.ANSIBLE_COLOR', True)
    field = hostcolor('short', OK_STATS, color=True, width=26)
    padding = ' ' * (26 - len('short'))
    assert field.endswith(padding)
    colored_host = field[:-len(padding)]
    assert colored_host.startswith('\033[')
    assert _strip_ansi(colored_host) == 'short'
    assert _strip_ansi(field) == 'short' + padding


def test_hostcolor_falls_back_to_len_on_environmenterror(monkeypatch):
    def boom(_text):
        raise EnvironmentError('no width')

    monkeypatch.setattr('ansible.utils.display.get_text_width', boom)
    field = hostcolor('short', OK_STATS, color=False, width=26)
    assert field == 'short' + (' ' * 21)
