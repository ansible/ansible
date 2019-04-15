#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_offload
version_added: '2.8'
short_description: Create, modify and delete NFS or S3 offload targets
description:
- Create, modify and delete NFS or S3 offload targets.
- Only supported on Purity v5.2.0 or higher.
- You must have a correctly configured offload network for offload to work.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Define state of offload
    default: present
    choices: [ absent, present ]
    type: str
  name:
    description:
    - The name of the offload target
    required: true
    type: str
  protocol:
    description:
    - Define which protocol the offload engine uses
    default: nfs
    choices: [ nfs, s3 ]
    type: str
  address:
    description:
    - The IP or FQDN address of the NFS server
    type: str
  share:
    description:
    - NFS export on the NFS server
    type: str
  options:
    description:
    - Additonal mount options for the NFS share
    - Supported mount options include I(port), I(rsize),
      I(wsize), I(nfsvers), and I(tcp) or I(udp)
    required: false
    default: ""
    type: str
  access_key:
    description:
    - Access Key ID of the S3 target
    type: str
  bucket:
    description:
    - Name of the bucket for the S3 target
    type: str
  secret:
    description:
    - Secret Access Key for the S3 target
    type: str
  initialize:
    description:
    - Define whether to initialize the S3 bucket
    type: bool
    default: true

extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create NFS offload target
  purefa_offload:
    name: nfs-offload
    protocol: nfs
    address: 10.21.200.4
    share: "/offload_target"
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create S3 offload target
  purefa_offload:
    name: s3-offload
    protocol: s3
    access_key: "3794fb12c6204e19195f"
    bucket: offload-bucket
    secret: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete offload target
  purefa_offload:
    name: nfs-offload
    protocol: nfs
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592


'''

RETURN = r'''
'''

import re
from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec

MIN_REQUIRED_API_VERSION = '1.16'
REGEX_TARGET_NAME = re.compile(r"^[a-zA-Z0-9\-]*$")


def get_target(module, array):
    """Return target or None"""
    try:
        return array.get_offload(module.params['name'])
    except Exception:
        return None


def create_offload(module, array):
    """Create offload target"""
    changed = False
    # First check if the offload network inteface is there and enabled
    try:
        if not array.get_network_interface('@offload.data')['enabled']:
            module.fail_json(msg='Offload Network interface not enabled. Please resolve.')
    except Exception:
        module.fail_json(msg='Offload Network interface not correctly configured. Please resolve.')
    ra_facts = {}
    if module.params['protocol'] == 'nfs':
        try:
            array.connect_nfs_offload(module.params['name'],
                                      mount_point=module.params['share'],
                                      address=module.params['address'],
                                      mount_options=module.params['options'])
            changed = True
        except Exception:
            module.fail_json(msg='Failed to create NFS offload {0}. '
                                 'Please perform diagnostic checks.'.format(module.params['name']))
    if module.params['protocol'] == 's3':
        try:
            array.connect_s3_offload(module.params['name'],
                                     access_key_id=module.params['access_key'],
                                     secret_access_key=module.params['secret'],
                                     bucket=module.params['bucket'],
                                     initialize=module.params['initialize'])
            changed = True
        except Exception:
            module.fail_json(msg='Failed to create S3 offload {0}. '
                                 'Please perform diagnostic checks.'.format(module.params['name']))
    module.exit_json(changed=changed, ansible_facts=ra_facts)


def update_offload(module, array):
    """Update offload target"""
    changed = False
    module.exit_json(changed=changed)


def delete_offload(module, array):
    """Delete offload target"""
    changed = False
    if module.params['protocol'] == 'nfs':
        try:
            array.disconnect_nfs_offload(module.params['name'])
            changed = True
        except Exception:
            module.fail_json(msg='Failed to delete NFS offload {0}.'.format(module.params['name']))
    if module.params['protocol'] == 's3':
        try:
            array.disconnect_nfs_offload(module.params['name'])
            changed = True
        except Exception:
            module.fail_json(msg='Failed to delete S3 offload {0}.'.format(module.params['name']))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        protocol=dict(type='str', default='nfs', choices=['nfs', 's3']),
        name=dict(type='str', required=True),
        initialize=dict(default=True, type='bool'),
        access_key=dict(type='str'),
        secret=dict(type='str', no_log=True),
        bucket=dict(type='str'),
        share=dict(type='str'),
        address=dict(type='str'),
        options=dict(type='str', default=''),
    ))

    required_if = []

    if argument_spec['state'] == "present":
        required_if = [
            ('protocol', 'nfs', ['address', 'share']),
            ('protocol', 's3', ['access_key', 'secret', 'bucket'])
        ]

    module = AnsibleModule(argument_spec,
                           required_if=required_if,
                           supports_check_mode=False)

    array = get_system(module)
    api_version = array._list_available_rest_versions()

    if MIN_REQUIRED_API_VERSION not in api_version:
        module.fail_json(msg='FlashArray REST version not supported. '
                             'Minimum version required: {0}'.format(MIN_REQUIRED_API_VERSION))

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9]$", module.params['name']) or len(module.params['name']) > 56:
        module.fail_json(msg='Target name invalid. '
                             'Target name must be between 1 and 56 characters (alphanumeric and -) in length '
                             'and begin and end with a letter or number. The name must include at least one letter.')
    if module.params['protocol'] == "s3":
        if not re.match(r"^[a-z0-9][a-z0-9.\-]*[a-z0-9]$", module.params['bucket']) or len(module.params['bucket']) > 63:
            module.fail_json(msg='Bucket name invalid. '
                                 'Bucket name must be between 3 and 63 characters '
                                 '(ilowercase, alphanumeric, dash or period) in length '
                                 'and begin and end with a letter or number.')

    apps = array.list_apps()
    app_version = 0
    all_good = False
    for app in range(0, len(apps)):
        if apps[app]['name'] == 'offload':
            if (apps[app]['enabled'] and
                    apps[app]['status'] == 'healthy' and
                    LooseVersion(apps[app]['version']) >= LooseVersion('5.2.0')):
                all_good = True
                app_version = apps[app]['version']
                break

    if not all_good:
        module.fail_json(msg='Correct Offload app not installed or incorrectly configured')
    else:
        if LooseVersion(array.get()['version']) != LooseVersion(app_version):
            module.fail_json(msg='Offload app version must match Purity version. Please upgrade.')

    target = get_target(module, array)
    if module.params['state'] == 'present' and not target:
        target_count = len(array.list_offload())
        # Currently only 1 offload target is supported
        # TODO: (SD) when more targets supported add in REST version check as well
        if target_count != 0:
            module.fail_json(msg='Currently only 1 Offload Target is supported.')
        create_offload(module, array)
    elif module.params['state'] == 'present' and target:
        update_offload(module, array)
    elif module.params['state'] == 'absent' and target:
        delete_offload(module, array)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
