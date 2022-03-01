# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import pytest
from ansible.playbook.role.requirement import RoleRequirement


def test_null_role_url():
    role = RoleRequirement.role_yaml_parse('')
    assert role['src'] == ''
    assert role['name'] == ''
    assert role['scm'] is None
    assert role['version'] is None


def test_git_file_role_url():
    role = RoleRequirement.role_yaml_parse('git+file:///home/bennojoy/nginx')
    assert role['src'] == 'file:///home/bennojoy/nginx'
    assert role['name'] == 'nginx'
    assert role['scm'] == 'git'
    assert role['version'] is None


def test_https_role_url():
    role = RoleRequirement.role_yaml_parse('https://github.com/bennojoy/nginx')
    assert role['src'] == 'https://github.com/bennojoy/nginx'
    assert role['name'] == 'nginx'
    assert role['scm'] is None
    assert role['version'] is None


def test_git_https_role_url():
    role = RoleRequirement.role_yaml_parse('git+https://github.com/geerlingguy/ansible-role-composer.git')
    assert role['src'] == 'https://github.com/geerlingguy/ansible-role-composer.git'
    assert role['name'] == 'ansible-role-composer'
    assert role['scm'] == 'git'
    assert role['version'] is None


def test_git_version_role_url():
    role = RoleRequirement.role_yaml_parse('git+https://github.com/geerlingguy/ansible-role-composer.git,main')
    assert role['src'] == 'https://github.com/geerlingguy/ansible-role-composer.git'
    assert role['name'] == 'ansible-role-composer'
    assert role['scm'] == 'git'
    assert role['version'] == 'main'


@pytest.mark.parametrize("url", [
    ('https://some.webserver.example.com/files/main.tar.gz'),
    ('https://some.webserver.example.com/files/main.tar.bz2'),
    ('https://some.webserver.example.com/files/main.tar.xz'),
])
def test_tar_role_url(url):
    role = RoleRequirement.role_yaml_parse(url)
    assert role['src'] == url
    assert role['name'].startswith('main')
    assert role['scm'] is None
    assert role['version'] is None


def test_git_ssh_role_url():
    role = RoleRequirement.role_yaml_parse('git@gitlab.company.com:mygroup/ansible-base.git')
    assert role['src'] == 'git@gitlab.company.com:mygroup/ansible-base.git'
    assert role['name'].startswith('ansible-base')
    assert role['scm'] is None
    assert role['version'] is None


def test_token_role_url():
    role = RoleRequirement.role_yaml_parse('git+https://gitlab+deploy-token-312644:_aJQ9c3HWzmRR4knBNyx@gitlab.com/akasurde/ansible-demo')
    assert role['src'] == 'https://gitlab+deploy-token-312644:_aJQ9c3HWzmRR4knBNyx@gitlab.com/akasurde/ansible-demo'
    assert role['name'].startswith('ansible-demo')
    assert role['scm'] == 'git'
    assert role['version'] is None


def test_token_new_style_role_url():
    role = RoleRequirement.role_yaml_parse({"src": "git+https://gitlab+deploy-token-312644:_aJQ9c3HWzmRR4knBNyx@gitlab.com/akasurde/ansible-demo"})
    assert role['src'] == 'https://gitlab+deploy-token-312644:_aJQ9c3HWzmRR4knBNyx@gitlab.com/akasurde/ansible-demo'
    assert role['name'].startswith('ansible-demo')
    assert role['scm'] == 'git'
    assert role['version'] == ''
