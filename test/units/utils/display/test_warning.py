# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.utils.display import Display


def test_warning(capsys):
    d = Display()
    d.warning(u'bad things will happen')
    out, err = capsys.readouterr()
    assert d._warns == {'[WARNING]: bad things will happen\n': 1}
    assert err == '[WARNING]: bad things will happen\n'


def test_warning_formatted(capsys):
    d = Display()
    d.warning(u'bad things will happen', formatted=True)
    out, err = capsys.readouterr()
    assert d._warns == {'\n[WARNING]: \nbad things will happen': 1}
    assert err == '\n[WARNING]: \nbad things will happen\n'
