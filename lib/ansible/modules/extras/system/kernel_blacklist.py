#!/usr/bin/python
# encoding: utf-8 -*-

# (c) 2013, Matthias Vogelgesang <matthias.vogelgesang@gmail.com>
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

import os
import re


DOCUMENTATION = '''
---
module: kernel_blacklist
author: Matthias Vogelgesang
version_added: 1.4
short_description: Blacklist kernel modules
description:
    - Add or remove kernel modules from blacklist.
options:
    name:
        required: true
        description:
            - Name of kernel module to black- or whitelist.
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the module should be present in the blacklist or absent.
    blacklist_file:
        required: false
        description:
            - If specified, use this blacklist file instead of
              C(/etc/modprobe.d/blacklist-ansible.conf).
        default: null
requirements: []
'''

EXAMPLES = '''
# Blacklist the nouveau driver module
- kernel_blacklist: name=nouveau state=present
'''


class Blacklist(object):
    def __init__(self, module, filename):
        if not os.path.exists(filename):
            open(filename, 'a').close()

        self.filename = filename
        self.module = module

    def get_pattern(self):
        return '^blacklist\s*' + self.module + '$'

    def readlines(self):
        f = open(self.filename, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def module_listed(self):
        lines = self.readlines()
        pattern = self.get_pattern()

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            if re.match(pattern, stripped):
                return True

        return False

    def remove_module(self):
        lines = self.readlines()
        pattern = self.get_pattern()

        f = open(self.filename, 'w')

        for line in lines:
            if not re.match(pattern, line.strip()):
                f.write(line)

        f.close()

    def add_module(self):
        f = open(self.filename, 'a')
        f.write('blacklist %s\n' % self.module)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
            blacklist_file=dict(required=False, default=None)
        ),
        supports_check_mode=False,
    )

    args = dict(changed=False, failed=False,
                name=module.params['name'], state=module.params['state'])

    filename = '/etc/modprobe.d/blacklist-ansible.conf'

    if module.params['blacklist_file']:
        filename = module.params['blacklist_file']

    blacklist = Blacklist(args['name'], filename)

    if blacklist.module_listed():
        if args['state'] == 'absent':
            blacklist.remove_module()
            args['changed'] = True
    else:
        if args['state'] == 'present':
            blacklist.add_module()
            args['changed'] = True

    module.exit_json(**args)

# import module snippets
from ansible.module_utils.basic import *
main()
