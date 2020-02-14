# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.cli.galaxy import _display_header


def test_display_header_default(capsys):
    _display_header('/collections/path', 'h1', 'h2')
    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert out_lines[0] == ''
    assert out_lines[1] == '# /collections/path'
    assert out_lines[2] == 'h1         h2     '
    assert out_lines[3] == '---------- -------'


def test_display_header_widths(capsys):
    _display_header('/collections/path', 'Collection', 'Version', 18, 18)
    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert out_lines[0] == ''
    assert out_lines[1] == '# /collections/path'
    assert out_lines[2] == 'Collection         Version           '
    assert out_lines[3] == '------------------ ------------------'


def test_display_header_small_widths(capsys):
    _display_header('/collections/path', 'Col', 'Ver', 1, 1)
    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert out_lines[0] == ''
    assert out_lines[1] == '# /collections/path'
    assert out_lines[2] == 'Col Ver'
    assert out_lines[3] == '--- ---'
