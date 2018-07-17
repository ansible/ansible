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
# https://docs.ansible.com/playbooks_vault.html for more details.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import time
import os


def main(args):
    path = os.path.abspath(args[1])

    fo = open(path, 'r+')

    content = fo.readlines()

    content.append('faux editor added at %s\n' % time.time())

    fo.seek(0)
    fo.write(''.join(content))
    fo.close()

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[:]))
