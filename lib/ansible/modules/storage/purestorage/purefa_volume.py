#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: purefa_volume
version_added: "2.4"
short_description:  Create, Delete or Extend a volume on Pure Storage FlashArray
description:
    - This module creates, deletes or extends the capacity of a volume on Pure Storage FlashArray.
author: Simon Dodsley (@simondodsley)
options:
  name:
    description:
      - Volume Name.
    required: true
  state:
    description:
      - Create, delete or extend capacity of a volume.
    required: false
    default: present
    choices: [ "present", "absent" ]
  eradicate:
    description:
      - Define whether to eradicate the volume on delete or leave in trash.
    required: false
    type: bool
    default: false
  size:
    description:
      - Volume size in M, G, T or P units. See examples.
    required: true
extends_documentation_fragment:
    - purestorage
'''

EXAMPLES = '''
- name: Create new volume named foo
  purefa_volume:
    name: foo
    size: 1T
    state: present
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Extend the size of an existing volume named foo
  purefa_volume:
    name: foo
    size: 2T
    state: present
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete and eradicate volume named foo
  purefa_volume:
    name: foo
    eradicate: true
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592'''

RETURN = '''
'''

HAS_PURESTORAGE = True
try:
    from purestorage import purestorage
except ImportError:
    HAS_PURESTORAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def human_to_bytes(size):
    """Given a human-readable byte string (e.g. 2G, 30M),
       return the number of bytes.  Will return 0 if the argument has
       unexpected form.
    """
    bytes = size[:-1]
    unit = size[-1]
    if (bytes.isdigit()):
        bytes = int(bytes)
        if (unit == 'P'):
            bytes *= 1125899906842624
        elif (unit == 'T'):
            bytes *= 1099511627776
        elif (unit == 'G'):
            bytes *= 1073741824
        elif (unit == 'M'):
            bytes *= 1048576
        else:
            bytes = 0
    else:
        bytes = 0
    return bytes


def get_volume(module, array):
    """Return Volume or None"""
    try:
        return array.get_volume(module.params['name'])
    except:
        return None


def create_volume(module, array):
    """Create Volume"""
    size = module.params['size']

    if not module.check_mode:
        array.create_volume(module.params['name'], size)
    module.exit_json(changed=True)


def update_volume(module, array):
    """Update Volume"""
    changed = True
    if not module.check_mode:
        vol = array.get_volume(module.params['name'])
        if human_to_bytes(module.params['size']) > vol['size']:
            array.extend_volume(module.params['name'], module.params['size'])
        else:
            changed = False
    module.exit_json(changed=changed)


def delete_volume(module, array):
    """ Delete Volume"""
    if not module.check_mode:
        array.destroy_volume(module.params['name'])
        if module.params['eradicate'] == 'true':
            array.eradicate_volume(module.params['name'])
    module.exit_json(changed=True)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            eradicate=dict(default='false', type='bool'),
            state=dict(default='present', choices=['present', 'absent']),
            size=dict()
        )
    )

    required_if = [('state', 'present', ('size'))]

    module = AnsibleModule(argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    if not HAS_PURESTORAGE:
        module.fail_json(msg='purestorage sdk is required for this module in volume')

    state = module.params['state']
    array = get_system(module)
    volume = get_volume(module, array)

    if state == 'present' and not volume:
        create_volume(module, array)
    elif state == 'present' and volume:
        update_volume(module, array)
    elif state == 'absent' and volume:
        delete_volume(module, array)
    elif state == 'absent' and not volume:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
