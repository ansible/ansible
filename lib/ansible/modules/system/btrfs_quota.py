#!/usr/bin/python

# Copyright: (c) 2019, Pawel Szatkowski <pszatkowski.byd@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: btrfs_quota

author:
    - Pawel Szatkowski (@pszatkowski) <pszatkowski.byd@gmail.com>

version_added: '2.8'

short_description: Manage btrfs quota

description:
    - This module manage btrfs quota

options:
    state:
        description:
            - Enable or disable quota for btrfs filesystem
        choices: [enabled, disabled]
        required: true
    filesystem:
        description:
            - Path to btrfs filesystem
        required: true
    qgroup:
        description:
            - Qgroup ID (0/257) or subvolume path (@/opt)
        default: none
        required: false
    max_rfer:
        description:
            - Max reference limit
        default: none
        required: false
    max_excl:
        description:
            - Max exclusive limit
        default: none
        required: false
'''

EXAMPLES = '''
- name: Enable quota and set limits
  btrfs_quota:
    state: enable
    filesystem: /
    qgroup: 0/257
    max_rfer: 10G
    max_excl: 500M

- name: Change limits
  btrfs_quota:
    state: enable
    filesystem: /
    qgroup: '@/opt'
    max_rfer: 15G
    max_excl: none

- name: Disable quota
  btrfs_quota:
    state: disable
    filesystem: /
'''

RETURN = ''' # '''

import re
from ansible.module_utils.basic import AnsibleModule


def is_quota_enabled(module):
    filesystem = module.params['filesystem']
    cmd = '%s %s %s' % (btrfs_cmd, 'qgroup show', filesystem)
    rc, out, err = module.run_command(cmd)

    # There is no btrfs command that would check directly if quota is enabled/disabled thus
    # check if one of below errors occure.
    # ERROR: can't list qgroups: quotas not enabled
    # ERROR: can't list qgroups: No such file or directory
    # WARNING: quota disabled, qgroup data may be out of date
    if "ERROR: can't list qgroups" in err or 'WARNING: quota disabled' in err:
        return False
    elif rc != 0:
        module.exit_json(msg='Cannot verify quota state!', cmd=cmd, rc=rc, stdout=out, stderr=err)
    return True


def set_quota_state(module):
    if module.params['state'] == 'enabled':
        state = 'enable'
    elif module.params['state'] == 'disabled':
        state = 'disable'
    filesystem = module.params['filesystem']

    # Workaround due to some sort of btrfs bug. Sometimes it's required to run quota enable/disable
    # command more than once to make it effective.
    run = 2
    for i in range(run):
        cmd = '%s %s %s %s' % (btrfs_cmd, 'quota', state, filesystem)
        rc, out, err = module.run_command(cmd)
        if rc != 0:
            module.exit_json(msg='Cannot modify quota state!', cmd=cmd, rc=rc, stdout=out, stderr=err)


def validate_limit_syntax(module, limit):
    match = re.match(r'^none$|^\d+[kKmMgGtT]$', limit)
    if not match:
        module.exit_json(msg='Incorrect limit syntax!')


def parse_qgroup(module):
    qgroup = module.params['qgroup']
    filesystem = module.params['filesystem']
    match = re.match(r'^\d+\/\d+$', qgroup)
    if match:
        return qgroup
    else:
        cmd = '%s %s %s' % (btrfs_cmd, 'subvolume list', filesystem)
        rc, out, err = module.run_command(cmd)
        if rc != 0:
            module.exit_json(msg='Cannot parse qgroup!', cmd=cmd, rc=rc, stdout=out, stderr=err)

        subvols = {}
        for line in out.splitlines():
            line = line.split()
            subvol_path = line[8]
            subvol_id = line[1]
            subvols[subvol_path] = subvol_id
        qgroup = '0/%s' % (subvols[qgroup])

        match = re.match(r'^\d+\/\d+$', qgroup)
        if match:
            return qgroup
        else:
            return None


def get_limits(module):
    qgroup = parse_qgroup(module)
    filesystem = module.params['filesystem']
    cmd = '%s %s %s' % (btrfs_cmd, 'qgroup show --raw -re', filesystem)
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        module.exit_json(msg='Cannot get limits!', cmd=cmd, rc=rc, stdout=out, stderr=err)
    for line in out.splitlines():
        line = line.split()
        if line[0] == qgroup:
            return (line[3], line[4])
    return (None, None)


def set_limits(module, max_rfer=None, max_excl=None):
    qgroup = parse_qgroup(module)
    filesystem = module.params['filesystem']
    if max_rfer:
        cmd = '%s %s %s %s %s' % (btrfs_cmd, 'qgroup limit', max_rfer, qgroup, filesystem)
        rc, out, err = module.run_command(cmd)
        if rc != 0:
            module.exit_json(msg='Cannot set qgroup rfer limit!', cmd=cmd, rc=rc, stdout=out, stderr=err)

    if max_excl:
        cmd = '%s %s %s %s %s' % (btrfs_cmd, 'qgroup limit -e', max_excl, qgroup, filesystem)
        rc, out, err = module.run_command(cmd)
        if rc != 0:
            module.exit_json(msg='Cannot set qgroup excl limit!', cmd=cmd, rc=rc, stdout=out, stderr=err)


def to_bytes(value):
    prefixes = dict(k=1024, K='1024', m='1048576', M='1048576', g='1073741824', G='1073741824', t='1099511627776', T='1099511627776')
    if value == 'none':
        return 'none'
    prefix = re.search(r'[kKmMgGtT]', value)
    value = re.search(r'\d+', value)
    if value:
        value = int(value.group(0))
        if prefix:
            prefix = int(prefixes[prefix.group(0)])
            return str(value * prefix)
        return str(value)
    return None


def main():
    module_args = dict(
        state=dict(type='str', required=True, choices=['enabled', 'disabled']),
        filesystem=dict(type='str', required=True),
        qgroup=dict(type='str', default='none'),
        max_rfer=dict(type='str', default='none'),
        max_excl=dict(type='str', default='none')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    global btrfs_cmd
    btrfs_cmd = module.get_bin_path('btrfs', required=True)

    changed = False

    if module.params['state'] == 'disabled':
        if is_quota_enabled(module) is True:
            set_quota_state(module)
            changed = True
    elif module.params['state'] == 'enabled':
        if is_quota_enabled(module) is False:
            set_quota_state(module)
            changed = True
        if module.params['qgroup'] != 'none':
            max_rfer, max_excl = get_limits(module)
            validate_limit_syntax(module, module.params['max_rfer'])
            validate_limit_syntax(module, module.params['max_excl'])
            max_rfer_new = to_bytes(module.params['max_rfer'])
            max_excl_new = to_bytes(module.params['max_excl'])
            if max_rfer != max_rfer_new:
                set_limits(module, max_rfer=max_rfer_new)
                changed = True
            if max_excl != max_excl_new:
                set_limits(module, max_excl=max_excl_new)
                changed = True

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
