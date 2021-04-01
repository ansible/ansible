# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

import pytest

from ansible.modules import pip


@pytest.fixture
def ansible_global_module_name():
    return 'ansible.modules.pip'


@pytest.mark.parametrize('ansible_module_args', [{'name': 'six'}], indirect=['ansible_module_args'])
@pytest.mark.usefixtures('ansible_module_args')
def test_failure_when_pip_absent(mocker, capfd):
    mocker.patch('ansible.modules.pip._have_pip_module').return_value = False

    get_bin_path = mocker.patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    get_bin_path.return_value = None

    with pytest.raises(SystemExit):
        pip.main()

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'pip needs to be installed' in results['msg']


@pytest.mark.parametrize('ansible_module_args, test_input, expected', [
    [None, ['django>1.11.1', '<1.11.2', 'ipaddress', 'simpleproject<2.0.0', '>1.1.0'],
        ['django>1.11.1,<1.11.2', 'ipaddress', 'simpleproject<2.0.0,>1.1.0']],
    [None, ['django>1.11.1,<1.11.2,ipaddress', 'simpleproject<2.0.0,>1.1.0'],
        ['django>1.11.1,<1.11.2', 'ipaddress', 'simpleproject<2.0.0,>1.1.0']],
    [None, ['django>1.11.1', '<1.11.2', 'ipaddress,simpleproject<2.0.0,>1.1.0'],
        ['django>1.11.1,<1.11.2', 'ipaddress', 'simpleproject<2.0.0,>1.1.0']]])
@pytest.mark.usefixtures('ansible_module_args')
def test_recover_package_name(test_input, expected):
    assert pip._recover_package_name(test_input) == expected


def test_new_mod_make(make_ansible_module_caller):
    # run_module = make_ansible_module_caller('pip')
    # run_module = make_ansible_module_caller('ansible_collections.ansible.builtin.pip')
    # run_module = make_ansible_module_caller(
    #     'ansible_collections.community.general.modules.pip_package_info',
    # )
    # run_module = make_ansible_module_caller(
    #     'ansible_collections.community.general.pip_package_info',
    # )
    run_module = make_ansible_module_caller('ansible.modules.pip')
    assert run_module(name='bottle') == {}


def test_new_mod_global_fail(run_ansible_module):
    failed_response = run_module(name='bottle')
    # assert failed_response.failed  # FIXME?
    assert failed_response['failed']


@pytest.mark.parametrize(
    'ansible_module_name',
    ('ansible.modules.pip', ),
    indirect=('ansible_module_name', ),
)
def test_new_mod_param(run_ansible_module):
    assert run_ansible_module(name='bottle', executable='pip3.9') == {}


def test_new_mod_yaml_fail(run_ansible_task_yaml):
    failed_response = run_ansible_task_yaml("""
      ansible.modules.pip:
        name: bottle
        executable: pip3.9
    """)
    assert failed_response['failed']


def test_new_mod_yaml_list_fail(run_ansible_task_yaml):
    failed_response = run_ansible_task_yaml("""
    - ansible.modules.pip:
        name: bottle
        executable: pip3.9
    """)
    assert failed_response['failed']
