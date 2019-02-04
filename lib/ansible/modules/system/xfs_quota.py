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

DOCUMENTATION = '''
---
module: xfs_quota
short_description: Set Quotas on XFS filesystems
descrition:
  - Configure Quotas on XFS filesystems. /etc/projects and /etc/projid needs to be configured before calling this module when setting project quotas.
version_added: "2.8"
author: "William Leemans (@bushvin) <willie@elaba.net>"
options:
  type:
    description:
      - The xfs quota type.
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
      - the mountpoint on which to apply the quotas
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

RETURN = ''' # '''

import grp
import json
import os
import pwd
import sys

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import human_to_bytes


def main():
    module = AnsibleModule(
        argument_spec=dict(
            bhard=dict(type='str', required=False, default=None),
            bsoft=dict(type='str', required=False, default=None),
            ihard=dict(type='int', required=False, default=None),
            isoft=dict(type='int', required=False, default=None),
            mountpoint=dict(type='str', required=True),
            name=dict(type='str', required=False, default=None),
            rtbhard=dict(type='str', required=False, default=None),
            rtbsoft=dict(type='str', required=False, default=None),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
            type=dict(type='str', required=True, choices=['user', 'group', 'project'])
        ),
        supports_check_mode=True
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

    changed = False

    if os.getuid() != 0:
        module.fail_json(msg='You need to be root to run this module')

    if not os.path.ismount(mountpoint):
        module.fail_json(msg='%s is not a mountpoint' % mountpoint)

    mp = get_fs_by_mountpoint(mountpoint)
    if mp is None:
        module.fail_json(msg='%s is not a mountpoint or not located on an xfs filesystem.' % mountpoint)

    if quota_type == 'user':
        type_arg = '-u'
        quota_default = 'root'
        if name is None:
            name = quota_default

        if 'uquota' not in mp['mntopts'] \
                and 'usrquota' not in mp['mntopts'] \
                and 'quota' not in mp['mntopts'] \
                and 'uqnoenforce' not in mp['mntopts'] \
                and 'qnoenforce' not in mp['mntopts']:
            module.fail_json(
                msg='%s is not mounted with the uquota/usrquota/quota/uqnoenforce/qnoenforce option.'
                    % mountpoint
            )
        try:
            pwd.getpwnam(name)
        except KeyError as e:
            module.fail_json(msg='User %s doesn\'t exist.' % name)

    if quota_type == 'group':
        type_arg = '-g'
        quota_default = 'root'
        if name is None:
            name = quota_default

        if 'gquota' not in mp['mntopts'] and 'grpquota' not in mp['mntopts'] and 'gqnoenforce' not in mp['mntopts']:
            module.fail_json(
                msg='%s is not mounted with the gquota/grpquota/gqnoenforce option. (current options: %s)'
                    % (mountpoint, mp['mntopts'])
            )
        try:
            grp.getgrnam(name)
        except KeyError as e:
            module.fail_json(msg='User %s doesn\'t exist.' % name)

    elif quota_type == 'project':
        type_arg = '-p'
        quota_default = '#0'
        if name is None:
            name = quota_default

        if 'pquota' not in mp['mntopts'] and 'prjquota' not in mp['mntopts'] and 'pqnoenforce' not in mp['mntopts']:
            module.fail_json(msg='%s is not mounted with the pquota/prjquota/pqnoenforce option.' % mountpoint)

        if name != quota_default and not os.path.isfile('/etc/projects'):
            module.fail_json(msg='/etc/projects doesn\'t exist.')

        if name != quota_default and not os.path.isfile('/etc/projid'):
            module.fail_json(msg='/etc/projid doesn\'t exist.')

        if name != quota_default and name is not None and get_project_id(name) is None:
            module.fail_json(msg='%s hasn\'t been defined in /etc/projid.' % name)

        prj_set = True
        if name != quota_default:
            cmd = 'project %s' % name
            r = exec_quota(module, cmd, mountpoint)
            if r['rc'] != 0:
                module.fail_json(msg='Could not get project state.', cmd=cmd, retval=r)
            else:
                for line in r['stdout']:
                    if '%s - project identifier is not set' in line:
                        prj_set = False
                        break

        if not prj_set and not module.check_mode:
            cmd = 'project -s'
            r = exec_quota(module, cmd, mountpoint)
            if r['rc'] != 0:
                module.fail_json(msg='Could not get quota realtime block report.', cmd=cmd, retval=r)
            else:
                changed = True
        elif not prj_set and module.check_mode:
            changed = True

    changed = False

    # Set limits
    if state == 'absent':
        bhard = 0
        bsoft = 0
        ihard = 0
        isoft = 0
        rtbhard = 0
        rtbsoft = 0

    if bsoft is not None or bhard is not None:
        current_bsoft, current_bhard = quota_report(module, mountpoint, name, quota_type, 'b')

    if isoft is not None or ihard is not None:
        current_isoft, current_ihard = quota_report(module, mountpoint, name, quota_type, 'i')

    if rtbsoft is not None or rtbhard is not None:
        current_rtbsoft, current_rtbhard = quota_report(module, mountpoint, name, quota_type, 'rtb')

    limit = []
    if bsoft is not None and int(bsoft / 1024) != current_bsoft:
        limit.append('bsoft=%s' % bsoft)

    if bhard is not None and int(bhard / 1024) != current_bhard:
        limit.append('bhard=%s' % bhard)

    if isoft is not None and isoft != current_isoft:
        limit.append('isoft=%s' % isoft)

    if ihard is not None and ihard != current_ihard:
        limit.append('ihard=%s' % ihard)

    if rtbsoft is not None and int(rtbsoft / 1024) != current_rtbsoft:
        limit.append('rtbsoft=%s' % rtbsoft)

    if rtbhard is not None and int(rtbhard / 1024) != current_rtbhard:
        limit.append('rtbhard=%s' % rtbhard)

    if len(limit) > 0 and not module.check_mode:
        if name == quota_default:
            cmd = 'limit %s -d %s' % (type_arg, ' '.join(limit))
        else:
            cmd = 'limit %s %s %s' % (type_arg, ' '.join(limit), name)

        r = exec_quota(module, cmd, mountpoint)
        if r['rc'] != 0:
            module.fail_json(msg='Could not set limits.', cmd=cmd, retval=r)
        else:
            changed = True
    elif len(limit) > 0 and module.check_mode:
        changed = True

    module.exit_json(changed=changed)

    return True


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
    elif used_type == 'i':
        used_arg = '-i'
        used_name = 'inodes'
    elif used_type == 'rtb':
        used_arg = '-r'
        used_name = 'realtime blocks'

    r = exec_quota(module, 'report %s %s' % (type_arg, used_arg), mountpoint)

    if r['rc'] != 0:
        module.fail_json(msg='Could not get quota report for %s (%s).' % (used_name, r['stderr']))
    else:
        for line in r['stdout']:
            line = line.strip().split()
            if len(line) and line[0] == name:
                soft = int(line[2])
                hard = int(line[3])
                break

    return soft, hard


def exec_quota(module, cmd, mountpoint):
    cmd = ['xfs_quota', '-x', '-c'] + [cmd, mountpoint]
    (rc, stdout, stderr) = module.run_command(cmd, use_unsafe_shell=True)
    return {'rc': rc, 'stdout': stdout.split('\n'), 'stderr': stderr.split('\n')}


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
