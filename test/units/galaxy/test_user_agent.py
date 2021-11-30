# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import platform

from ansible.galaxy import user_agent
from ansible.module_utils.ansible_release import __version__ as ansible_version


def test_user_agent():
    res = user_agent.user_agent()
    assert res.startswith('ansible-galaxy/%s' % ansible_version)
    assert platform.system() in res
    assert 'python:' in res
