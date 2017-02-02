#!/usr/bin/python
# encoding: utf-8 -*-

# (c) 2013, Matthias Vogelgesang <matthias.vogelgesang@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: kernel_blacklist
author: "Matthias Vogelgesang (@matze)"
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
- kernel_blacklist:
    name: nouveau
    state: present
'''

import os
import re

from ansible.module_utils.basic import AnsibleModule


class Blacklist(object):
    def __init__(self, module, filename, checkmode):
        self.filename = filename
        self.module = module
        self.checkmode = checkmode

    def create_file(self):
        if not self.checkmode and not os.path.exists(self.filename):
            open(self.filename, 'a').close()
            return True
        elif self.checkmode and not os.path.exists(self.filename):
            self.filename = os.devnull
            return True
        else:
            return False

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

        if self.checkmode:
            f = open(os.devnull, 'w')
        else:
            f = open(self.filename, 'w')

        for line in lines:
            if not re.match(pattern, line.strip()):
                f.write(line)

        f.close()

    def add_module(self):
        if self.checkmode:
            f = open(os.devnull, 'a')
        else:
            f = open(self.filename, 'a')

        f.write('blacklist %s\n' % self.module)

        f.close()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
            blacklist_file=dict(required=False, default=None)
        ),
        supports_check_mode=True,
    )

    args = dict(changed=False, failed=False,
                name=module.params['name'], state=module.params['state'])

    filename = '/etc/modprobe.d/blacklist-ansible.conf'

    if module.params['blacklist_file']:
        filename = module.params['blacklist_file']

    blacklist = Blacklist(args['name'], filename, module.check_mode)

    if blacklist.create_file():
        args['changed'] = True
    else:
        args['changed'] = False

    if blacklist.module_listed():
        if args['state'] == 'absent':
            blacklist.remove_module()
            args['changed'] = True
    else:
        if args['state'] == 'present':
            blacklist.add_module()
            args['changed'] = True

    module.exit_json(**args)


if __name__ == '__main__':
    main()
