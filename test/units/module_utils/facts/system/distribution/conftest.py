# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import pytest

from unittest.mock import Mock


@pytest.fixture
def mock_module():
    mock_module = Mock()
    mock_module.params = {'gather_subset': ['all'],
                          'gather_timeout': 5,
                          'filter': '*'}
    mock_module.get_bin_path = Mock(return_value=None)
    return mock_module
