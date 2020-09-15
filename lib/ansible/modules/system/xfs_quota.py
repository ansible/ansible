#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Emmanouil Kampitakis <info@kampitakis.de>
# Copyright: (c) 2018, William Leemans <willie@elaba.net>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: xfs_quota
short_description: Manage quotas on XFS filesystems
description:
  - Configure quotas on XFS filesystems.
  - Before using this module /etc/projects and /etc/projid need to be configured.
version_added: "2.8"
author:
- William Leemans (@bushvin)
options:
  type:
    description:
      - The XFS quota type.
    type: str
    required: true
    choices:
      - user
      - group
      - project
  name:
    description:
      - The name of the user, group or project to apply the quota to, if other than default.
    type: str
  mountpoint:
    description:
      - The mount point on which to apply the quotas.
    type: str
    required: true
  bhard:
    description:
      - Hard blocks quota limit.
      - This argument supports human readable sizes.
    type: str
  bsoft:
    description:
      - Soft blocks quota limit.
      - This argument supports human readable sizes.
    type: str
  ihard:
    description:
      - Hard inodes quota limit.
    type: int
  isoft:
    description:
      - Soft inodes quota limit.
    type: int
  rtbhard:
    description:
      - Hard realtime blocks quota limit.
      - This argument supports human readable sizes.
    type: str
  rtbsoft:
    description:
      - Soft realtime blocks quota limit.
      - This argument supports human readable sizes.
    type: str
  state:
    description:
      - Whether to apply the limits or remove them.
      - When removing limit, they are set to 0, and not quite removed.
    type: str
    default: present
    choices:
      - present
      - absent

requirements:
   - xfsprogs
'''

EXAMPLES = r'''
- name: Set default project soft and hard limit on /opt of 1g
  xfs_quota:
    type: project
    mountpoint: /opt
    bsoft: 1g
    bhard: 1g
    state: present

- name: Remove the default limits on /opt
  xfs_quota:
    type: project
    mountpoint: /opt
    state: absent

- name: Set default soft user inode limits on /home of 1024 inodes and hard of 2048
  xfs_quota:
    type: user
    mountpoint: /home
    isoft: 1024
    ihard: 2048

'''

RETURN = r'''
bhard:
    description: the current bhard setting in bytes
    returned: always
    type: int
    sample: 1024
bsoft:
    description: the current bsoft setting in bytes
    returned: always
    type: int
    sample: 1024
ihard:
    description: the current ihard setting in bytes
    returned: always
    type: int
    sample: 100
isoft:
    description: the current isoft setting in bytes
    returned: always
    type: int
    sample: 100
rtbhard:
    description: the current rtbhard setting in bytes
    returned: always
    type: int
    sample: 1024
rtbsoft:
    description: the current rtbsoft setting in bytes
    returned: always
    type: int
    sample: 1024
