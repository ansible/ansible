#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: mso_label
short_description: Manage labels
description:
- Manage labels on Cisco ACI Multi-Site.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  label:
    description:
    - The name of the label.
    type: str
    required: yes
    aliases: [ name ]
  type:
    description:
    - The type of the label.
    type: str
    choices: [ site ]
    default: site
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a new label
  mso_label:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    label: Belgium
    type: site
    state: present
  delegate_to: localhost

- name: Remove a label
  mso_label:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    label: Belgium
    state: absent
  delegate_to: localhost

- name: Query a label
  mso_label:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    label: Belgium
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all labels
  mso_label:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec, issubset


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        label=dict(type='str', aliases=['name']),
        type=dict(type='str', default='site', choices=['site']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['label']],
            ['state', 'present', ['label']],
        ],
    )

    label = module.params['label']
    label_type = module.params['type']
    state = module.params['state']

    mso = MSOModule(module)

    label_id = None
    path = 'labels'

    # Query for existing object(s)
    if label:
        mso.existing = mso.get_obj(path, displayName=label)
        if mso.existing:
            label_id = mso.existing['id']
            # If we found an existing object, continue with it
            path = 'labels/{id}'.format(id=label_id)
    else:
        mso.existing = mso.query_objs(path)

    if state == 'query':
        pass

    elif state == 'absent':
        mso.previous = mso.existing
        if mso.existing:
            if module.check_mode:
                mso.existing = {}
            else:
                mso.existing = mso.request(path, method='DELETE')

    elif state == 'present':
        mso.previous = mso.existing

        payload = dict(
            id=label_id,
            displayName=label,
            type=label_type,
        )

        mso.sanitize(payload, collate=True)

        if mso.existing:
            if not issubset(mso.sent, mso.existing):
                if module.check_mode:
                    mso.existing = mso.proposed
                else:
                    mso.existing = mso.request(path, method='PUT', data=mso.sent)
        else:
            if module.check_mode:
                mso.existing = mso.proposed
            else:
                mso.existing = mso.request(path, method='POST', data=mso.sent)

    mso.exit_json()


if __name__ == "__main__":
    main()
