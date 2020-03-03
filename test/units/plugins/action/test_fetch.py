#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.errors import AnsibleError
from ansible.plugins.action.fetch import ActionModule
from ansible.playbook.task import Task


# CVE-2020-1735
@pytest.mark.parametrize('source', [
    '../foo',
    '../../foo',
    '../../../foo',
    '/../../../foo',
    '/../foo',
]
)
def test_fetch_path_traversal(mocker, source):
    task = mocker.MagicMock(Task)
    task.args = {
        'src': '/tmp/foo',
        'dest': 'bar',
        'fail_on_missing': True,
    }
    task.async_val = False

    connection = mocker.MagicMock()
    mocker.patch.object(connection._shell, 'join_path', return_value='a/')

    play_context = mocker.MagicMock()
    play_context.check_mode = False
    play_context.remote_addr = 'testhost'

    loader = mocker.MagicMock()
    mocker.patch.object(loader, 'path_dwim', return_value='bar')

    plugin = ActionModule(task, connection, play_context, loader, templar=None, shared_loader_obj=None)
    mocker.patch.object(plugin, '_remote_expand_user', return_value='/tmp/foo')
    mocker.patch.object(plugin, '_execute_module', return_value={'source': source, 'encoding': 'notbase64'})

    with pytest.raises(AnsibleError, match=r'Source path would result in incorrect destination'):
        plugin.run()
