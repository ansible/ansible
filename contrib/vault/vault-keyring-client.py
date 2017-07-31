#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2014, Matt Martz <matt@sivel.net>
# (c) 2016, Justin Mayer <https://justinmayer.com/>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
# =============================================================================
#
# This script is to be used with vault_password_file or --vault-password-file
# to retrieve the vault password via your OS's native keyring application.
#
# This file *MUST* be saved with executable permissions. Otherwise, Ansible
# will try to parse as a password file and display: "ERROR! Decryption failed"
#
# The `keyring` Python module is required: https://pypi.python.org/pypi/keyring
#
# By default, this script will store the specified password in the keyring of
# the user that invokes the script. To specify a user keyring, add a [vault]
# section to your ansible.cfg file with a 'username' option. Example:
#
# [vault]
# username = 'ansible-vault'
#
# Another optional setting is for the key name, which allows you to use this
# script to handle multiple project vaults with different passwords:
#
# [vault]
# keyname = 'ansible-vault-yourproject'
#
# You can configure the `vault_password_file` option in ansible.cfg:
#
# [defaults]
# ...
# vault_password_file = /path/to/vault-keyring.py
# ...
#
# To set your password, `cd` to your project directory and run:
#
# python /path/to/vault-keyring.py set
#
# If you choose not to configure the path to `vault_password_file` in
# ansible.cfg, your `ansible-playbook` command might look like:
#
# ansible-playbook --vault-password-file=/path/to/vault-keyring.py site.yml

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

import argparse
import sys
import getpass
import keyring

import ansible.constants as C
from ansible.config.manager import ConfigManager


def build_arg_parser():
    parser = argparse.ArgumentParser(description='Get a vault password from user keyring')

    parser.add_argument('--vault-id', action='store', default=None,
                        dest='vault_id',
                        help='name of the vault secret to get from keyring')
    parser.add_argument('--username', action='store', default=None,
                        help='the username whose keyring is queried')
    return parser


def main():

    config_manager = ConfigManager()
    # (parser, config_path) = C.load_config_file()
    username = config_manager.data.get_setting('vault.username')
    # print('u: %s' % username)
    if not username:
        username = getpass.getuser()

    keyname = config_manager.data.get_setting('vault.keyname')
    # print('k: %s' % keyname)
    if not keyname:
        keyname = 'ansible'

    arg_parser = build_arg_parser()
    args = arg_parser.parse_args()
    # print('args: %s' % args)

    username = args.username or username
    keyname = args.vault_id or keyname

    # print('username: %s keyname: %s' % (username, keyname))

    if len(sys.argv) == 2 and sys.argv[1] == 'set':
        intro = 'Storing password in "{}" user keyring using key name: {}\n'
        sys.stdout.write(intro.format(username, keyname))
        password = getpass.getpass()
        confirm = getpass.getpass('Confirm password: ')
        if password == confirm:
            keyring.set_password(keyname, username, password)
        else:
            sys.stderr.write('Passwords do not match\n')
            sys.exit(1)
    else:
        secret = keyring.get_password(keyname, username)
        # print('secret: %s' % secret)
        sys.stdout.write('{}\n'.format(secret))

    sys.exit(0)


if __name__ == '__main__':
    main()
