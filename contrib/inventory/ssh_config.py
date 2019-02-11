#!/usr/bin/env python

# (c) 2014, Tomas Karasek <tomas.karasek@digile.fi>
#
# This file is part of Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

# Dynamic inventory script which lets you use aliases from ~/.ssh/config.
#
# There were some issues with various Paramiko versions. I took a deeper look
# and tested heavily. Now, ansible parses this alright with Paramiko versions
# 1.7.2 to 1.15.2.
#
# It prints inventory based on parsed ~/.ssh/config. You can refer to hosts
# with their alias, rather than with the IP or hostname. It takes advantage
# of the ansible_ssh_{host,port,user,private_key_file}.
#
# If you have in your .ssh/config:
#   Host git
#       HostName git.domain.org
#       User tkarasek
#       IdentityFile /home/tomk/keys/thekey
#
#   You can do
#       $ ansible git -m ping
#
# Example invocation:
#    ssh_config.py --list
#    ssh_config.py --host <alias>

import argparse
import os.path
import sys

import json

import paramiko

from ansible.module_utils.common._collections_compat import MutableSequence

SSH_CONF = '~/.ssh/config'

_key = 'ssh_config'

_ssh_to_ansible = [('user', 'ansible_ssh_user'),
                   ('hostname', 'ansible_ssh_host'),
                   ('identityfile', 'ansible_ssh_private_key_file'),
                   ('port', 'ansible_ssh_port')]


def get_config():
    if not os.path.isfile(os.path.expanduser(SSH_CONF)):
        return {}
    with open(os.path.expanduser(SSH_CONF)) as f:
        cfg = paramiko.SSHConfig()
        cfg.parse(f)
        ret_dict = {}
        for d in cfg._config:
            if isinstance(d['host'], MutableSequence):
                alias = d['host'][0]
            else:
                alias = d['host']
            if ('?' in alias) or ('*' in alias):
                continue
            _copy = dict(d)
            del _copy['host']
            if 'config' in _copy:
                ret_dict[alias] = _copy['config']
            else:
                ret_dict[alias] = _copy
        return ret_dict


def print_list():
    cfg = get_config()
    meta = {'hostvars': {}}
    for alias, attributes in cfg.items():
        tmp_dict = {}
        for ssh_opt, ans_opt in _ssh_to_ansible:
            if ssh_opt in attributes:
                # If the attribute is a list, just take the first element.
                # Private key is returned in a list for some reason.
                attr = attributes[ssh_opt]
                if isinstance(attr, MutableSequence):
                    attr = attr[0]
                tmp_dict[ans_opt] = attr
        if tmp_dict:
            meta['hostvars'][alias] = tmp_dict

    print(json.dumps({_key: list(set(meta['hostvars'].keys())), '_meta': meta}))


def print_host(host):
    cfg = get_config()
    print(json.dumps(cfg[host]))


def get_args(args_list):
    parser = argparse.ArgumentParser(
        description='ansible inventory script parsing .ssh/config')
    mutex_group = parser.add_mutually_exclusive_group(required=True)
    help_list = 'list all hosts from .ssh/config inventory'
    mutex_group.add_argument('--list', action='store_true', help=help_list)
    help_host = 'display variables for a host'
    mutex_group.add_argument('--host', help=help_host)
    return parser.parse_args(args_list)


def main(args_list):

    args = get_args(args_list)
    if args.list:
        print_list()
    if args.host:
        print_host(args.host)


if __name__ == '__main__':
    main(sys.argv[1:])
