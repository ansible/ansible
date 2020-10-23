#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Johan Wiren <johan.wiren.se@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: zfs
short_description: Manage zfs
description:
  - Manages ZFS file systems, volumes, clones and snapshots
version_added: "1.1"
options:
  name:
    description:
      - File system, snapshot or volume name e.g. C(rpool/myfs).
    required: true
  state:
    description:
      - Whether to create (C(present)), or remove (C(absent)) a
        file system, snapshot or volume. All parents/children
        will be created/destroyed as needed to reach the desired state.
    choices: [ absent, present ]
    required: true
  origin:
    description:
      - Snapshot from which to create a clone.
  extra_zfs_properties:
    description:
      - A dictionary of zfs properties to be set.
      - See the zfs(8) man page for more information.
    version_added: "2.5"
author:
- Johan Wiren (@johanwiren)
'''

EXAMPLES = '''
- name: Create a new file system called myfs in pool rpool with the setuid property turned off
  zfs:
    name: rpool/myfs
    state: present
    extra_zfs_properties:
      setuid: off

- name: Create a new volume called myvol in pool rpool.
  zfs:
    name: rpool/myvol
    state: present
    extra_zfs_properties:
      volsize: 10M

- name: Create a snapshot of rpool/myfs file system.
  zfs:
    name: rpool/myfs@mysnapshot
    state: present

- name: Create a new file system called myfs2 with snapdir enabled
  zfs:
    name: rpool/myfs2
    state: present
    extra_zfs_properties:
      snapdir: enabled

- name: Create a new file system by cloning a snapshot
  zfs:
    name: rpool/cloned_fs
    state: present
    origin: rpool/myfs@mysnapshot

- name: Destroy a filesystem
  zfs:
    name: rpool/myfs
    state: absent
'''

import os

from ansible.module_utils.basic import AnsibleModule


class Zfs(object):

    def __init__(self, module, name, properties):
        self.module = module
        self.name = name
        self.properties = properties
        self.changed = False
        self.zfs_cmd = module.get_bin_path('zfs', True)
        self.zpool_cmd = module.get_bin_path('zpool', True)
        self.pool = name.split('/')[0].split('@')[0]
        self.is_solaris = os.uname()[0] == 'SunOS'
        self.is_openzfs = self.check_openzfs()
        self.enhanced_sharing = self.check_enhanced_sharing()

    def check_openzfs(self):
        cmd = [self.zpool_cmd]
        cmd.extend(['get', 'version'])
        cmd.append(self.pool)
        (rc, out, err) = self.module.run_command(cmd, check_rc=True)
        version = out.splitlines()[-1].split()[2]
        if version == '-':
            return True
        if int(version) == 5000:
            return True
        return False

    def check_enhanced_sharing(self):
        if self.is_solaris and not self.is_openzfs:
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
        origin = self.module.params.get('origin', None)
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

        if properties:
            for prop, value in properties.items():
                if prop == 'volsize':
                    cmd += ['-V', value]
                elif prop == 'volblocksize':
                    cmd += ['-b', value]
                else:
                    cmd += ['-o', '%s="%s"' % (prop, value)]
        if origin and action == 'clone':
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
        for prop, value in self.properties.items():
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
        if self.enhanced_sharing:
            properties['sharenfs'] = properties.get('share.nfs', None)
            properties['sharesmb'] = properties.get('share.smb', None)
        return properties


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', required=True, choices=['absent', 'present']),
            origin=dict(type='str', default=None),
            extra_zfs_properties=dict(type='dict', default={}),
        ),
        supports_check_mode=True,
    )

    state = module.params.get('state')
    name = module.params.get('name')

    if module.params.get('origin') and '@' in name:
        module.fail_json(msg='cannot specify origin when operating on a snapshot')

    # Reverse the boolification of zfs properties
    for prop, value in module.params['extra_zfs_properties'].items():
        if isinstance(value, bool):
            if value is True:
                module.params['extra_zfs_properties'][prop] = 'on'
            else:
                module.params['extra_zfs_properties'][prop] = 'off'
        else:
            module.params['extra_zfs_properties'][prop] = value

    result = dict(
        name=name,
        state=state,
    )

    zfs = Zfs(module, name, module.params['extra_zfs_properties'])

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


if __name__ == '__main__':
    main()