'''

import grp
import os
import pwd

from ansible.module_utils.basic import AnsibleModule, human_to_bytes


def main():
    module = AnsibleModule(
        argument_spec=dict(
            bhard=dict(type='str'),
            bsoft=dict(type='str'),
            ihard=dict(type='int'),
            isoft=dict(type='int'),
            mountpoint=dict(type='str', required=True),
            name=dict(type='str'),
            rtbhard=dict(type='str'),
            rtbsoft=dict(type='str'),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            type=dict(type='str', required=True, choices=['group', 'project', 'user'])
        ),
        supports_check_mode=True,
    )

    quota_type = module.params['type']
    name = module.params['name']
    mountpoint = module.params['mountpoint']
    bhard = module.params['bhard']
    bsoft = module.params['bsoft']
    ihard = module.params['ihard']
    isoft = module.params['isoft']
    rtbhard = module.params['rtbhard']
    rtbsoft = module.params['rtbsoft']
    state = module.params['state']

    if bhard is not None:
        bhard = human_to_bytes(bhard)

    if bsoft is not None:
        bsoft = human_to_bytes(bsoft)

    if rtbhard is not None:
        rtbhard = human_to_bytes(rtbhard)

    if rtbsoft is not None:
        rtbsoft = human_to_bytes(rtbsoft)

    result = dict(
        changed=False,
    )

    if not os.path.ismount(mountpoint):
        module.fail_json(msg="Path '%s' is not a mount point" % mountpoint, **result)

    mp = get_fs_by_mountpoint(mountpoint)
    if mp is None:
        module.fail_json(msg="Path '%s' is not a mount point or not located on an xfs file system." % mountpoint, **result)

    if quota_type == 'user':
        type_arg = '-u'
        quota_default = 'root'
        if name is None:
            name = quota_default

        if 'uquota' not in mp['mntopts'] and 'usrquota' not in mp['mntopts'] and 'quota' not in mp['mntopts'] and 'uqnoenforce' not in mp['mntopts'] and \
                'qnoenforce' not in mp['mntopts']:
            module.fail_json(
                msg="Path '%s' is not mounted with the uquota/usrquota/quota/uqnoenforce/qnoenforce option." % mountpoint, **result
            )
        try:
            pwd.getpwnam(name)
        except KeyError as e:
            module.fail_json(msg="User '%s' does not exist." % name, **result)

    elif quota_type == 'group':
        type_arg = '-g'
        quota_default = 'root'
        if name is None:
            name = quota_default

        if 'gquota' not in mp['mntopts'] and 'grpquota' not in mp['mntopts'] and 'gqnoenforce' not in mp['mntopts']:
            module.fail_json(
                msg="Path '%s' is not mounted with the gquota/grpquota/gqnoenforce option. (current options: %s)" % (mountpoint, mp['mntopts']), **result
            )
        try:
            grp.getgrnam(name)
        except KeyError as e:
            module.fail_json(msg="User '%s' does not exist." % name, **result)

    elif quota_type == 'project':
        type_arg = '-p'
        quota_default = '#0'
        if name is None:
            name = quota_default

        if 'pquota' not in mp['mntopts'] and 'prjquota' not in mp['mntopts'] and 'pqnoenforce' not in mp['mntopts']:
            module.fail_json(msg="Path '%s' is not mounted with the pquota/prjquota/pqnoenforce option." % mountpoint, **result)

        if name != quota_default and not os.path.isfile('/etc/projects'):
            module.fail_json(msg="Path '/etc/projects' does not exist.", **result)

        if name != quota_default and not os.path.isfile('/etc/projid'):
            module.fail_json(msg="Path '/etc/projid' does not exist.", **result)

        if name != quota_default and name is not None and get_project_id(name) is None:
            module.fail_json(msg="Entry '%s' has not been defined in /etc/projid." % name, **result)

        prj_set = True
        if name != quota_default:
            cmd = 'project %s' % name
            rc, stdout, stderr = exec_quota(module, cmd, mountpoint)
            if rc != 0:
                result['cmd'] = cmd
                result['rc'] = rc
                result['stdout'] = stdout
                result['stderr'] = stderr
                module.fail_json(msg='Could not get project state.', **result)
            else:
                for line in stdout.split('\n'):
                    if "Project Id '%s' - is not set." in line:
                        prj_set = False
                        break

        if not prj_set and not module.check_mode:
            cmd = 'project -s'
            rc, stdout, stderr = exec_quota(module, cmd, mountpoint)
            if rc != 0:
                result['cmd'] = cmd
                result['rc'] = rc
                result['stdout'] = stdout
                result['stderr'] = stderr
                module.fail_json(msg='Could not get quota realtime block report.', **result)

            result['changed'] = True

        elif not prj_set and module.check_mode:
            result['changed'] = True

    # Set limits
    if state == 'absent':
        bhard = 0
        bsoft = 0
        ihard = 0
        isoft = 0
        rtbhard = 0
        rtbsoft = 0

    current_bsoft, current_bhard = quota_report(module, mountpoint, name, quota_type, 'b')
    current_isoft, current_ihard = quota_report(module, mountpoint, name, quota_type, 'i')
    current_rtbsoft, current_rtbhard = quota_report(module, mountpoint, name, quota_type, 'rtb')

    result['xfs_quota'] = dict(
        bsoft=current_bsoft,
        bhard=current_bhard,
        isoft=current_isoft,
        ihard=current_ihard,
        rtbsoft=current_rtbsoft,
        rtbhard=current_rtbhard
    )

    limit = []
    if bsoft is not None and int(bsoft) != current_bsoft:
        limit.append('bsoft=%s' % bsoft)
        result['bsoft'] = int(bsoft)

    if bhard is not None and int(bhard) != current_bhard:
        limit.append('bhard=%s' % bhard)
        result['bhard'] = int(bhard)

    if isoft is not None and isoft != current_isoft:
        limit.append('isoft=%s' % isoft)
        result['isoft'] = isoft

    if ihard is not None and ihard != current_ihard:
        limit.append('ihard=%s' % ihard)
        result['ihard'] = ihard

    if rtbsoft is not None and int(rtbsoft) != current_rtbsoft:
        limit.append('rtbsoft=%s' % rtbsoft)
        result['rtbsoft'] = int(rtbsoft)

    if rtbhard is not None and int(rtbhard) != current_rtbhard:
        limit.append('rtbhard=%s' % rtbhard)
        result['rtbhard'] = int(rtbhard)

    if len(limit) > 0 and not module.check_mode:
        if name == quota_default:
            cmd = 'limit %s -d %s' % (type_arg, ' '.join(limit))
        else:
            cmd = 'limit %s %s %s' % (type_arg, ' '.join(limit), name)

        rc, stdout, stderr = exec_quota(module, cmd, mountpoint)
        if rc != 0:
            result['cmd'] = cmd
            result['rc'] = rc
            result['stdout'] = stdout
            result['stderr'] = stderr
            module.fail_json(msg='Could not set limits.', **result)

        result['changed'] = True

    elif len(limit) > 0 and module.check_mode:
        result['changed'] = True

    module.exit_json(**result)


def quota_report(module, mountpoint, name, quota_type, used_type):
    soft = None
    hard = None

    if quota_type == 'project':
        type_arg = '-p'
    elif quota_type == 'user':
        type_arg = '-u'
    elif quota_type == 'group':
        type_arg = '-g'

    if used_type == 'b':
        used_arg = '-b'
        used_name = 'blocks'
        factor = 1024
    elif used_type == 'i':
        used_arg = '-i'
        used_name = 'inodes'
        factor = 1
    elif used_type == 'rtb':
        used_arg = '-r'
        used_name = 'realtime blocks'
        factor = 1024

    rc, stdout, stderr = exec_quota(module, 'report %s %s' % (type_arg, used_arg), mountpoint)

    if rc != 0:
        result = dict(
            changed=False,
            rc=rc,
            stdout=stdout,
            stderr=stderr,
        )
        module.fail_json(msg='Could not get quota report for %s.' % used_name, **result)

    for line in stdout.split('\n'):
        line = line.strip().split()
        if len(line) > 3 and line[0] == name:
            soft = int(line[2]) * factor
            hard = int(line[3]) * factor
            break

    return soft, hard


def exec_quota(module, cmd, mountpoint):
    cmd = ['xfs_quota', '-x', '-c'] + [cmd, mountpoint]
    (rc, stdout, stderr) = module.run_command(cmd, use_unsafe_shell=True)
    if "XFS_GETQUOTA: Operation not permitted" in stderr.split('\n') or \
            rc == 1 and 'xfs_quota: cannot set limits: Operation not permitted' in stderr.split('\n'):
        module.fail_json(msg='You need to be root or have CAP_SYS_ADMIN capability to perform this operation')

    return rc, stdout, stderr


def get_fs_by_mountpoint(mountpoint):
    mpr = None
    with open('/proc/mounts', 'r') as s:
        for line in s.readlines():
            mp = line.strip().split()
            if len(mp) == 6 and mp[1] == mountpoint and mp[2] == 'xfs':
                mpr = dict(zip(['spec', 'file', 'vfstype', 'mntopts', 'freq', 'passno'], mp))
                mpr['mntopts'] = mpr['mntopts'].split(',')
                break
    return mpr


def get_project_id(name):
    prjid = None
    with open('/etc/projid', 'r') as s:
        for line in s.readlines():
            line = line.strip().partition(':')
            if line[0] == name:
                prjid = line[2]
                break

    return prjid


if __name__ == '__main__':
    main()
