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
module: purefa_pgsnap
version_added: '2.6'
short_description: Manage local protection group snapshots on Pure Storage FlashArrays
description:
- Create or delete local protection group snapshots on Pure Storage FlashArray.
- This module only supports local protection groups.
author:
- Simon Dodsley (@sdodsley)
options:
  name:
    description:
    - The name of the source protection group.
    required: true
  suffix:
    description:
    - Suffix of snapshot name.
  state:
    description:
    - Define whether the protection group snapshot should exist or not.
      Copy (added in 2.7) will force an overwrite of an exisitng volume
      from a snapshot.
    choices: [ absent, present, copy ]
    default: present
  eradicate:
    description:
    - Define whether to eradicate the snapshot on delete or leave in trash.
    type: bool
    default: 'no'
  restore:
    description:
    - Restore a specific volume from a protection group snapshot.
      This implies overwrite of the current full volume. USE WITH CARE!!
    version_added: 2.7
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create protection group snapshot foo.ansible
  purefa_pgsnap:
    name: foo
    suffix: ansible
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: present

- name: Delete and eradicate protection group snapshot named foo.snap
  purefa_pgsnap:
    name: foo
    suffix: snap
    eradicate: true
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent

- name: Restore volume data from protection group snapshot named foo.snap
        USE WITH CARE! This will overwrite your existing volume
  purefa_pgsnap:
    name: foo
    suffix: snap
    restore: data
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: copy
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


def get_pgroup(module, array):
    """Return Protection Group or None"""
    try:
        return array.get_pgroup(module.params['name'])
    except:
        return None


def get_pgroupvolume(module, array):
    """Return Protection Group Volume or None"""
    try:
        pgroup = array.get_pgroup(module.params['name'])
        for volume in pgroup['volumes']:
            if volume == module.params['restore']:
                return volume
    except:
        return None


def get_pgsnapshot(module, array):
    """Return Snapshot or None"""
    try:
        snapname = module.params['name'] + "." + module.params['suffix']
        for s in array.get_pgroup(module.params['name'], snap='true'):
            if s['name'] == snapname:
                return snapname
    except:
        return None


def create_pgsnapshot(module, array):
    """Create Protection Group Snapshot"""
    if not module.check_mode:
        try:
            array.create_pgroup_snapshot(source=module.params['name'],
                                         suffix=module.params['suffix'],
                                         snap=True,
                                         apply_retention=True)
            changed = True
        except:
            changed = False
    module.exit_json(changed=changed)


def restore_pgsnapvolume(module, array):
    """Restore a Protection Group Snapshot Volume"""
    volume = module.params['name'] + "." + module.params['suffix'] + "." + module.params['restore']
    try:
        array.copy_volume(volume, module.params['restore'], overwrite=True)
        changed = True
    except:
        changed = False
    module.exit_json(changed=changed)


def update_pgsnapshot(module, array):
    """Update Protection Group Snapshot"""
    changed = False
    module.exit_json(changed=changed)


def delete_pgsnapshot(module, array):
    """ Delete Protection Group Snapshot"""
    if not module.check_mode:
        snapname = module.params['name'] + "." + module.params['suffix']
        try:
            array.destroy_pgroup(snapname)
            chaned = True
            if module.params['eradicate']:
                try:
                    array.eradicate_pgroup(snapname)
                    changed = True
                except:
                    changed = False
        except:
            changed = False
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        suffix=dict(type='str'),
        restore=dict(type='str'),
        eradicate=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['absent', 'present', 'copy']),
    ))

    required_if = [('state', 'copy', ['suffix', 'restore'])]

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
    pgroup = get_pgroup(module, array)
    pgsnap = get_pgsnapshot(module, array)
    rvolume = get_pgroupvolume(module, array)

    if state == 'copy' and rvolume:
        restore_pgsnapvolume(module, array)
    elif state == 'present' and pgroup and not pgsnap:
        create_pgsnapshot(module, array)
    elif state == 'present' and pgroup and pgsnap:
        update_pgsnapshot(module, array)
    elif state == 'present' and not pgroup:
        update_pgsnapshot(module, array)
    elif state == 'absent' and pgsnap:
        delete_pgsnapshot(module, array)
    elif state == 'absent' and not pgsnap:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
