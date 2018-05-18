#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_volume
version_added: '2.4'
short_description:  Manage volumes on Pure Storage FlashArrays
description:
- Create, delete or extend the capacity of a volume on Pure Storage FlashArray.
author:
- Simon Dodsley (@sdodsley)
options:
  name:
    description:
    - The name of the volume.
    required: true
  target:
    description:
    - The name of the target volume, if copying.
  state:
    description:
    - Define whether the volume should exist or not.
    default: present
    choices: [ absent, present ]
  eradicate:
    description:
    - Define whether to eradicate the volume on delete or leave in trash.
    type: bool
    default: 'no'
  overwrite:
    description:
    - Define whether to overwrite a target volume if it already exisits.
    type: bool
    default: 'no'
  size:
    description:
    - Volume size in M, G, T or P units.
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create new volume named foo
  purefa_volume:
    name: foo
    size: 1T
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: present

- name: Extend the size of an existing volume named foo
  purefa_volume:
    name: foo
    size: 2T
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: present

- name: Delete and eradicate volume named foo
  purefa_volume:
    name: foo
    eradicate: yes
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent

- name: Create clone of volume bar named foo
  purefa_volume:
    name: foo
    target: bar
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: present

- name: Overwrite volume bar with volume foo
  purefa_volume:
    name: foo
    target: bar
    overwrite: yes
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: present
'''

RETURN = r'''
'''

try:
    from purestorage import purestorage
    HAS_PURESTORAGE = True
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
    vol = array.get_volume(module.params['name'])
    if human_to_bytes(module.params['size']) > vol['size']:
        if not module.check_mode:
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
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        target=dict(type='str'),
        overwrite=dict(type='bool', default=False),
        eradicate=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        size=dict(type='str'),
    ))

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
