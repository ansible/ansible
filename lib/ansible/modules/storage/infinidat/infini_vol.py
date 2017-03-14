#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Gregory Shulov (gregory.shulov@gmail.com)
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

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

HAS_INFINISDK = True
try:
    from infinisdk import InfiniBox, core
except ImportError:
    HAS_INFINISDK = False

from ansible.module_utils.infinibox import *
from capacity import KiB, Capacity


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


# Import Ansible Utilities
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
