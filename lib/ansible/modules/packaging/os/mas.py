#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Michael Heap

# Written by Michael Heap <m@michaelheap.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
module: mas
author:
    - "Michael Heap (@mheap)"
version_added: "2.8"
short_description: Manage applications via the Mac App Store
description:
    - Manage applications via the Mac App Store.
    - The `mas` tool only supports installing applications. Removing applications is not supported.
options:
    id:
        description:
        - The ID of the package you want to install.
        - This can be found by running C(mas search APP_NAME) on your machine
        required: true
    state:
        description:
          - C(present) will make sure the package is installed.
        required: false
        choices: [ present ]
        default: "present"
'''

EXAMPLES = '''
- name: Install Keynote
  mas:
    id: 409183694
    state: present

- name: Install Divvy
  mas:
    id: 413857545
    state: present
'''

RETURN = '''
id:
  description: the ID of the package installed
  returned: success
  type: str
  sample: 409183694
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import os


class Mas(object):

    def __init__(self, module):
        self.module = module
        self.params = module.params

        # Populate caches
        self.mas_path = self.module.get_bin_path('mas')
        self.check_logged_in()
        self._installed = self.cache_installed()

    def cache_installed(self):
        rc, raw_list, err = self.run(["list"])
        rows = raw_list.split("\n")
        installed = {}
        for r in rows:
            r = r.split(" ", 1)
            if len(r) == 2:
                installed[r[1]] = r[0]
        return installed

    def check_logged_in(self):
        rc, out, err = self.run(["account"])
        if out.rstrip() == 'Not signed in':
            raise Exception("You must sign in to the Mac App Store")

        return True

    def run(self, cmd):
        cmd.insert(0, self.mas_path)
        return self.module.run_command(cmd, False)

    def install(self, id, dry_run):
        if not dry_run:
            rc, out, err = self.run(["install", id])
            if rc != 0:
                return "Error installing '{0}': {1}".format(id, err.rstrip())
        return None

    def is_installed(self, id):
        return id in self._installed.values()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present']),
            id=dict(required=False)
        )
    )

    state = module.params['state']

    # Is `mas` installed?
    try:
        mas = Mas(module)
    except Exception as e:
        module.exit_json(msg=to_native(e))

    args = {
        "changed": False,
        'id': module.params['id']
    }

    if state == 'present':
        if not mas.is_installed(module.params['id']):
            err = mas.install(module.params['id'], module.check_mode)
            if err is not None:
                module.fail_json(msg=err)
            else:
                args['changed'] = True
    else:
        module.fail_json(msg="State must be one of 'present'")

    module.exit_json(**args)


if __name__ == '__main__':
    main()
