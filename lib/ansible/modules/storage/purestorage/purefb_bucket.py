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
module: purefb_bucket
version_added: "2.8"
short_description:  Manage Object Store Buckets on a  Pure Storage FlashBlade.
description:
    - This module managess object store (s3) buckets on Pure Storage FlashBlade.
author: Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  name:
    description:
      - Bucket Name.
    required: true
    type: str
  account:
    description:
      - Object Store Account for Bucket.
    required: true
    type: str
  state:
    description:
      - Create, delete or modifies a bucket.
    required: false
    default: present
    type: str
    choices: [ "present", "absent" ]
  eradicate:
    description:
      - Define whether to eradicate the bucket on delete or leave in trash.
    required: false
    type: bool
    default: false
extends_documentation_fragment:
- purestorage.fb
'''

EXAMPLES = '''
- name: Create new bucket named foo in account bar
  purefb_bucket:
    name: foo
    account: bar
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Delete bucket named foo in account bar
  purefb_bucket:
    name: foo
    account: bar
    state: absent
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Recover deleted bucket named foo in account bar
  purefb_bucket:
    name: foo
    account: bar
    state: present
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Eradicate bucket named foo in account bar
  purefb_bucket:
    name: foo
    account: bar
    state: absent
    eradicate: true
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641
'''

RETURN = '''
'''

HAS_PURITY_FB = True
try:
    from purity_fb import Bucket, Reference
except ImportError:
    HAS_PURITY_FB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec


MIN_REQUIRED_API_VERSION = '1.5'


def get_s3acc(module, blade):
    """Return Object Store Account or None"""
    s3acc = None
    accts = blade.object_store_accounts.list_object_store_accounts()
    for acct in range(0, len(accts.items)):
        if accts.items[acct].name == module.params['account']:
            s3acc = accts.items[acct]
    return s3acc


def get_bucket(module, blade):
    """Return Bucket or None"""
    s3bucket = None
    buckets = blade.buckets.list_buckets()
    for bucket in range(0, len(buckets.items)):
        if buckets.items[bucket].name == module.params['name']:
            s3bucket = buckets.items[bucket]
    return s3bucket


def create_bucket(module, blade):
    """Create bucket"""
    changed = False
    try:
        attr = Bucket()
        attr.account = Reference(name=module.params['account'])
        blade.buckets.create_buckets(names=[module.params['name']], account=attr)
        changed = True
    except Exception:
        module.fail_json(msg='Object Store Bucket {0}: Creation failed'.format(module.params['name']))
    module.exit_json(changed=changed)


def delete_bucket(module, blade):
    """ Delete Bucket"""
    changed = False
    try:
        blade.buckets.update_buckets(names=[module.params['name']],
                                     destroyed=Bucket(destroyed=True))
        changed = True
        if module.params['eradicate']:
            try:
                blade.buckets.delete_buckets(names=[module.params['name']])
                changed = True
            except Exception:
                module.fail_json(msg='Object Store Bucket {0}: Eradication failed'.format(module.params['name']))
    except Exception:
        module.fail_json(msg='Object Store Bucket {0}: Deletion failed'.format(module.params['name']))
    module.exit_json(changed=changed)


def recover_bucket(module, blade):
    """ Recover Bucket"""
    changed = False
    try:
        blade.buckets.update_buckets(names=[module.params['name']],
                                     destroyed=Bucket(destroyed=False))
        changed = True
    except Exception:
        module.fail_json(msg='Object Store Bucket {0}: Recovery failed'.format(module.params['name']))
    module.exit_json(changed=changed)


def eradicate_bucket(module, blade):
    """ Eradicate Bucket"""
    changed = False
    try:
        blade.buckets.delete_buckets(names=[module.params['name']])
        changed = True
    except Exception:
        module.fail_json(msg='Object Store Bucket {0}: Eradication failed'.format(module.params['name']))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            account=dict(required=True),
            eradicate=dict(default='false', type='bool'),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )

    module = AnsibleModule(argument_spec)

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb sdk is required for this module')

    state = module.params['state']
    blade = get_blade(module)
    api_version = blade.api_version.list_versions().versions
    if MIN_REQUIRED_API_VERSION not in api_version:
        module.fail_json(msg="Purity//FB must be upgraded to support this module.")
    bucket = get_bucket(module, blade)
    if not get_s3acc(module, blade):
        module.fail_json(msg="Object Store Account {0} does not exist.".format(module.params['account']))

    if state == 'present' and not bucket:
        create_bucket(module, blade)
    elif state == 'present' and bucket and bucket.destroyed:
        recover_bucket(module, blade)
    elif state == 'absent' and bucket and not bucket.destroyed:
        delete_bucket(module, blade)
    elif state == 'absent' and bucket and bucket.destroyed and module.params['eradicate']:
        eradicate_bucket(module, blade)
    elif state == 'absent' and not bucket:
        module.exit_json(changed=False)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
