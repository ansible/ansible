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
module: purefb_snap
version_added: '2.6'
short_description: Manage filesystem snapshots on Pure Storage FlashBlades
description:
- Create or delete volumes and filesystem snapshots on Pure Storage FlashBlades.
author:
- Simon Dodsley (@sdodsley)
options:
  name:
    description:
    - The name of the source filesystem.
    required: true
  suffix:
    description:
    - Suffix of snapshot name.
  state:
    description:
    - Define whether the filesystem snapshot should exist or not.
    choices: [ absent, present ]
    default: present
  eradicate:
    description:
    - Define whether to eradicate the snapshot on delete or leave in trash.
    type: bool
    default: 'no'
extends_documentation_fragment:
- purestorage.fb
'''

EXAMPLES = r'''
- name: Create snapshot foo.ansible
  purefb_snap:
    name: foo
    suffix: ansible
    fb_url: 10.10.10.2
    fb_api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: present

- name: Delete snapshot named foo.snap
  purefb_snap:
    name: foo
    suffix: snap
    fb_url: 10.10.10.2
    fb_api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent

- name: Recover deleted snapshot foo.ansible
  purefb_snap:
    name: foo
    suffix: ansible
    fb_url: 10.10.10.2
    fb_api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: present

- name: Eradicate snapshot named foo.snap
  purefb_snap:
    name: foo
    suffix: snap
    eradicate: true
    fb_url: 10.10.10.2
    fb_api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec

from datetime import datetime

HAS_PURITY_FB = True
try:
    from purity_fb import FileSystemSnapshot, SnapshotSuffix
except ImportError:
    HAS_PURITY_FB = False


def get_fs(module, blade):
    """Return Filesystem or None"""
    fs = []
    fs.append(module.params['name'])
    try:
        res = blade.file_systems.list_file_systems(names=fs)
        return res.items[0]
    except:
        return None


def get_fssnapshot(module, blade):
    """Return Snapshot or None"""
    try:
        filt = 'source=\'' + module.params['name'] + '\' and suffix=\'' + module.params['suffix'] + '\''
        res = blade.file_system_snapshots.list_file_system_snapshots(filter=filt)
        return res.items[0]
    except:
        return None


def create_snapshot(module, blade):
    """Create Snapshot"""
    if not module.check_mode:
        source = []
        source.append(module.params['name'])
        try:
            blade.file_system_snapshots.create_file_system_snapshots(sources=source, suffix=SnapshotSuffix(module.params['suffix']))
            changed = True
        except:
            changed = False
    module.exit_json(changed=changed)


def recover_snapshot(module, blade):
    """Recover deleted Snapshot"""
    if not module.check_mode:
        snapname = module.params['name'] + "." + module.params['suffix']
        new_attr = FileSystemSnapshot(destroyed=False)
        try:
            blade.file_system_snapshots.update_file_system_snapshots(name=snapname, attributes=new_attr)
            changed = True
        except:
            changed = False
    module.exit_json(changed=changed)


def update_snapshot(module, blade):
    """Update Snapshot"""
    changed = False
    module.exit_json(changed=changed)


def delete_snapshot(module, blade):
    """ Delete Snapshot"""
    if not module.check_mode:
        snapname = module.params['name'] + "." + module.params['suffix']
        new_attr = FileSystemSnapshot(destroyed=True)
        try:
            blade.file_system_snapshots.update_file_system_snapshots(name=snapname, attributes=new_attr)
            changed = True
            if module.params['eradicate']:
                try:
                    blade.file_system_snapshots.delete_file_system_snapshots(name=snapname)
                    changed = True
                except:
                    changed = False
        except:
            changed = False
    module.exit_json(changed=changed)


def eradicate_snapshot(module, blade):
    """ Eradicate Snapshot"""
    if not module.check_mode:
        snapname = module.params['name'] + "." + module.params['suffix']
        try:
            blade.file_system_snapshots.delete_file_system_snapshots(name=snapname)
            changed = True
        except:
            changed = False
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            suffix=dict(type='str'),
            eradicate=dict(default='false', type='bool'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True)

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb sdk is required for this module')

    if module.params['suffix'] is None:
        suffix = "snap-" + str((datetime.utcnow() - datetime(1970, 1, 1, 0, 0, 0, 0)).total_seconds())
        module.params['suffix'] = suffix.replace(".", "")

    state = module.params['state']
    blade = get_blade(module)
    fs = get_fs(module, blade)
    snap = get_fssnapshot(module, blade)

    if state == 'present' and fs and not fs.destroyed and not snap:
        create_snapshot(module, blade)
    elif state == 'present' and fs and not fs.destroyed and snap and not snap.destroyed:
        update_snapshot(module, blade)
    elif state == 'present' and fs and not fs.destroyed and snap and snap.destroyed:
        recover_snapshot(module, blade)
    elif state == 'present' and fs and fs.destroyed:
        update_snapshot(module, blade)
    elif state == 'present' and not fs:
        update_snapshot(module, blade)
    elif state == 'absent' and snap and not snap.destroyed:
        delete_snapshot(module, blade)
    elif state == 'absent' and snap and snap.destroyed:
        eradicate_snapshot(module, blade)
    elif state == 'absent' and not snap:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
