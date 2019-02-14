#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Gregory Shulov (gregory.shulov@gmail.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: infini_fs
version_added: 2.3
short_description:  Create, Delete or Modify filesystems on Infinibox
description:
    - This module creates, deletes or modifies filesystems on Infinibox.
author: Gregory Shulov (@GR360RY)
options:
  name:
    description:
      - File system name.
    required: true
  state:
    description:
      - Creates/Modifies file system when present or removes when absent.
    required: false
    default: present
    choices: [ "present", "absent" ]
  size:
    description:
      - File system size in MB, GB or TB units. See examples.
    required: false
  pool:
    description:
      - Pool that will host file system.
    required: true
extends_documentation_fragment:
    - infinibox
requirements:
    - capacity
'''

EXAMPLES = '''
- name: Create new file system named foo under pool named bar
  infini_fs:
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
import traceback

CAPACITY_IMP_ERR = None
try:
    from capacity import KiB, Capacity
    HAS_CAPACITY = True
except ImportError:
    CAPACITY_IMP_ERR = traceback.format_exc()
    HAS_CAPACITY = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.infinibox import HAS_INFINISDK, api_wrapper, get_system, infinibox_argument_spec


@api_wrapper
def get_pool(module, system):
    """Return Pool or None"""
    try:
        return system.pools.get(name=module.params['pool'])
    except Exception:
        return None


@api_wrapper
def get_filesystem(module, system):
    """Return Filesystem or None"""
    try:
        return system.filesystems.get(name=module.params['name'])
    except Exception:
        return None


@api_wrapper
def create_filesystem(module, system):
    """Create Filesystem"""
    if not module.check_mode:
        filesystem = system.filesystems.create(name=module.params['name'], pool=get_pool(module, system))
        if module.params['size']:
            size = Capacity(module.params['size']).roundup(64 * KiB)
            filesystem.update_size(size)
    module.exit_json(changed=True)


@api_wrapper
def update_filesystem(module, filesystem):
    """Update Filesystem"""
    changed = False
    if module.params['size']:
        size = Capacity(module.params['size']).roundup(64 * KiB)
        if filesystem.get_size() != size:
            if not module.check_mode:
                filesystem.update_size(size)
            changed = True

    module.exit_json(changed=changed)


@api_wrapper
def delete_filesystem(module, filesystem):
    """ Delete Filesystem"""
    if not module.check_mode:
        filesystem.delete()
    module.exit_json(changed=True)


def main():
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            pool=dict(required=True),
            size=dict()
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg=missing_required_lib('infinisdk'))
    if not HAS_CAPACITY:
        module.fail_json(msg=missing_required_lib('capacity'), exception=CAPACITY_IMP_ERR)

    if module.params['size']:
        try:
            Capacity(module.params['size'])
        except Exception:
            module.fail_json(msg='size (Physical Capacity) should be defined in MB, GB, TB or PB units')

    state = module.params['state']
    system = get_system(module)
    pool = get_pool(module, system)
    filesystem = get_filesystem(module, system)

    if pool is None:
        module.fail_json(msg='Pool {0} not found'.format(module.params['pool']))

    if state == 'present' and not filesystem:
        create_filesystem(module, system)
    elif state == 'present' and filesystem:
        update_filesystem(module, filesystem)
    elif state == 'absent' and filesystem:
        delete_filesystem(module, filesystem)
    elif state == 'absent' and not filesystem:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
