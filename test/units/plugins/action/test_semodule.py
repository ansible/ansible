from ansible.plugins.action.semodule import ActionModule
from ansible.playbook.task import Task
from units.compat.mock import MagicMock, Mock
from ansible.plugins.loader import connection_loader
import os
import pytest

SEMODULE_OUTPUT = '''unconfined      3.5.0
unconfineduser  1.0.0
unlabelednet    1.0.0
unprivuser      2.4.0
updfstab        1.6.0
usbmodules      1.3.0
usbmuxd 1.2.0
userdomain      4.9.1
userhelper      1.8.1
usermanage      1.19.0
usernetctl      1.7.0
'''

play_context = Mock()
play_context.shell = 'sh'
connection = connection_loader.get('local', play_context, os.devnull)
task = MagicMock(Task)


def test_module_exist():
    semodule_action = ActionModule(task, connection, play_context, loader=None, templar=None, shared_loader_obj=None)
    assert semodule_action._module_exist('usermanage', SEMODULE_OUTPUT)
    assert not semodule_action._module_exist('notreal', SEMODULE_OUTPUT)


@pytest.mark.parametrize('new_ver,old_ver,change,change_reason', [
    ('1.2.3', '1.0.0.0', True, 'newer'),
    ('1.2', '2', True, 'older'),
    ('2', '1.6', True, 'newer'),
    ('1.2', '1.2', False, 'same')]
)
def test_check_policy_version(new_ver, old_ver, change, change_reason):
    semodule_action = ActionModule(task, connection, play_context, loader=None, templar=None, shared_loader_obj=None)
    result = semodule_action._check_policy_version(new_ver, old_ver)
    assert result[0] == change
    assert result[1] == change_reason
