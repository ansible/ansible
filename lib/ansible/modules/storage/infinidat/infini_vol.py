#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Gregory Shulov (gregory.shulov@gmail.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: infini_vol
version_added: 2.3
short_description:  Create, Delete or Modify volumes on Infinibox
description:
    - This module creates, deletes or modifies volume on Infinibox.
author: Gregory Shulov (@GR360RY)
options:
  name:
    description:
      - Volume Name
    required: true
  state:
    description:
      - Creates/Modifies volume when present or removes when absent
    required: false
    default: present
    choices: [ "present", "absent" ]
  size:
    description:
      - Volume size in MB, GB or TB units. See examples.
    required: false
  pool:
    description:
      - Pool that volume will reside on
    required: true
extends_documentation_fragment:
    - infinibox
requirements:
    - capacity
'''

EXAMPLES = '''
- name: Create new volume named foo under pool named bar
  infini_vol:
    name: foo
    size: 1TB
    pool: bar
    state: present
    user: admin
    password: secret
    system: ibox001
'''

RETURN = '''
'''

try:
    from capacity import KiB, Capacity
    HAS_CAPACITY = True
except ImportError:
    HAS_CAPACITY = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.infinibox import HAS_INFINISDK, api_wrapper, get_system, infinibox_argument_spec


@api_wrapper
def get_pool(module, system):
    """Return Pool or None"""
    try:
        return system.pools.get(name=module.params['pool'])
    except:
        return None


@api_wrapper
def get_volume(module, system):
    """Return Volume or None"""
    try:
        return system.volumes.get(name=module.params['name'])
    except:
        return None


@api_wrapper
def create_volume(module, system):
    """Create Volume"""
    if not module.check_mode:
        volume = system.volumes.create(name=module.params['name'], pool=get_pool(module, system))
        if module.params['size']:
            size = Capacity(module.params['size']).roundup(64 * KiB)
            volume.update_size(size)
    module.exit_json(changed=True)


@api_wrapper
def update_volume(module, volume):
    """Update Volume"""
    changed = False
    if module.params['size']:
        size = Capacity(module.params['size']).roundup(64 * KiB)
        if volume.get_size() != size:
            if not module.check_mode:
                volume.update_size(size)
            changed = True

    module.exit_json(changed=changed)


@api_wrapper
def delete_volume(module, volume):
    """ Delete Volume"""
    if not module.check_mode:
        volume.delete()
    module.exit_json(changed=True)


def main():
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            name  = dict(required=True),
            state = dict(default='present', choices=['present', 'absent']),
            pool  = dict(required=True),
            size  = dict()
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg='infinisdk is required for this module')

    if module.params['size']:
        try:
            Capacity(module.params['size'])
        except:
            module.fail_json(msg='size (Physical Capacity) should be defined in MB, GB, TB or PB units')

    state  = module.params['state']
    system = get_system(module)
    pool   = get_pool(module, system)
    volume = get_volume(module, system)

    if pool is None:
        module.fail_json(msg='Pool {} not found'.format(module.params['pool']))

    if state == 'present' and not volume:
        create_volume(module, system)
    elif state == 'present' and volume:
        update_volume(module, volume)
    elif state == 'absent' and volume:
        delete_volume(module, volume)
    elif state == 'absent' and not volume:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
