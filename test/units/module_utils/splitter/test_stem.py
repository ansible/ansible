# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.splitter import stem


@pytest.mark.parametrize(
    'path, expected', (
        ('main', 'main'),
        ('main.yml', 'main'),
        ('/absolute/path/main.yml', 'main'),
        ('/absolute/path/main.yml.tar.gz', 'main.yml.tar'),
        ('main.yml.tar.gz', 'main.yml.tar'),
        ('çafé.yml', 'çafé'),
    )
)
def test_stem(path, expected):
    assert stem(path) == expected


@pytest.mark.parametrize(
    'path', (
        ['list'],
        {'di': 'ct'},
        set(['me', 'on', 'fire']),
        1.7897298374,
        -1,
    )
)
def test_stem_invalid(path):
    with pytest.raises((TypeError, AttributeError)):
        stem(path)
