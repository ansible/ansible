# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.utils.display import Display


def test_display(capsys, mocker):
    """ Test default call to display() """

    # Disable logging
    mocker.patch('ansible.utils.display.logger', return_value=None)

    d = Display()
    d.display(u'Some displayed message')
    out, err = capsys.readouterr()
    assert out == 'Some displayed message\n'


def test_display_color_warning(capsys, mocker):
    """ Test displaying a warning message """

    # Disable logging
    mocker.patch('ansible.utils.display.logger', return_value=None)

    # Warning message wrapped in bright purple color code
    msg = u'[WARNING] This is a warning'
    colorized_msg = u'\x1b[1;35m%s\x1b[0m\n\x1b[1;35m\x1b[0m' % msg
    mocker.patch('ansible.utils.display.stringc', return_value=colorized_msg)

    d = Display()
    d.display(msg, color='bright purple', stderr=True)
    out, err = capsys.readouterr()

    assert err == colorized_msg
