# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest


@pytest.fixture
def ansible_global_module_name():
    return 'ansible.modules.pip'


def test_failure_when_pip_absent(monkeypatch, run_ansible_module):
    try:
        from importlib.util import find_spec as _original_find_spec
    except ImportError:
        from imp import find_module as _original_find_module

        def _patched_find_module(name, path=None):
            if path is None and name == 'pip':
                raise ImportError
            return _original_find_module(name, path)

        monkeypatch.setattr('imp.find_module', _patched_find_module)
    else:
        def _patched_find_spec(name, package=None):
            if name == 'pip':
                return None
            return _original_find_spec(name=name, package=package)

        monkeypatch.setattr('importlib.util.find_spec', _patched_find_spec)

    monkeypatch.setattr(
        'ansible.modules.pip._have_pip_module',
        lambda: False,
    )

    monkeypatch.setattr(
        'ansible.module_utils.basic.AnsibleModule.get_bin_path',
        lambda *_: None,
    )

    failed_response = run_ansible_module(name='six')
    assert failed_response['failed']
    assert 'pip needs to be installed' in failed_response['msg']


@pytest.mark.parametrize(
    'test_input',
    (
        ['django>1.11.1', '<1.11.2', 'ipaddress', 'simpleproject<2.0.0', '>1.1.0'],
        ['django>1.11.1,<1.11.2,ipaddress', 'simpleproject<2.0.0,>1.1.0'],
        ['django>1.11.1', '<1.11.2', 'ipaddress,simpleproject<2.0.0,>1.1.0'],
    ),
)
def test_recover_package_name(test_input):
    from ansible.modules import pip
    expected = [
        'django>1.11.1,<1.11.2',
        'ipaddress',
        'simpleproject<2.0.0,>1.1.0',
    ]
    assert pip._recover_package_name(test_input) == expected


@pytest.mark.parametrize(
    'test_input',
    (
        ['django>1.11.1', '<1.11.2', 'ipaddress', 'simpleproject<2.0.0', '>1.1.0'],
        ['django>1.11.1,<1.11.2,ipaddress', 'simpleproject<2.0.0,>1.1.0'],
        ['django>1.11.1', '<1.11.2', 'ipaddress,simpleproject<2.0.0,>1.1.0'],
    ),
)
def test_recover_package_name_v2(test_input, run_ansible_module):
    mod_res = run_ansible_module(name=test_input)
    expected = [
        'django<1.11.2,>1.11.1',
        'ipaddress',
        'simpleproject<2.0.0,>1.1.0',
    ]
    assert mod_res['cmd'][-len(expected):] == expected


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
    assert run_module(name='bottle')['cmd'][1:] == [
        '-m', 'pip.__main__', 'install', 'bottle',
    ]
    assert run_module(name='bottle')  # the second invocation doesn't 💣


@pytest.fixture
def patched_ansible_module_class(patched_ansible_module_class):
    class AnsibleModule(patched_ansible_module_class):
        def run_command(self, *args, **kwargs):
            if args[0][-2:] == ['install', 'bottle']:
                return 666, '<out>', '<err>'
            return super(AnsibleModule, self).run_command(*args, **kwargs)

    return AnsibleModule


def test_new_mod_global_fail(run_ansible_module):
    failed_response = run_ansible_module(name='bottle')
    print(failed_response)
    assert failed_response['failed']


@pytest.mark.parametrize(
    'ansible_module_name',
    ('ansible.modules.pip', ),
    indirect=('ansible_module_name', ),
)
def test_new_mod_param(run_ansible_module):
    assert run_ansible_module(name='bottle', executable='pip3.9')['cmd'][1:] == ['install', 'bottle']


@pytest.mark.parametrize(
    'yaml_task',
    (
        # NOTE: FQCN cannot be used here because ansible-test only puts
        # NOTE: `ansible.modules` and `ansible.module_utils` in the venv.
        # These don't work:
        # * ansible_collections.ansible.legacy.pip
        # * ansible_collections.ansible.builtin.pip
        # Only the following works:
        """
        - ansible.modules.pip:
            name: bottle
            executable: pip3.9
        """,
        """
        ansible.modules.pip:
          name: bottle
          executable: pip3.9
        """,
    ),
    ids=('list', 'mapping'),
)
def test_new_mod_yaml_fail(
        patched_ansible_module_class,
        run_ansible_task_yaml,
        yaml_task,
):
    class AnsibleModule(patched_ansible_module_class):
        def run_command(self, *args, **kwargs):
            if args[0][-2:] == ['install', 'bottle']:
                return 666, '<test out>', '<test err>'
            return super(AnsibleModule, self).run_command(*args, **kwargs)

    failed_response = run_ansible_task_yaml(
        yaml_task,
        ansible_module_class=AnsibleModule,
    )
    assert failed_response['failed']


def test_new_mod_make_subp(run_ansible_module_in_subprocess):
    assert run_ansible_module_in_subprocess(name='bottle')['cmd'][1:] == [
        '-m', 'pip.__main__', 'install', 'bottle',
    ]
