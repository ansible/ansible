#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: purefa_volume
version_added: "2.4"
short_description:  Create, Delete, Copy or Extend a volume on Pure Storage FlashArray
description:
    - This module creates, deletes or extends the capacity of a volume on Pure Storage FlashArray.
author: Simon Dodsley (@sdodsley)
options:
  name:
    description:
      - Volume Name.
    required: true
  target:
    description:
      - Target Volume Name if copying.
    required: false
  state:
    description:
      - Create, delete, copy or extend capacity of a volume.
    required: false
    default: present
    choices: [ "present", "absent" ]
  eradicate:
    description:
      - Define whether to eradicate the volume on delete or leave in trash.
    required: false
    type: bool
    default: false
  overwrite:
    description:
      - Define whether to overwrite a target volume if it already exisits.
    required: false
    type: bool
    default: false
  size:
    description:
      - Volume size in M, G, T or P units. See examples.
    required: false
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
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create clone of volume bar named foo
  purefa_volume:
    name: foo
    target: bar
    state: present
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Overwrite volume bar with volume foo
  purefa_volume:
    name: foo
    target: bar
    overwrite: true
    state: present
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
    if bytes.isdigit():
        bytes = int(bytes)
        if unit == 'P':
            bytes *= 1125899906842624
        elif unit == 'T':
            bytes *= 1099511627776
        elif unit == 'G':
            bytes *= 1073741824
        elif unit == 'M':
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


def get_target(module, array):
    """Return Volume or None"""
    try:
        return array.get_volume(module.params['target'])
    except:
        return None


def create_volume(module, array):
    """Create Volume"""
    size = module.params['size']

    if not module.check_mode:
        array.create_volume(module.params['name'], size)
    module.exit_json(changed=True)


def copy_from_volume(module, array):
    """Create Volume Clone"""
    changed = False

    tgt = get_target(module, array)

    if tgt is None:
        changed = True
        if not module.check_mode:
            array.copy_volume(module.params['name'],
                              module.params['target'])
    elif tgt is not None and module.params['overwrite']:
        changed = True
        if not module.check_mode:
            array.copy_volume(module.params['name'],
                              module.params['target'],
                              overwrite=module.params['overwrite'])

    module.exit_json(changed=changed)


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
        if module.params['eradicate']:
            array.eradicate_volume(module.params['name'])
    module.exit_json(changed=True)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            target=dict(),
            overwrite=dict(default=False, type='bool'),
            eradicate=dict(default=False, type='bool'),
            state=dict(default='present', choices=['present', 'absent']),
            size=dict()
        )
    )

    mutually_exclusive = [['size', 'target']]

    module = AnsibleModule(argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    if not HAS_PURESTORAGE:
        module.fail_json(msg='purestorage sdk is required for this module in volume')

    size = module.params['size']
    state = module.params['state']
    array = get_system(module)
    volume = get_volume(module, array)
    target = get_target(module, array)

    if state == 'present' and not volume and size:
        create_volume(module, array)
    elif state == 'present' and volume and size:
        update_volume(module, array)
    elif state == 'present' and volume and target:
        copy_from_volume(module, array)
    elif state == 'present' and volume and not target:
        copy_from_volume(module, array)
    elif state == 'absent' and volume:
        delete_volume(module, array)
    elif state == 'present' and not volume or not size:
        module.exit_json(changed=False)
    elif state == 'absent' and not volume:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
