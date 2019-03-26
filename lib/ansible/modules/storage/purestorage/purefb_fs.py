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
module: purefb_fs
version_added: "2.6"
short_description:  Manage filesystemon Pure Storage FlashBlade`
description:
    - This module manages filesystems on Pure Storage FlashBlade.
author: Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  name:
    description:
      - Filesystem Name.
    required: true
    type: str
  state:
    description:
      - Create, delete or modifies a filesystem.
    required: false
    default: present
    type: str
    choices: [ "present", "absent" ]
  eradicate:
    description:
      - Define whether to eradicate the filesystem on delete or leave in trash.
    required: false
    type: bool
    default: false
  size:
    description:
      - Volume size in M, G, T or P units. See examples.
    type: str
    required: false
    default: 32G
  nfs:
    description:
      - Define whether to NFS protocol is enabled for the filesystem.
    required: false
    type: bool
    default: true
  nfs_rules:
    description:
      - Define the NFS rules in operation.
    required: false
    default: '*(rw,no_root_squash)'
    type: str
  smb:
    description:
      - Define whether to SMB protocol is enabled for the filesystem.
    required: false
    type: bool
    default: false
  http:
    description:
      - Define whether to HTTP/HTTPS protocol is enabled for the filesystem.
    required: false
    type: bool
    default: false
  snapshot:
    description:
      - Define whether a snapshot directory is enabled for the filesystem.
    required: false
    type: bool
    default: false
  fastremove:
    description:
      - Define whether the fast remove directory is enabled for the filesystem.
    required: false
    type: bool
    default: false
  hard_limit:
    description:
      - Define whether the capacity for a filesystem is a hard limit.
      - CAUTION This will cause the filesystem to go Read-Only if the
        capacity has already exceeded the logical size of the filesystem.
    required: false
    type: bool
    default: false
    version_added: 2.8
extends_documentation_fragment:
    - purestorage.fb
'''

EXAMPLES = '''
- name: Create new filesystem named foo
  purefb_fs:
    name: foo
    size: 1T
    state: present
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Delete filesystem named foo
  purefb_fs:
    name: foo
    state: absent
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Recover filesystem named foo
  purefb_fs:
    name: foo
    state: present
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Eradicate filesystem named foo
  purefb_fs:
    name: foo
    state: absent
    eradicate: true
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Modify attributes of an existing filesystem named foo
  purefb_fs:
    name: foo

    size: 2T
    nfs : true
    nfs_rules: '*(ro)'
    snapshot: true
    fastremove: true
    hard_limit: true
    smb: true
    state: present
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641'''

RETURN = '''
'''

HAS_PURITY_FB = True
try:
    from purity_fb import FileSystem, ProtocolRule, NfsRule
except ImportError:
    HAS_PURITY_FB = False

from ansible.module_utils.basic import AnsibleModule, human_to_bytes
from ansible.module_utils.pure import get_blade, purefb_argument_spec


HARD_LIMIT_API_VERSION = '1.4'


def get_fs(module, blade):
    """Return Filesystem or None"""
    fs = []
    fs.append(module.params['name'])
    try:
        res = blade.file_systems.list_file_systems(names=fs)
        return res.items[0]
    except Exception:
        return None


def create_fs(module, blade):
    """Create Filesystem"""

    if not module.params['size']:
        module.params['size'] = '32G'

    size = human_to_bytes(module.params['size'])

    if not module.check_mode:
        try:
            api_version = blade.api_version.list_versions().versions
            if HARD_LIMIT_API_VERSION in api_version:
                fs_obj = FileSystem(name=module.params['name'],
                                    provisioned=size,
                                    fast_remove_directory_enabled=module.params['fastremove'],
                                    hard_limit_enabled=module.params['hard_limit'],
                                    snapshot_directory_enabled=module.params['snapshot'],
                                    nfs=NfsRule(enabled=module.params['nfs'], rules=module.params['nfs_rules']),
                                    smb=ProtocolRule(enabled=module.params['smb']),
                                    http=ProtocolRule(enabled=module.params['http'])
                                    )
            else:
                fs_obj = FileSystem(name=module.params['name'],
                                    provisioned=size,
                                    fast_remove_directory_enabled=module.params['fastremove'],
                                    snapshot_directory_enabled=module.params['snapshot'],
                                    nfs=NfsRule(enabled=module.params['nfs'], rules=module.params['nfs_rules']),
                                    smb=ProtocolRule(enabled=module.params['smb']),
                                    http=ProtocolRule(enabled=module.params['http'])
                                    )
            blade.file_systems.create_file_systems(fs_obj)
            changed = True
        except Exception:
            changed = False
    module.exit_json(changed=changed)


def modify_fs(module, blade):
    """Modify Filesystem"""
    changed = False
    attr = {}
    if not module.check_mode:
        fs = get_fs(module, blade)
        if fs.destroyed:
            attr['destroyed'] = False
            changed = True
        if module.params['size']:
            if human_to_bytes(module.params['size']) > fs.provisioned:
                attr['provisioned'] = human_to_bytes(module.params['size'])
                changed = True
        if module.params['nfs'] and not fs.nfs.enabled:
            attr['nfs'] = NfsRule(enabled=module.params['nfs'])
            changed = True
        if not module.params['nfs'] and fs.nfs.enabled:
            attr['nfs'] = NfsRule(enabled=module.params['nfs'])
            changed = True
        if module.params['nfs'] and fs.nfs.enabled:
            if fs.nfs.rules != module.params['nfs_rules']:
                attr['nfs'] = NfsRule(rules=module.params['nfs_rules'])
                changed = True
        if module.params['smb'] and not fs.smb.enabled:
            attr['smb'] = ProtocolRule(enabled=module.params['smb'])
            changed = True
        if not module.params['smb'] and fs.smb.enabled:
            attr['smb'] = ProtocolRule(enabled=module.params['smb'])
            changed = True
        if module.params['http'] and not fs.http.enabled:
            attr['http'] = ProtocolRule(enabled=module.params['http'])
            changed = True
        if not module.params['http'] and fs.http.enabled:
            attr['http'] = ProtocolRule(enabled=module.params['http'])
            changed = True
        if module.params['snapshot'] and not fs.snapshot_directory_enabled:
            attr['snapshot_directory_enabled'] = module.params['snapshot']
            changed = True
        if not module.params['snapshot'] and fs.snapshot_directory_enabled:
            attr['snapshot_directory_enabled'] = module.params['snapshot']
            changed = True
        if module.params['fastremove'] and not fs.fast_remove_directory_enabled:
            attr['fast_remove_directory_enabled'] = module.params['fastremove']
            changed = True
        if not module.params['fastremove'] and fs.fast_remove_directory_enabled:
            attr['fast_remove_directory_enabled'] = module.params['fastremove']
            changed = True
        api_version = blade.api_version.list_versions().versions
        if HARD_LIMIT_API_VERSION in api_version:
            if not module.params['hard_limit'] and fs.hard_limit_enabled:
                attr['hard_limit_enabled'] = module.params['hard_limit']
                changed = True
        if changed:
            n_attr = FileSystem(**attr)
            try:
                blade.file_systems.update_file_systems(name=module.params['name'], attributes=n_attr)
            except Exception:
                changed = False
    module.exit_json(changed=changed)


def delete_fs(module, blade):
    """ Delete Filesystem"""
    if not module.check_mode:
        try:
            blade.file_systems.update_file_systems(name=module.params['name'],
                                                   attributes=FileSystem(nfs=NfsRule(enabled=False),
                                                   smb=ProtocolRule(enabled=False),
                                                   http=ProtocolRule(enabled=False),
                                                   destroyed=True)
                                                   )
            changed = True
            if module.params['eradicate']:
                try:
                    blade.file_systems.delete_file_systems(module.params['name'])
                    changed = True
                except Exception:
                    changed = False
        except Exception:
            changed = False
    module.exit_json(changed=changed)


def eradicate_fs(module, blade):
    """ Eradicate Filesystem"""
    if not module.check_mode:
        try:
            blade.file_systems.delete_file_systems(module.params['name'])
            changed = True
        except Exception:
            changed = False
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            eradicate=dict(default='false', type='bool'),
            nfs=dict(default='true', type='bool'),
            nfs_rules=dict(default='*(rw,no_root_squash)'),
            smb=dict(default='false', type='bool'),
            http=dict(default='false', type='bool'),
            snapshot=dict(default='false', type='bool'),
            fastremove=dict(default='false', type='bool'),
            hard_limit=dict(default='false', type='bool'),
            state=dict(default='present', choices=['present', 'absent']),
            size=dict()
        )
    )

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True)

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb sdk is required for this module')

    state = module.params['state']
    blade = get_blade(module)
    fs = get_fs(module, blade)

    if state == 'present' and not fs:
        create_fs(module, blade)
    elif state == 'present' and fs:
        modify_fs(module, blade)
    elif state == 'absent' and fs and not fs.destroyed:
        delete_fs(module, blade)
    elif state == 'absent' and fs and fs.destroyed and module.params['eradicate']:
        eradicate_fs(module, blade)
    elif state == 'absent' and not fs:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
