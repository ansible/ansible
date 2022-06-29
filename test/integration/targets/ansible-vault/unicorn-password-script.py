#!/usr/bin/env python
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
# ansible-vault is a script that encrypts/decrypts YAML files. See
# https://docs.ansible.com/ansible/latest/user_guide/vault.html for more details.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys

# This script is NOT called password-script.py on purpose. Only when it
# is invoked as such (through a symlink) does it behave like we expect.
# That way we test that symlink support works:
# https://github.com/ansible/ansible/issues/18319
PASSWORDS = dict(
    password='test-vault-password',
    default='rainbows-are-pretty',
)


def main(args):
    # './password-script.py' -> 'password'
    # './unicorn-whatever.py' -> 'unicorn'
    context = os.path.basename(args[0]).split('-', 1)[0]
    print(PASSWORDS.get(context, PASSWORDS['default']))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
