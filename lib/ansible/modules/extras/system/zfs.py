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
  - Manages ZFS file systems on Solaris and FreeBSD. Can manage file systems, volumes and snapshots. See zfs(1M) for more information about the properties.
version_added: "1.1"
options:
  name:
    description:
      - File system, snapshot or volume name e.g. C(rpool/myfs)
    required: true
  state:
    description:
      - Whether to create (C(present)), or remove (C(absent)) a file system, snapshot or volume.
    required: true
    choices: [present, absent]
  aclinherit:
    description:
      - The aclinherit property.
    required: False
    choices: [discard,noallow,restricted,passthrough,passthrough-x]
  aclmode:
    description:
      - The aclmode property.
    required: False
    choices: [discard,groupmask,passthrough]
  atime:
    description:
      - The atime property.
    required: False
    choices: ['on','off']
  canmount:
    description:
      - The canmount property.
    required: False
    choices: ['on','off','noauto']
  casesensitivity:
    description:
      - The casesensitivity property.
    required: False
    choices: [sensitive,insensitive,mixed]
  checksum:
    description:
      - The checksum property.
    required: False
    choices: ['on','off',fletcher2,fletcher4,sha256]
  compression:
    description:
      - The compression property.
    required: False
    choices: ['on','off',lzjb,gzip,gzip-1,gzip-2,gzip-3,gzip-4,gzip-5,gzip-6,gzip-7,gzip-8,gzip-9,lz4,zle]
  copies:
    description:
      - The copies property.
    required: False
    choices: [1,2,3]
  dedup:
    description:
      - The dedup property.
    required: False
    choices: ['on','off']
  devices:
    description:
      - The devices property.
    required: False
    choices: ['on','off']
  exec:
    description:
      - The exec property.
    required: False
    choices: ['on','off']
  jailed:
    description:
      - The jailed property.
    required: False
    choices: ['on','off']
  logbias:
    description:
      - The logbias property.
    required: False
    choices: [latency,throughput]
  mountpoint:
    description:
      - The mountpoint property.
    required: False
  nbmand:
    description:
      - The nbmand property.
    required: False
    choices: ['on','off']
  normalization:
    description:
      - The normalization property.
    required: False
    choices: [none,formC,formD,formKC,formKD]
  primarycache:
    description:
      - The primarycache property.
    required: False
    choices: [all,none,metadata]
  quota:
    description:
      - The quota property.
    required: False
  readonly:
    description:
      - The readonly property.
    required: False
    choices: ['on','off']
  recordsize:
    description:
      - The recordsize property.
    required: False
  refquota:
    description:
      - The refquota property.
    required: False
  refreservation:
    description:
      - The refreservation property.
    required: False
  reservation:
    description:
      - The reservation property.
    required: False
  secondarycache:
    description:
      - The secondarycache property.
    required: False
    choices: [all,none,metadata]
  setuid:
    description:
      - The setuid property.
    required: False
    choices: ['on','off']
  shareiscsi:
    description:
      - The shareiscsi property.
    required: False
    choices: ['on','off']
  sharenfs:
    description:
      - The sharenfs property.
    required: False
  sharesmb:
    description:
      - The sharesmb property.
    required: False
  snapdir:
    description:
      - The snapdir property.
    required: False
    choices: [hidden,visible]
  sync:
    description:
      - The sync property.
    required: False
    choices: ['on','off']
  utf8only:
    description:
      - The utf8only property.
    required: False
    choices: ['on','off']
  volsize:
    description:
      - The volsize property.
    required: False
  volblocksize:
    description:
      - The volblocksize property.
    required: False
  vscan:
    description:
      - The vscan property.
    required: False
    choices: ['on','off']
  xattr:
    description:
      - The xattr property.
    required: False
    choices: ['on','off']
  zoned:
    description:
      - The zoned property.
    required: False
    choices: ['on','off']
author: Johan Wiren
'''

EXAMPLES = '''
# Create a new file system called myfs in pool rpool
- zfs: name=rpool/myfs state=present

# Create a new volume called myvol in pool rpool. 
- zfs: name=rpool/myvol state=present volsize=10M

# Create a snapshot of rpool/myfs file system.
- zfs: name=rpool/myfs@mysnapshot state=present

