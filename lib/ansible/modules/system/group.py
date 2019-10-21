#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Stephen Fromm <sfromm@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: group
version_added: "0.0.2"
short_description: Add or remove groups
requirements:
- groupadd
- groupdel
- groupmod
description:
    - Manage presence of groups on a host.
    - For Windows targets, use the M(win_group) module instead.
options:
    name:
        description:
            - Name of the group to manage.
        type: str
        required: true
    gid:
        description:
            - Optional I(GID) to set for the group.
        type: int
    state:
        description:
            - Whether the group should be present or not on the remote host.
        type: str
        choices: [ absent, present ]
        default: present
    system:
        description:
            - If I(yes), indicates that the group created is a system group.
        type: bool
        default: no
    local:
        description:
            - Forces the use of "local" command alternatives on platforms that implement it.
            - This is useful in environments that use centralized authentication when you want to manipulate the local groups.
              (e.g. it uses C(lgroupadd) instead of C(groupadd)).
            - This requires that these commands exist on the targeted host, otherwise it will be a fatal error.
        type: bool
        default: no
        version_added: "2.6"
    non_unique:
        description:
            - This option allows to change the group ID to a non-unique value. Requires C(gid).
            - Not supported on macOS or BusyBox distributions.
        type: bool
        default: no
        version_added: "2.8"
seealso:
- module: user
- module: win_group
author:
- Stephen Fromm (@sfromm)
'''

EXAMPLES = '''
- name: Ensure group "somegroup" exists
  group:
    name: somegroup
    state: present
