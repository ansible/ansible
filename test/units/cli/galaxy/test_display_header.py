# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.cli.galaxy import _format_header


def test_display_header_default(capsys):
    assert _format_header('/collections/path', 'h1', 'h2') == (
        '\n'
        '# /collections/path\n'
        'h1         h2     \n'
        '---------- -------\n'
    )


def test_display_header_widths(capsys):
    assert _format_header('/collections/path', 'Collection', 'Version', 18, 18) == (
        '\n'
        '# /collections/path\n'
        'Collection         Version           \n'
        '------------------ ------------------\n'
    )


def test_display_header_small_widths(capsys):
    assert _format_header('/collections/path', 'Col', 'Ver', 1, 1) == (
        '\n'
        '# /collections/path\n'
        'Col Ver\n'
        '--- ---\n'
    )