# Create a new file system called myfs2 with snapdir enabled
- zfs: name=rpool/myfs2 state=present snapdir=enabled
'''


import os

class Zfs(object):
    def __init__(self, module, name, properties):
        self.module = module
        self.name = name
        self.properties = properties
        self.changed = False

        self.immutable_properties = [ 'casesensitivity', 'normalization', 'utf8only' ]

    def exists(self):
        cmd = [self.module.get_bin_path('zfs', True)]
        cmd.append('list')
        cmd.append('-t all')
        cmd.append(self.name)
        (rc, out, err) = self.module.run_command(' '.join(cmd))
        if rc == 0:
            return True
        else:
            return False

    def create(self):
        if self.module.check_mode:
            self.changed = True
            return
        properties=self.properties
        volsize = properties.pop('volsize', None)
        volblocksize = properties.pop('volblocksize', None)
        if "@" in self.name:
            action = 'snapshot'
        else:
            action = 'create'

        cmd = [self.module.get_bin_path('zfs', True)]
        cmd.append(action)
        if volblocksize:
            cmd.append('-b %s' % volblocksize)
        if properties:
            for prop, value in properties.iteritems():
                cmd.append('-o %s="%s"' % (prop, value))
        if volsize:
            cmd.append('-V')
            cmd.append(volsize)
        cmd.append(self.name)
        (rc, err, out) = self.module.run_command(' '.join(cmd))
        if rc == 0:
            self.changed=True
        else:
            self.module.fail_json(msg=out)

    def destroy(self):
        if self.module.check_mode:
            self.changed = True
            return
        cmd = [self.module.get_bin_path('zfs', True)]
        cmd.append('destroy')
        cmd.append(self.name)
        (rc, err, out) = self.module.run_command(' '.join(cmd))
        if rc == 0:
            self.changed = True
        else:
            self.module.fail_json(msg=out)

    def set_property(self, prop, value):
        if self.module.check_mode:
            self.changed = True
            return
        cmd = self.module.get_bin_path('zfs', True)
        args = [cmd, 'set', prop + '=' + value, self.name]
        (rc, err, out) = self.module.run_command(args)
        if rc == 0:
            self.changed = True
        else:
            self.module.fail_json(msg=out)

    def set_properties_if_changed(self):
        current_properties = self.get_current_properties()
        for prop, value in self.properties.iteritems():
            if current_properties[prop] != value:
                if prop in self.immutable_properties:
                    self.module.fail_json(msg='Cannot change property %s after creation.' % prop)
                else:
                    self.set_property(prop, value) 

    def get_current_properties(self):
        def get_properties_by_name(propname):
            cmd = [self.module.get_bin_path('zfs', True)]
            cmd += ['get', '-H', propname, self.name]
            rc, out, err = self.module.run_command(cmd)
            return [l.split('\t')[1:3] for l in out.splitlines()]
        properties = dict(get_properties_by_name('all'))
        if 'share.*' in properties:
            # Some ZFS pools list the sharenfs and sharesmb properties
            # hierarchically as share.nfs and share.smb respectively.
            del properties['share.*']
            for p, v in get_properties_by_name('share.all'):
                alias = p.replace('.', '')  # share.nfs -> sharenfs (etc)
                properties[alias] = v
        return properties

    def run_command(self, cmd):
        progname = cmd[0]
        cmd[0] = module.get_bin_path(progname, True)
        return module.run_command(cmd)

def main():

    # FIXME: should use dict() constructor like other modules, required=False is default
    module = AnsibleModule(
        argument_spec = {
            'name':            {'required': True},
            'state':           {'required': True,  'choices':['present', 'absent']},
            'aclinherit':      {'required': False, 'choices':['discard', 'noallow', 'restricted', 'passthrough', 'passthrough-x']},
            'aclmode':         {'required': False, 'choices':['discard', 'groupmask', 'passthrough']},
            'atime':           {'required': False, 'choices':['on', 'off']},
            'canmount':        {'required': False, 'choices':['on', 'off', 'noauto']},
            'casesensitivity': {'required': False, 'choices':['sensitive', 'insensitive', 'mixed']},
            'checksum':        {'required': False, 'choices':['on', 'off', 'fletcher2', 'fletcher4', 'sha256']},
            'compression':     {'required': False, 'choices':['on', 'off', 'lzjb', 'gzip', 'gzip-1', 'gzip-2', 'gzip-3', 'gzip-4', 'gzip-5', 'gzip-6', 'gzip-7', 'gzip-8', 'gzip-9', 'lz4', 'zle']},
            'copies':          {'required': False, 'choices':['1', '2', '3']},
            'dedup':           {'required': False, 'choices':['on', 'off']},
            'devices':         {'required': False, 'choices':['on', 'off']},
            'exec':            {'required': False, 'choices':['on', 'off']},
            # Not supported
            #'groupquota':      {'required': False},
            'jailed':          {'required': False, 'choices':['on', 'off']},
            'logbias':         {'required': False, 'choices':['latency', 'throughput']},
            'mountpoint':      {'required': False},
            'nbmand':          {'required': False, 'choices':['on', 'off']},
            'normalization':   {'required': False, 'choices':['none', 'formC', 'formD', 'formKC', 'formKD']},
            'primarycache':    {'required': False, 'choices':['all', 'none', 'metadata']},
            'quota':           {'required': False},
            'readonly':        {'required': False, 'choices':['on', 'off']},
            'recordsize':      {'required': False},
            'refquota':        {'required': False},
            'refreservation':  {'required': False},
            'reservation':     {'required': False},
            'secondarycache':  {'required': False, 'choices':['all', 'none', 'metadata']},
            'setuid':          {'required': False, 'choices':['on', 'off']},
            'shareiscsi':      {'required': False, 'choices':['on', 'off']},
            'sharenfs':        {'required': False},
            'sharesmb':        {'required': False},
            'snapdir':         {'required': False, 'choices':['hidden', 'visible']},
            'sync':            {'required': False, 'choices':['on', 'off']},
            # Not supported
            #'userquota':       {'required': False},
            'utf8only':        {'required': False, 'choices':['on', 'off']},
            'volsize':         {'required': False},
            'volblocksize':    {'required': False},
            'vscan':           {'required': False, 'choices':['on', 'off']},
            'xattr':           {'required': False, 'choices':['on', 'off']},
            'zoned':           {'required': False, 'choices':['on', 'off']},
            },
        supports_check_mode=True
        )

    state = module.params.pop('state')
    name = module.params.pop('name')

    # Get all valid zfs-properties
    properties = dict()
    for prop, value in module.params.iteritems():
        if prop in ['CHECKMODE']:
            continue
        if value:
            properties[prop] = value

    result = {}
    result['name'] = name
    result['state'] = state

    zfs=Zfs(module, name, properties)

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