'''

import grp

from ansible.module_utils._text import to_bytes
from ansible.module_utils.basic import AnsibleModule, load_platform_subclass


class Group(object):
    """
    This is a generic Group manipulation class that is subclassed
    based on platform.

    A subclass may wish to override the following action methods:-
      - group_del()
      - group_add()
      - group_mod()

    All subclasses MUST define platform and distribution (which may be None).
    """

    platform = 'Generic'
    distribution = None
    GROUPFILE = '/etc/group'

    def __new__(cls, *args, **kwargs):
        return load_platform_subclass(Group, args, kwargs)

    def __init__(self, module):
        self.module = module
        self.state = module.params['state']
        self.name = module.params['name']
        self.gid = module.params['gid']
        self.system = module.params['system']
        self.local = module.params['local']
        self.non_unique = module.params['non_unique']

    def execute_command(self, cmd):
        return self.module.run_command(cmd)

    def group_del(self):
        if self.local:
            command_name = 'lgroupdel'
        else:
            command_name = 'groupdel'
        cmd = [self.module.get_bin_path(command_name, True), self.name]
        return self.execute_command(cmd)

    def _local_check_gid_exists(self):
        if self.gid:
            for gr in grp.getgrall():
                if self.gid == gr.gr_gid and self.name != gr.gr_name:
                    self.module.fail_json(msg="GID '{0}' already exists with group '{1}'".format(self.gid, gr.gr_name))

    def group_add(self, **kwargs):
        if self.local:
            command_name = 'lgroupadd'
            self._local_check_gid_exists()
        else:
            command_name = 'groupadd'
        cmd = [self.module.get_bin_path(command_name, True)]
        for key in kwargs:
            if key == 'gid' and kwargs[key] is not None:
                cmd.append('-g')
                cmd.append(str(kwargs[key]))
                if self.non_unique:
                    cmd.append('-o')
            elif key == 'system' and kwargs[key] is True:
                cmd.append('-r')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        if self.local:
            command_name = 'lgroupmod'
            self._local_check_gid_exists()
        else:
            command_name = 'groupmod'
        cmd = [self.module.get_bin_path(command_name, True)]
        info = self.group_info()
        for key in kwargs:
            if key == 'gid':
                if kwargs[key] is not None and info[2] != int(kwargs[key]):
                    cmd.append('-g')
                    cmd.append(str(kwargs[key]))
                    if self.non_unique:
                        cmd.append('-o')
        if len(cmd) == 1:
            return (None, '', '')
        if self.module.check_mode:
            return (0, '', '')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def group_exists(self):
        try:
            if grp.getgrnam(self.name):
                return True
        except KeyError:
            return False

    def group_info(self):
        if not self.group_exists():
            return False
        try:
            info = list(grp.getgrnam(self.name))
        except KeyError:
            return False
        return info


# ===========================================

class SunOS(Group):
    """
    This is a SunOS Group manipulation class. Solaris doesn't have
    the 'system' group concept.

    This overrides the following methods from the generic class:-
        - group_add()
    """

    platform = 'SunOS'
    distribution = None
    GROUPFILE = '/etc/group'

    def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('groupadd', True)]
        for key in kwargs:
            if key == 'gid' and kwargs[key] is not None:
                cmd.append('-g')
                cmd.append(str(kwargs[key]))
                if self.non_unique:
                    cmd.append('-o')
        cmd.append(self.name)
        return self.execute_command(cmd)


# ===========================================

class AIX(Group):
    """
    This is a AIX Group manipulation class.

    This overrides the following methods from the generic class:-
      - group_del()
      - group_add()
      - group_mod()
    """

    platform = 'AIX'
    distribution = None
    GROUPFILE = '/etc/group'

    def group_del(self):
        cmd = [self.module.get_bin_path('rmgroup', True), self.name]
        return self.execute_command(cmd)

    def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('mkgroup', True)]
        for key in kwargs:
            if key == 'gid' and kwargs[key] is not None:
                cmd.append('id=' + str(kwargs[key]))
            elif key == 'system' and kwargs[key] is True:
                cmd.append('-a')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        cmd = [self.module.get_bin_path('chgroup', True)]
        info = self.group_info()
        for key in kwargs:
            if key == 'gid':
                if kwargs[key] is not None and info[2] != int(kwargs[key]):
                    cmd.append('id=' + str(kwargs[key]))
        if len(cmd) == 1:
            return (None, '', '')
        if self.module.check_mode:
            return (0, '', '')
        cmd.append(self.name)
        return self.execute_command(cmd)


# ===========================================

class FreeBsdGroup(Group):
    """
    This is a FreeBSD Group manipulation class.

    This overrides the following methods from the generic class:-
      - group_del()
      - group_add()
      - group_mod()
    """

    platform = 'FreeBSD'
    distribution = None
    GROUPFILE = '/etc/group'

    def group_del(self):
        cmd = [self.module.get_bin_path('pw', True), 'groupdel', self.name]
        return self.execute_command(cmd)

    def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('pw', True), 'groupadd', self.name]
        if self.gid is not None:
            cmd.append('-g')
            cmd.append(str(self.gid))
            if self.non_unique:
                cmd.append('-o')
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        cmd = [self.module.get_bin_path('pw', True), 'groupmod', self.name]
        info = self.group_info()
        cmd_len = len(cmd)
        if self.gid is not None and int(self.gid) != info[2]:
            cmd.append('-g')
            cmd.append(str(self.gid))
            if self.non_unique:
                cmd.append('-o')
        # modify the group if cmd will do anything
        if cmd_len != len(cmd):
            if self.module.check_mode:
                return (0, '', '')
            return self.execute_command(cmd)
        return (None, '', '')


class DragonFlyBsdGroup(FreeBsdGroup):
    """
    This is a DragonFlyBSD Group manipulation class.
    It inherits all behaviors from FreeBsdGroup class.
    """

    platform = 'DragonFly'


# ===========================================

class DarwinGroup(Group):
    """
    This is a Mac macOS Darwin Group manipulation class.

    This overrides the following methods from the generic class:-
      - group_del()
      - group_add()
      - group_mod()

    group manipulation are done using dseditgroup(1).
    """

    platform = 'Darwin'
    distribution = None

    def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('dseditgroup', True)]
        cmd += ['-o', 'create']
        if self.gid is not None:
            cmd += ['-i', str(self.gid)]
        elif 'system' in kwargs and kwargs['system'] is True:
            gid = self.get_lowest_available_system_gid()
            if gid is not False:
                self.gid = str(gid)
                cmd += ['-i', str(self.gid)]
        cmd += ['-L', self.name]
        (rc, out, err) = self.execute_command(cmd)
        return (rc, out, err)

    def group_del(self):
        cmd = [self.module.get_bin_path('dseditgroup', True)]
        cmd += ['-o', 'delete']
        cmd += ['-L', self.name]
        (rc, out, err) = self.execute_command(cmd)
        return (rc, out, err)

    def group_mod(self, gid=None):
        info = self.group_info()
        if self.gid is not None and int(self.gid) != info[2]:
            cmd = [self.module.get_bin_path('dseditgroup', True)]
            cmd += ['-o', 'edit']
            if gid is not None:
                cmd += ['-i', str(gid)]
            cmd += ['-L', self.name]
            (rc, out, err) = self.execute_command(cmd)
            return (rc, out, err)
        return (None, '', '')

    def get_lowest_available_system_gid(self):
        # check for lowest available system gid (< 500)
        try:
            cmd = [self.module.get_bin_path('dscl', True)]
            cmd += ['/Local/Default', '-list', '/Groups', 'PrimaryGroupID']
            (rc, out, err) = self.execute_command(cmd)
            lines = out.splitlines()
            highest = 0
            for group_info in lines:
                parts = group_info.split(' ')
                if len(parts) > 1:
                    gid = int(parts[-1])
                    if gid > highest and gid < 500:
                        highest = gid
            if highest == 0 or highest == 499:
                return False
            return (highest + 1)
        except Exception:
            return False


class OpenBsdGroup(Group):
    """
    This is a OpenBSD Group manipulation class.

    This overrides the following methods from the generic class:-
      - group_del()
      - group_add()
      - group_mod()
    """

    platform = 'OpenBSD'
    distribution = None
    GROUPFILE = '/etc/group'

    def group_del(self):
        cmd = [self.module.get_bin_path('groupdel', True), self.name]
        return self.execute_command(cmd)

    def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('groupadd', True)]
        if self.gid is not None:
            cmd.append('-g')
            cmd.append(str(self.gid))
            if self.non_unique:
                cmd.append('-o')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        cmd = [self.module.get_bin_path('groupmod', True)]
        info = self.group_info()
        if self.gid is not None and int(self.gid) != info[2]:
            cmd.append('-g')
            cmd.append(str(self.gid))
            if self.non_unique:
                cmd.append('-o')
        if len(cmd) == 1:
            return (None, '', '')
        if self.module.check_mode:
            return (0, '', '')
        cmd.append(self.name)
        return self.execute_command(cmd)


# ===========================================

class NetBsdGroup(Group):
    """
    This is a NetBSD Group manipulation class.

    This overrides the following methods from the generic class:-
      - group_del()
      - group_add()
      - group_mod()
    """

    platform = 'NetBSD'
    distribution = None
    GROUPFILE = '/etc/group'

    def group_del(self):
        cmd = [self.module.get_bin_path('groupdel', True), self.name]
        return self.execute_command(cmd)

    def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('groupadd', True)]
        if self.gid is not None:
            cmd.append('-g')
            cmd.append(str(self.gid))
            if self.non_unique:
                cmd.append('-o')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        cmd = [self.module.get_bin_path('groupmod', True)]
        info = self.group_info()
        if self.gid is not None and int(self.gid) != info[2]:
            cmd.append('-g')
            cmd.append(str(self.gid))
            if self.non_unique:
                cmd.append('-o')
        if len(cmd) == 1:
            return (None, '', '')
        if self.module.check_mode:
            return (0, '', '')
        cmd.append(self.name)
        return self.execute_command(cmd)


# ===========================================


class BusyBoxGroup(Group):
    """
    BusyBox group manipulation class for systems that have addgroup and delgroup.

    It overrides the following methods:
        - group_add()
        - group_del()
        - group_mod()
    """

    def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('addgroup', True)]
        if self.gid is not None:
            cmd.extend(['-g', str(self.gid)])

        if self.system:
            cmd.append('-S')

        cmd.append(self.name)

        return self.execute_command(cmd)

    def group_del(self):
        cmd = [self.module.get_bin_path('delgroup', True), self.name]
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        # Since there is no groupmod command, modify /etc/group directly
        info = self.group_info()
        if self.gid is not None and self.gid != info[2]:
            with open('/etc/group', 'rb') as f:
                b_groups = f.read()

            b_name = to_bytes(self.name)
            b_current_group_string = b'%s:x:%d:' % (b_name, info[2])
            b_new_group_string = b'%s:x:%d:' % (b_name, self.gid)

            if b':%d:' % self.gid in b_groups:
                self.module.fail_json(msg="gid '{gid}' in use".format(gid=self.gid))

            if self.module.check_mode:
                return 0, '', ''
            b_new_groups = b_groups.replace(b_current_group_string, b_new_group_string)
            with open('/etc/group', 'wb') as f:
                f.write(b_new_groups)
            return 0, '', ''

        return None, '', ''


class AlpineGroup(BusyBoxGroup):

    platform = 'Linux'
    distribution = 'Alpine'


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            name=dict(type='str', required=True),
            gid=dict(type='int'),
            system=dict(type='bool', default=False),
            local=dict(type='bool', default=False),
            non_unique=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        required_if=[
            ['non_unique', True, ['gid']],
        ],
    )

    group = Group(module)

    module.debug('Group instantiated - platform %s' % group.platform)
    if group.distribution:
        module.debug('Group instantiated - distribution %s' % group.distribution)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = group.name
    result['state'] = group.state

    if group.state == 'absent':

        if group.group_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = group.group_del()
            if rc != 0:
                module.fail_json(name=group.name, msg=err)

    elif group.state == 'present':

        if not group.group_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = group.group_add(gid=group.gid, system=group.system)
        else:
            (rc, out, err) = group.group_mod(gid=group.gid)

        if rc is not None and rc != 0:
            module.fail_json(name=group.name, msg=err)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    if group.group_exists():
        info = group.group_info()
        result['system'] = group.system
        result['gid'] = info[2]

    module.exit_json(**result)


if __name__ == '__main__':
    main()
