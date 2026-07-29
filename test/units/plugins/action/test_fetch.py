# (c) 2024 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from unittest.mock import MagicMock, patch

from ansible.errors import AnsibleActionFail
from ansible.plugins.action.fetch import ActionModule
from ansible.playbook.task import Task


def _fetch_action(src, dest, flat=False):
    task = MagicMock(Task)
    task.async_val = False
    task.check_mode = False
    task.args = {'src': src, 'dest': dest, 'flat': flat}

    connection = MagicMock()
    connection.become = False
    connection._shell.join_path.side_effect = lambda *a: '/'.join(a)
    connection._shell.tmpdir = '/tmp/ansible-tmp'

    play_context = MagicMock()

    loader = MagicMock()
    loader.path_dwim.side_effect = lambda p: p

    action = ActionModule(task=task, connection=connection, play_context=play_context,
                          loader=loader, templar=None, shared_loader_obj=MagicMock())

    # remote lookups are mocked so the destination math is exercised in isolation
    action._remote_expand_user = MagicMock(side_effect=lambda p, **kw: p)
    action._execute_remote_stat = MagicMock(return_value={'exists': True, 'isdir': False, 'checksum': 'A' * 40})
    action._remove_tmp_path = MagicMock()
    return action


@patch('ansible.plugins.action.fetch.secure_hash', return_value=None)
@patch('ansible.plugins.action.fetch.md5', return_value=None)
@patch('ansible.plugins.action.fetch.checksum', return_value=None)
@patch('ansible.plugins.action.fetch.makedirs_safe')
def test_fetch_dest_contains_traversal_hostname(makedirs, csum, _md5, _shash):
    # a hostname sourced from untrusted/dynamic inventory must not redirect the write
    action = _fetch_action(src='/etc/hostname', dest='/tmp/loot')
    with pytest.raises(AnsibleActionFail, match='directory traversal'):
        action.run(task_vars={'inventory_hostname': '../../../../etc/cron.d'})


@patch('ansible.plugins.action.fetch.secure_hash', return_value='A' * 40)
@patch('ansible.plugins.action.fetch.md5', return_value=None)
@patch('ansible.plugins.action.fetch.checksum', return_value=None)
@patch('ansible.plugins.action.fetch.makedirs_safe')
def test_fetch_dest_normal_hostname_is_allowed(makedirs, csum, _md5, _shash):
    action = _fetch_action(src='/etc/hostname', dest='/tmp/loot')
    result = action.run(task_vars={'inventory_hostname': 'web01'})
    assert action._connection.fetch_file.call_args[0][1] == '/tmp/loot/web01/etc/hostname'
    assert not result.get('failed')
