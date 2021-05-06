# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import curses
import importlib
import io
import pytest
import sys

from ansible.plugins.action import pause  # noqa: F401
from ansible.module_utils.six import PY2

builtin_import = 'builtins.__import__'
if PY2:
    builtin_import = '__builtin__.__import__'


def test_pause_curses_tigetstr_none(mocker, monkeypatch):
    monkeypatch.delitem(sys.modules, 'ansible.plugins.action.pause')

    dunder_import = __import__

    def _import(*args, **kwargs):
        if args[0] == 'curses':
            mock_curses = mocker.Mock()
            mock_curses.setupterm = mocker.Mock(return_value=True)
            mock_curses.tigetstr = mocker.Mock(return_value=None)
            return mock_curses
        else:
            return dunder_import(*args, **kwargs)

    mocker.patch(builtin_import, _import)

    mod = importlib.import_module('ansible.plugins.action.pause')

    assert mod.HAS_CURSES is True
    assert mod.MOVE_TO_BOL == b'\r'
    assert mod.CLEAR_TO_EOL == b'\x1b[K'


def test_pause_missing_curses(mocker, monkeypatch):
    monkeypatch.delitem(sys.modules, 'ansible.plugins.action.pause')

    dunder_import = __import__

    def _import(*args, **kwargs):
        if args[0] == 'curses':
            raise ImportError
        else:
            return dunder_import(*args, **kwargs)

    mocker.patch(builtin_import, _import)

    mod = importlib.import_module('ansible.plugins.action.pause')

    with pytest.raises(AttributeError):
        mod.curses

    assert mod.HAS_CURSES is False
    assert mod.MOVE_TO_BOL == b'\r'
    assert mod.CLEAR_TO_EOL == b'\x1b[K'


@pytest.mark.parametrize('exc', (curses.error, TypeError, io.UnsupportedOperation))
def test_pause_curses_setupterm_error(mocker, monkeypatch, exc):
    monkeypatch.delitem(sys.modules, 'ansible.plugins.action.pause')

    dunder_import = __import__

    def _import(*args, **kwargs):
        if args[0] == 'curses':
            mock_curses = mocker.Mock()
            mock_curses.setupterm = mocker.Mock(side_effect=exc)
            mock_curses.error = curses.error
            return mock_curses
        else:
            return dunder_import(*args, **kwargs)

    mocker.patch(builtin_import, _import)

    mod = importlib.import_module('ansible.plugins.action.pause')

    assert mod.HAS_CURSES is False
    assert mod.MOVE_TO_BOL == b'\r'
    assert mod.CLEAR_TO_EOL == b'\x1b[K'
