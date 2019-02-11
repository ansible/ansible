#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2014, Matt Martz <matt@sivel.net>
# (c) 2016, Justin Mayer <https://justinmayer.com/>
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
# This script is to be used with ansible-vault's --vault-id arg
# to retrieve the vault password via your OS's native keyring application.
#
# This file *MUST* be saved with executable permissions. Otherwise, Ansible
# will try to parse as a password file and display: "ERROR! Decryption failed"
#
# The `keyring` Python module is required: https://pypi.org/project/keyring/
#
# By default, this script will store the specified password in the keyring of
# the user that invokes the script. To specify a user keyring, add a [vault]
# section to your ansible.cfg file with a 'username' option. Example:
#
# [vault]
# username = 'ansible-vault'
#
# In useage like:
#
#    ansible-vault --vault-id keyring_id@contrib/vault/vault-keyring-client.py view some_encrypted_file
#
#  --vault-id will call this script like:
#
#     contrib/vault/vault-keyring-client.py --vault-id keyring_id
#
# That will retrieve the password from users keyring for the
# keyring service 'keyring_id'. The equilivent of:
#
#      keyring get keyring_id $USER
#
# If no vault-id name is specified to ansible command line, the vault-keyring-client.py
# script will be called without a '--vault-id' and will default to the keyring service 'ansible'
# This is equilivent to:
#
#    keyring get ansible $USER
#
# You can configure the `vault_password_file` option in ansible.cfg:
#
# [defaults]
# ...
# vault_password_file = /path/to/vault-keyring-client.py
# ...
#
# To set your password, `cd` to your project directory and run:
#
#   # will use default keyring service / vault-id of 'ansible'
#   /path/to/vault-keyring-client.py --set
#
# or to specify the keyring service / vault-id of 'my_ansible_secret':
#
#  /path/to/vault-keyring-client.py --vault-id my_ansible_secret --set
#
# If you choose not to configure the path to `vault_password_file` in
# ansible.cfg, your `ansible-playbook` command might look like:
#
# ansible-playbook --vault-id=keyring_id@/path/to/vault-keyring-client.py site.yml

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

import argparse
import sys
import getpass
import keyring

from ansible.config.manager import ConfigManager

KEYNAME_UNKNOWN_RC = 2


def build_arg_parser():
    parser = argparse.ArgumentParser(description='Get a vault password from user keyring')

    parser.add_argument('--vault-id', action='store', default=None,
                        dest='vault_id',
                        help='name of the vault secret to get from keyring')
    parser.add_argument('--username', action='store', default=None,
                        help='the username whose keyring is queried')
    parser.add_argument('--set', action='store_true', default=False,
                        dest='set_password',
                        help='set the password instead of getting it')
    return parser


def main():
    config_manager = ConfigManager()
    username = config_manager.data.get_setting('vault.username')
    if not username:
        username = getpass.getuser()

    keyname = config_manager.data.get_setting('vault.keyname')
    if not keyname:
        keyname = 'ansible'

    arg_parser = build_arg_parser()
    args = arg_parser.parse_args()

    username = args.username or username
    keyname = args.vault_id or keyname

    # print('username: %s keyname: %s' % (username, keyname))

    if args.set_password:
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
        if secret is None:
            sys.stderr.write('vault-keyring-client could not find key="%s" for user="%s" via backend="%s"\n' %
                             (keyname, username, keyring.get_keyring().name))
            sys.exit(KEYNAME_UNKNOWN_RC)

        # print('secret: %s' % secret)
        sys.stdout.write('%s\n' % secret)

    sys.exit(0)


if __name__ == '__main__':
    main()
