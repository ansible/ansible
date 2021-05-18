# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.errors import AnsibleFilterError
from ansible.plugins.test.core import version_compare


@pytest.mark.parametrize('value', ('', None, set(), tuple(), dict(), 0, False))
def test_version_compare_empty_value(value):
    with pytest.raises(AnsibleFilterError, match='Version to compare cannot be empty'):
        version_compare(value, '1.0')
