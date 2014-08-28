#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Stephen Fromm <sfromm@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: group
author: Stephen Fromm
version_added: "0.0.2"
short_description: Add or remove groups
requirements: [ groupadd, groupdel, groupmod ]
description:
    - Manage presence of groups on a host.
options:
    name:
        required: true
        description:
            - Name of the group to manage.
    gid:
        required: false
        description:
            - Optional I(GID) to set for the group.
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the group should be present or not on the remote host.
    system:
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        description:
            - If I(yes), indicates that the group created is a system group.

'''

EXAMPLES = '''
# Example group command from Ansible Playbooks
- group: name=somegroup state=present
'''

import grp
import syslog
import platform

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
        self.module     = module
        self.state      = module.params['state']
        self.name       = module.params['name']
        self.gid        = module.params['gid']
        self.system     = module.params['system']
        self.syslogging = False

    def execute_command(self, cmd):
        if self.syslogging:
            syslog.openlog('ansible-%s' % os.path.basename(__file__))
            syslog.syslog(syslog.LOG_NOTICE, 'Command %s' % '|'.join(cmd))

        return self.module.run_command(cmd)

    def group_del(self):
        cmd = [self.module.get_bin_path('groupdel', True), self.name]
        return self.execute_command(cmd)

    def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('groupadd', True)]
        for key in kwargs:
            if key == 'gid' and kwargs[key] is not None:
                cmd.append('-g')
                cmd.append(kwargs[key])
            elif key == 'system' and kwargs[key] == True:
                cmd.append('-r')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        cmd = [self.module.get_bin_path('groupmod', True)]
        info = self.group_info()
        for key in kwargs:
            if key == 'gid':
                if kwargs[key] is not None and info[2] != int(kwargs[key]):
                    cmd.append('-g')
                    cmd.append(kwargs[key])
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
                cmd.append(kwargs[key])
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
                cmd.append('id='+kwargs[key])
            elif key == 'system' and kwargs[key] == True:
                cmd.append('-a')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        cmd = [self.module.get_bin_path('chgroup', True)]
        info = self.group_info()
        for key in kwargs:
            if key == 'gid':
                if kwargs[key] is not None and info[2] != int(kwargs[key]):
                    cmd.append('id='+kwargs[key])
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
            cmd.append('-g %d' % int(self.gid))
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        cmd = [self.module.get_bin_path('pw', True), 'groupmod', self.name]
        info = self.group_info()
        cmd_len = len(cmd)
        if self.gid is not None and int(self.gid) != info[2]:
            cmd.append('-g %d' % int(self.gid))
        # modify the group if cmd will do anything
        if cmd_len != len(cmd):
            if self.module.check_mode:
                return (0, '', '')
            return self.execute_command(cmd)
        return (None, '', '')

# ===========================================



class DarwinGroup(Group):
    """
    This is a Mac OS X Darwin Group manipulation class.

    This overrides the following methods from the generic class:-
      - group_del()
      - group_add()
      - group_mod()

    group manupulation are done using dseditgroup(1).
    """

    platform = 'Darwin'
    distribution = None

    def group_add(self, **kwargs):
        cmd = [self.module.get_bin_path('dseditgroup', True)]
        cmd += [ '-o', 'create' ]
        cmd += [ '-i', self.gid ]
        cmd += [ '-L', self.name ]
        (rc, out, err) = self.execute_command(cmd)
        return (rc, out, err)

    def group_del(self):
        cmd = [self.module.get_bin_path('dseditgroup', True)]
        cmd += [ '-o', 'delete' ]
        cmd += [ '-L', self.name ]
        (rc, out, err) = self.execute_command(cmd)
        return (rc, out, err)

    def group_mod(self):
        info = self.group_info()
        if self.gid is not None and int(self.gid) != info[2]:
            cmd = [self.module.get_bin_path('dseditgroup', True)]
            cmd += [ '-o', 'edit' ]
            cmd += [ '-i', self.gid ]
            cmd += [ '-L', self.name ]
            (rc, out, err) = self.execute_command(cmd)
            return (rc, out, err)
        return (None, '', '')

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
            cmd.append('%d' % int(self.gid))
        cmd.append(self.name)
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        cmd = [self.module.get_bin_path('groupmod', True)]
        info = self.group_info()
        cmd_len = len(cmd)
        if self.gid is not None and int(self.gid) != info[2]:
            cmd.append('-g')
            cmd.append('%d' % int(self.gid))
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
            cmd.append('%d' % int(self.gid))
        cmd.append(self.name)
        return self.execute_command(cmd)

    def group_mod(self, **kwargs):
        cmd = [self.module.get_bin_path('groupmod', True)]
        info = self.group_info()
        cmd_len = len(cmd)
        if self.gid is not None and int(self.gid) != info[2]:
            cmd.append('-g')
            cmd.append('%d' % int(self.gid))
        if len(cmd) == 1:
            return (None, '', '')
        if self.module.check_mode:
            return (0, '', '')
        cmd.append(self.name)
        return self.execute_command(cmd)

# ===========================================

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            name=dict(required=True, type='str'),
            gid=dict(default=None, type='str'),
            system=dict(default=False, type='bool'),
        ),
        supports_check_mode=True
    )

    group = Group(module)

    if group.syslogging:
        syslog.openlog('ansible-%s' % os.path.basename(__file__))
        syslog.syslog(syslog.LOG_NOTICE, 'Group instantiated - platform %s' % group.platform)
        if user.distribution:
            syslog.syslog(syslog.LOG_NOTICE, 'Group instantiated - distribution %s' % group.distribution)

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

# import module snippets
from ansible.module_utils.basic import *
main()
