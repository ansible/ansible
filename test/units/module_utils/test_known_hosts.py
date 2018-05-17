# -*- coding: utf-8 -*-
# (c) 2015, Michael Scherer <mscherer@redhat.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os.path

import pytest

from ansible.module_utils import known_hosts


URLS = {
    'ssh://one.example.org/example.git': {
        'is_ssh_url': True,
        'get_fqdn': 'one.example.org',
        'add_host_key_cmd': " -t rsa one.example.org",
        'port': None,
    },
    'ssh+git://two.example.org/example.git': {
        'is_ssh_url': True,
        'get_fqdn': 'two.example.org',
        'add_host_key_cmd': " -t rsa two.example.org",
        'port': None,
    },
    'rsync://three.example.org/user/example.git': {
        'is_ssh_url': False,
        'get_fqdn': 'three.example.org',
        'add_host_key_cmd': None,  # not called for non-ssh urls
        'port': None,
    },
    'git@four.example.org:user/example.git': {
        'is_ssh_url': True,
        'get_fqdn': 'four.example.org',
        'add_host_key_cmd': " -t rsa four.example.org",
        'port': None,
    },
    'git+ssh://five.example.org/example.git': {
        'is_ssh_url': True,
        'get_fqdn': 'five.example.org',
        'add_host_key_cmd': " -t rsa five.example.org",
        'port': None,
    },
    'ssh://six.example.org:21/example.org': {
        # ssh on FTP Port?
        'is_ssh_url': True,
        'get_fqdn': 'six.example.org',
        'add_host_key_cmd': " -t rsa -p 21 six.example.org",
        'port': '21',
    },
    'ssh://[2001:DB8::abcd:abcd]/example.git': {
        'is_ssh_url': True,
        'get_fqdn': '[2001:DB8::abcd:abcd]',
        'add_host_key_cmd': " -t rsa [2001:DB8::abcd:abcd]",
        'port': None,
    },
    'ssh://[2001:DB8::abcd:abcd]:22/example.git': {
        'is_ssh_url': True,
        'get_fqdn': '[2001:DB8::abcd:abcd]',
        'add_host_key_cmd': " -t rsa -p 22 [2001:DB8::abcd:abcd]",
        'port': '22',
    },
    'username@[2001:DB8::abcd:abcd]/example.git': {
        'is_ssh_url': True,
        'get_fqdn': '[2001:DB8::abcd:abcd]',
        'add_host_key_cmd': " -t rsa [2001:DB8::abcd:abcd]",
        'port': None,
    },
    'username@[2001:DB8::abcd:abcd]:path/example.git': {
        'is_ssh_url': True,
        'get_fqdn': '[2001:DB8::abcd:abcd]',
        'add_host_key_cmd': " -t rsa [2001:DB8::abcd:abcd]",
        'port': None,
    },
    'ssh://internal.git.server:7999/repos/repo.git': {
        'is_ssh_url': True,
        'get_fqdn': 'internal.git.server',
        'add_host_key_cmd': " -t rsa -p 7999 internal.git.server",
        'port': '7999',
    },
}


@pytest.mark.parametrize('url, is_ssh_url', ((k, v['is_ssh_url']) for k, v in URLS.items()))
def test_is_ssh_url(url, is_ssh_url):
    assert known_hosts.is_ssh_url(url) == is_ssh_url


@pytest.mark.parametrize('url, fqdn, port', ((k, v['get_fqdn'], v['port']) for k, v in URLS.items()))
def test_get_fqdn_and_port(url, fqdn, port):
    assert known_hosts.get_fqdn_and_port(url) == (fqdn, port)


@pytest.mark.parametrize('fqdn, port, add_host_key_cmd, stdin',
                         ((v['get_fqdn'], v['port'], v['add_host_key_cmd'], {})
                          for v in URLS.values() if v['is_ssh_url']),
                         indirect=['stdin'])
def test_add_host_key(am, mocker, fqdn, port, add_host_key_cmd):
    get_bin_path = mocker.MagicMock()
    get_bin_path.return_value = keyscan_cmd = "/custom/path/ssh-keyscan"
    am.get_bin_path = get_bin_path

    run_command = mocker.MagicMock()
    run_command.return_value = (0, "Needs output, otherwise thinks ssh-keyscan timed out'", "")
    am.run_command = run_command

    append_to_file = mocker.MagicMock()
    append_to_file.return_value = (None,)
    am.append_to_file = append_to_file

    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('os.path.exists', return_value=True)

    known_hosts.add_host_key(am, fqdn, port=port)
    run_command.assert_called_with(keyscan_cmd + add_host_key_cmd)
