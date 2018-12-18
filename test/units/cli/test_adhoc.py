# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible import context
from ansible.cli.adhoc import AdHocCLI, display
from ansible.errors import AnsibleOptionsError


def test_parse():
    """ Test adhoc parse"""
    adhoc_cli = AdHocCLI([])
    with pytest.raises(AnsibleOptionsError) as exec_info:
        adhoc_cli.parse()
    assert "Missing target hosts" == str(exec_info.value)


def test_with_command():
    """ Test simple adhoc command"""
    module_name = 'command'
    adhoc_cli = AdHocCLI(args=['-m', module_name, '-vv'])
    adhoc_cli.parse()
    assert context.CLIARGS['module_name'] == module_name
    assert display.verbosity == 2


def test_with_extra_parameters():
    """ Test extra parameters"""
    adhoc_cli = AdHocCLI(args=['-m', 'command', 'extra_parameters'])
    with pytest.raises(AnsibleOptionsError) as exec_info:
        adhoc_cli.parse()
    assert "Extraneous options or arguments" == str(exec_info.value)


def test_simple_command():
    """ Test valid command and its run"""
    adhoc_cli = AdHocCLI(['/bin/ansible', '-m', 'command', 'localhost', '-a', 'echo "hi"'])
    adhoc_cli.parse()
    ret = adhoc_cli.run()
    assert ret == 0


def test_no_argument():
    """ Test no argument command"""
    adhoc_cli = AdHocCLI(['/bin/ansible', '-m', 'command', 'localhost'])
    adhoc_cli.parse()
    with pytest.raises(AnsibleOptionsError) as exec_info:
        adhoc_cli.run()
    assert 'No argument passed to command module' == str(exec_info.value)


def test_did_you_mean_playbook():
    """ Test adhoc with yml file as argument parameter"""
    adhoc_cli = AdHocCLI(['/bin/ansible', '-m', 'command', 'localhost.yml'])
    adhoc_cli.parse()
    with pytest.raises(AnsibleOptionsError) as exec_info:
        adhoc_cli.run()
    assert 'No argument passed to command module (did you mean to run ansible-playbook?)' == str(exec_info.value)


def test_play_ds_positive():
    """ Test _play_ds"""
    adhoc_cli = AdHocCLI(args=['/bin/ansible', 'localhost', '-m', 'command'])
    adhoc_cli.parse()
    ret = adhoc_cli._play_ds('command', 10, 2)
    assert ret['name'] == 'Ansible Ad-Hoc'
    assert ret['tasks'] == [{'action': {'module': 'command', 'args': {}}, 'async_val': 10, 'poll': 2}]


def test_play_ds_with_include_role():
    """ Test include_role command with poll"""
    adhoc_cli = AdHocCLI(args=['/bin/ansible', 'localhost', '-m', 'include_role'])
    adhoc_cli.parse()
    ret = adhoc_cli._play_ds('include_role', None, 2)
    assert ret['name'] == 'Ansible Ad-Hoc'
    assert ret['gather_facts'] == 'no'


def test_run_import_playbook():
    """ Test import_playbook which is not allowed with ad-hoc command"""
    import_playbook = 'import_playbook'
    adhoc_cli = AdHocCLI(args=['/bin/ansible', '-m', import_playbook, 'localhost'])
    adhoc_cli.parse()
    with pytest.raises(AnsibleOptionsError) as exec_info:
        adhoc_cli.run()
    assert context.CLIARGS['module_name'] == import_playbook
    assert "'%s' is not a valid action for ad-hoc commands" % import_playbook == str(exec_info.value)
