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
module: purefa_snap
version_added: '2.4'
short_description: Manage volume snapshots on Pure Storage FlashArrays
description:
- Create or delete volumes and volume snapshots on Pure Storage FlashArray.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  name:
    description:
    - The name of the source volume.
    type: str
    required: true
  suffix:
    description:
    - Suffix of snapshot name.
    type: str
  target:
    description:
    - Name of target volume if creating from snapshot.
    type: str
  overwrite:
    description:
    - Define whether to overwrite existing volume when creating from snapshot.
    type: bool
    default: 'no'
  state:
    description:
    - Define whether the volume snapshot should exist or not.
    choices: [ absent, copy, present ]
    type: str
    default: present
  eradicate:
    description:
    - Define whether to eradicate the snapshot on delete or leave in trash.
    type: bool
    default: 'no'
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create snapshot foo.ansible
  purefa_snap:
    name: foo
    suffix: ansible
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: present

- name: Create R/W clone foo_clone from snapshot foo.snap
  purefa_snap:
    name: foo
    suffix: snap
    target: foo_clone
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: copy

- name: Overwrite existing volume foo_clone with snapshot foo.snap
  purefa_snap:
    name: foo
    suffix: snap
    target: foo_clone
    overwrite: true
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: copy

- name: Delete and eradicate snapshot named foo.snap
  purefa_snap:
    name: foo
    suffix: snap
    eradicate: true
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec

from datetime import datetime

try:
    from purestorage import purestorage
    HAS_PURESTORAGE = True
except ImportError:
    HAS_PURESTORAGE = False


def get_volume(module, array):
    """Return Volume or None"""
    try:
        return array.get_volume(module.params['name'])
    except Exception:
        return None


def get_target(module, array):
    """Return Volume or None"""
    try:
        return array.get_volume(module.params['target'])
    except Exception:
        return None


def get_snapshot(module, array):
    """Return Snapshot or None"""
    try:
        snapname = module.params['name'] + "." + module.params['suffix']
        for s in array.get_volume(module.params['name'], snap='true'):
            if s['name'] == snapname:
                return snapname
    except Exception:
        return None


def create_snapshot(module, array):
    """Create Snapshot"""
    changed = True
    if not module.check_mode:
        try:
            array.create_snapshot(module.params['name'], suffix=module.params['suffix'])
        except Exception:
            changed = False
    module.exit_json(changed=changed)


def create_from_snapshot(module, array):
    """Create Volume from Snapshot"""
    source = module.params['name'] + "." + module.params['suffix']
    tgt = get_target(module, array)
    if tgt is None:
        changed = True
        if not module.check_mode:
            array.copy_volume(source,
                              module.params['target'])
    elif tgt is not None and module.params['overwrite']:
        changed = True
        if not module.check_mode:
            array.copy_volume(source,
                              module.params['target'],
                              overwrite=module.params['overwrite'])
    elif tgt is not None and not module.params['overwrite']:
        changed = False
    module.exit_json(changed=changed)


def update_snapshot(module, array):
    """Update Snapshot"""
    changed = False
    module.exit_json(changed=changed)


def delete_snapshot(module, array):
    """ Delete Snapshot"""
    changed = True
    if not module.check_mode:
        snapname = module.params['name'] + "." + module.params['suffix']
        try:
            array.destroy_volume(snapname)
            if module.params['eradicate']:
                try:
                    array.eradicate_volume(snapname)
                except Exception:
                    changed = False
        except Exception:
            changed = False
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        suffix=dict(type='str'),
        target=dict(type='str'),
        overwrite=dict(type='bool', default=False),
        eradicate=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['absent', 'copy', 'present']),
    ))

    required_if = [('state', 'copy', ['target', 'suffix'])]

    module = AnsibleModule(argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    if not HAS_PURESTORAGE:
        module.fail_json(msg='purestorage sdk is required for this module in volume')

    if module.params['suffix'] is None:
        suffix = "snap-" + str((datetime.utcnow() - datetime(1970, 1, 1, 0, 0, 0, 0)).total_seconds())
        module.params['suffix'] = suffix.replace(".", "")

    state = module.params['state']
    array = get_system(module)
    volume = get_volume(module, array)
    target = get_target(module, array)
    snap = get_snapshot(module, array)

    if state == 'present' and volume and not snap:
        create_snapshot(module, array)
    elif state == 'present' and volume and snap:
        update_snapshot(module, array)
    elif state == 'present' and not volume:
        update_snapshot(module, array)
    elif state == 'copy' and snap:
        create_from_snapshot(module, array)
    elif state == 'copy' and not snap:
        update_snapshot(module, array)
    elif state == 'absent' and snap:
        delete_snapshot(module, array)
    elif state == 'absent' and not snap:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
