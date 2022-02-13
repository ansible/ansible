# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import textwrap

from ansible.cli.galaxy import _display_header


def test_display_header_default():
    out = _display_header('/collections/path', 'h1', 'h2')
    assert out == textwrap.dedent('''\
        
        # /collections/path
        h1         h2     
        ---------- -------'''
    )


def test_display_header_widths():
    out = _display_header('/collections/path', 'Collection', 'Version', 18, 18)
    assert out == textwrap.dedent('''\
        
        # /collections/path
        Collection         Version           
        ------------------ ------------------'''
    )


def test_display_header_small_widths():
    out = _display_header('/collections/path', 'Col', 'Ver', 1, 1)
    assert out == textwrap.dedent('''\
        
        # /collections/path
        Col Ver
        --- ---'''
    )
