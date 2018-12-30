#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_group
version_added: "2.8"
short_description: Manage pfSense groups
description:
  >
    Manage pfSense groups
author: Orion Poplawski (@opoplawski)
notes:
options:
  name:
    description: The name of the group
    required: true
  state:
    description: State in which to leave the group
    required: true
    choices: [ "present", "absent" ]
  descr:
    description: Description of the group
  scope:
    description: Scope of the group ('system' is 'Local')
    default: system
    choices: [ "system", "remote" ]
  gid:
    description:
    - GID of the group.
    - Will use next available GID if not specified.
  priv:
    description:
    - A list of priveleges to assign.
    - Allowed values include page-all, user-shell-access.
    type: list
"""

EXAMPLES = """
- name: Add adservers group
  pfsense_group:
    name: Domain Admins
    description: Remote Admins
    scope: remote
    priv: [ 'page-all', 'user-shell-access' ]

- name: Remove group
  pfsense_group:
    name: Domain Admins
    state: absent
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pfsense.pfsense import PFSenseModule


class pfSenseGroup(object):

    def __init__(self, module):
        self.module = module
        self.pfsense = PFSenseModule(module)
        self.system = self.pfsense.get_element('system')
        self.groups = self.system.findall('group')

    def _find_group(self, name):
        found = None
        i = 0
        for group in self.groups:
            i = list(self.system).index(group)
            if group.find('name').text == name:
                found = group
                break
        return (found, i)

    def add(self, group):
        groupEl, i = self._find_group(group['name'])
        changed = False
        rc = 0
        stdout = ''
        stderr = ''
        if groupEl is None:
            changed = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            groupEl = self.pfsense.new_element('group')
            self.pfsense.copy_dict_to_element(group, groupEl)
            self.system.insert(i + 1, groupEl)
            self.pfsense.write_config(descr='ansible pfsense_group added %s' % (group['name']))
        else:
            changed = self.pfsense.copy_dict_to_element(group, groupEl)
            if self.module.check_mode:
                self.module.exit_json(changed=changed)
            if changed:
                self.pfsense.write_config(descr='ansible pfsense_group updated "%s"' % (group['name']))
        self.module.exit_json(stdout=stdout, stderr=stderr, changed=changed)

    def remove(self, group):
        groupEl, i = self._find_group(group['name'])
        changed = False
        rc = 0
        stdout = ''
        stderr = ''
        if groupEl is not None:
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            self.groups.remove(groupEl)
            changed = True
            self.pfsense.write_config(descr='ansible pfsense_group removed "%s"' % (group['name']))
        self.module.exit_json(stdout=stdout, stderr=stderr, changed=changed)


def main():
    module = AnsibleModule(
        argument_spec={
            'name': {'required': True, 'type': 'str'},
            'state': {
                'required': True,
                'choices': ['present', 'absent']
            },
            'descr': {'required': False, 'type': 'str'},
            'scope': {
                'default': 'system',
                'choices': ['system', 'remote']
            },
            'gid': {'default': '', 'type': 'str'},
            'priv': {'required': False, 'type': 'list'},
        },
        supports_check_mode=True)

    pfgroup = pfSenseGroup(module)

    group = dict()
    group['name'] = module.params['name']
    state = module.params['state']
    if state == 'absent':
        pfgroup.remove(group)
    elif state == 'present':
        group['description'] = module.params['descr']
        group['scope'] = module.params['scope']
        group['gid'] = module.params['gid']
        group['priv'] = module.params['priv']
        pfgroup.add(group)


if __name__ == '__main__':
    main()
