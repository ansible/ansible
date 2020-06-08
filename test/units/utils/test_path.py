# -*- coding: utf-8 -*-
# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
from ansible.utils.path import cs_exists, cs_isdir, cs_isfile


def iter_parent_paths(path):
    parent = path
    while True:
        parent, leaf = os.path.split(parent)
        if not parent or not leaf:
            break
        else:
            yield parent


def test_cs_isfile():
    assert cs_isfile(__file__)
    for p in iter_parent_paths(__file__):
        assert not cs_isfile(p)
    assert not cs_isfile(__file__.upper())


def test_cs_isdir():
    assert not cs_isdir(__file__)
    for p in iter_parent_paths(__file__):
        assert cs_isdir(p)
        if p != p.upper():
            assert not cs_isdir(p.upper())


def test_cs_exists():
    assert cs_exists(__file__)
    assert not cs_exists(__file__.upper())
    for p in iter_parent_paths(__file__):
        assert cs_exists(p)
        if p != p.upper():
            assert not cs_exists(p.upper())
