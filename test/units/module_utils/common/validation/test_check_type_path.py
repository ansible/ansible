# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re

import os
from ansible.module_utils.common.validation import check_type_path


def mock_expand(value):
    return re.sub(r'~|\$HOME', '/home/testuser', value)


def test_check_type_path(monkeypatch):
    monkeypatch.setattr(os.path, 'expandvars', mock_expand)
    monkeypatch.setattr(os.path, 'expanduser', mock_expand)
    test_cases = (
        ('~/foo', '/home/testuser/foo'),
        ('$HOME/foo', '/home/testuser/foo'),
        ('/home/jane', '/home/jane'),
        (u'/home/jané', u'/home/jané'),
    )
    for case in test_cases:
        assert case[1] == check_type_path(case[0])
