#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Johan Wiren <johan.wiren.se@gmail.com>
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
#

DOCUMENTATION = '''
---
module: zfs
short_description: Manage zfs
description:
  - Manages ZFS file systems, volumes, clones and snapshots.
version_added: "1.1"
options:
  name:
    description:
      - File system, snapshot or volume name e.g. C(rpool/myfs)
    required: true
  state:
    description:
      - Whether to create (C(present)), or remove (C(absent)) a 
        file system, snapshot or volume. All parents/children
        will be created/destroyed as needed to reach the desired state.
    choices: ['present', 'absent']
    required: true
  origin:
    description:
      - Snapshot from which to create a clone
    default: null
    required: false
  key_value:
    description:
      - The C(zfs) module takes key=value pairs for zfs properties to be set. See the zfs(8) man page for more information.
    default: null
    required: false

author: "Johan Wiren (@johanwiren)"
'''

EXAMPLES = '''
# Create a new file system called myfs in pool rpool with the setuid property turned off
- zfs: name=rpool/myfs state=present setuid=off

# Create a new volume called myvol in pool rpool.
- zfs: name=rpool/myvol state=present volsize=10M

# Create a snapshot of rpool/myfs file system.
- zfs: name=rpool/myfs@mysnapshot state=present

# Create a new file system called myfs2 with snapdir enabled
- zfs: name=rpool/myfs2 state=present snapdir=enabled

# Create a new file system by cloning a snapshot
- zfs: name=rpool/cloned_fs state=present origin=rpool/myfs@mysnapshot

# Destroy a filesystem
- zfs: name=rpool/myfs state=absent
'''


import os


class Zfs(object):

    def __init__(self, module, name, properties):
        self.module = module
        self.name = name
        self.properties = properties
        self.changed = False
        self.is_solaris = os.uname()[0] == 'SunOS'
        self.pool = name.split('/')[0]
        self.zfs_cmd = module.get_bin_path('zfs', True)
        self.zpool_cmd = module.get_bin_path('zpool', True)
        self.enhanced_sharing = self.check_enhanced_sharing()

    def check_enhanced_sharing(self):
        if os.uname()[0] == 'SunOS':
            cmd = [self.zpool_cmd]
            cmd.extend(['get', 'version'])
            cmd.append(self.pool)
            (rc, out, err) = self.module.run_command(cmd, check_rc=True)
            version = out.splitlines()[-1].split()[2]
            if int(version) >= 34:
                return True
        return False

    def exists(self):
        cmd = [self.zfs_cmd, 'list', '-t', 'all', self.name]
        (rc, out, err) = self.module.run_command(' '.join(cmd))
        if rc == 0:
            return True
        else:
            return False

    def create(self):
        if self.module.check_mode:
            self.changed = True
            return
        properties = self.properties
        volsize = properties.pop('volsize', None)
        volblocksize = properties.pop('volblocksize', None)
        origin = properties.pop('origin', None)
        cmd = [self.zfs_cmd]

        if "@" in self.name:
            action = 'snapshot'
        elif origin:
            action = 'clone'
        else:
            action = 'create'

        cmd.append(action)

        if action in ['create', 'clone']:
            cmd += ['-p']

        if volsize:
            cmd += ['-V', volsize]
        if volblocksize:
            cmd += ['-b', 'volblocksize']
        if properties:
            for prop, value in properties.iteritems():
                cmd += ['-o', '%s="%s"' % (prop, value)]
        if origin:
            cmd.append(origin)
        cmd.append(self.name)
        (rc, out, err) = self.module.run_command(' '.join(cmd))
        if rc == 0:
            self.changed = True
        else:
            self.module.fail_json(msg=err)

    def destroy(self):
        if self.module.check_mode:
            self.changed = True
            return
        cmd = [self.zfs_cmd, 'destroy', '-R', self.name]
        (rc, out, err) = self.module.run_command(' '.join(cmd))
        if rc == 0:
            self.changed = True
        else:
            self.module.fail_json(msg=err)

    def set_property(self, prop, value):
        if self.module.check_mode:
            self.changed = True
            return
        cmd = [self.zfs_cmd, 'set', prop + '=' + str(value), self.name]
        (rc, out, err) = self.module.run_command(cmd)
        if rc == 0:
            self.changed = True
        else:
            self.module.fail_json(msg=err)

    def set_properties_if_changed(self):
        current_properties = self.get_current_properties()
        for prop, value in self.properties.iteritems():
            if current_properties.get(prop, None) != value:
                self.set_property(prop, value)

    def get_current_properties(self):
        cmd = [self.zfs_cmd, 'get', '-H']
        if self.enhanced_sharing:
            cmd += ['-e']
        cmd += ['all', self.name]
        rc, out, err = self.module.run_command(" ".join(cmd))
        properties = dict()
        for prop, value, source in [l.split('\t')[1:4] for l in out.splitlines()]:
            if source == 'local':
                properties[prop] = value
        # Add alias for enhanced sharing properties
        properties['sharenfs'] = properties.get('share.nfs', None)
        properties['sharesmb'] = properties.get('share.smb', None)
        return properties


def main():

    module = AnsibleModule(
        argument_spec = dict(
            name =         dict(type='str', required=True),
            state =        dict(type='str', required=True, choices=['present', 'absent']),
            # No longer used. Kept here to not interfere with zfs properties
            createparent = dict(type='bool', required=False)
            ),
        supports_check_mode=True,
        check_invalid_arguments=False
        )

    state = module.params.pop('state')
    name = module.params.pop('name')

    # Get all valid zfs-properties
    properties = dict()
    for prop, value in module.params.iteritems():
        # All freestyle params are zfs properties
        if prop not in module.argument_spec:
            # Reverse the boolification of freestyle zfs properties
            if type(value) == bool:
                if value is True:
                    properties[prop] = 'on'
                else:
                    properties[prop] = 'off'
            else:
                properties[prop] = value

    result = {}
    result['name'] = name
    result['state'] = state

    zfs = Zfs(module, name, properties)

    if state == 'present':
        if zfs.exists():
            zfs.set_properties_if_changed()
        else:
            zfs.create()

    elif state == 'absent':
        if zfs.exists():
            zfs.destroy()

    result.update(zfs.properties)
    result['changed'] = zfs.changed
    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
