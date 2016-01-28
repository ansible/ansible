#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2014, Matt Martz <matt@sivel.net>
#
# This file is part of Ansible
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
#
# Script to be used with vault_password_file or --vault-password-file
# to retrieve the vault password via your OSes native keyring application
#
# This script requires the ``keyring`` python module
#
# Add a [vault] section to your ansible.cfg file,
# the only option is 'username'. Example:
#
# [vault]
# username = 'ansible_vault'
#
# Additionally, it would be a good idea to configure vault_password_file in
# ansible.cfg
#
# [defaults]
# ...
# vault_password_file = /path/to/vault-keyring.py
# ...
#
# To set your password: python /path/to/vault-keyring.py set
#
# If you choose to not configure the path to vault_password_file in ansible.cfg
# your ansible-playbook command may look like:
#
# ansible-playbook --vault-password-file=/path/to/vault-keyring.py site.yml

import sys
import getpass
import keyring

import ansible.constants as C


def main():
    parser = C.load_config_file()
    try:
        username = parser.get('vault', 'username')
    except:
        sys.stderr.write('No [vault] section configured\n')
        sys.exit(1)

    if len(sys.argv) == 2 and sys.argv[1] == 'set':
        password = getpass.getpass()
        confirm = getpass.getpass('Confirm password: ')
        if password == confirm:
            keyring.set_password('ansible', username, password)
        else:
            sys.stderr.write('Passwords do not match\n')
            sys.exit(1)
    else:
        sys.stdout.write('%s\n' % keyring.get_password('ansible', username))

    sys.exit(0)


if __name__ == '__main__':
    main()
