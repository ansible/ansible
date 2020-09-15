#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Adam Števko <adam.stevko@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zfs_facts
short_description: Gather facts about ZFS datasets.
description:
  - Gather facts from ZFS dataset properties.
version_added: "2.3"
author: Adam Števko (@xen0l)
options:
    name:
        description:
            - ZFS dataset name.
        required: yes
        aliases: [ "ds", "dataset" ]
    recurse:
        description:
            - Specifies if properties for any children should be recursively
              displayed.
        type: bool
        default: 'no'
    parsable:
        description:
            - Specifies if property values should be displayed in machine
              friendly format.
        type: bool
        default: 'no'
    properties:
        description:
            - Specifies which dataset properties should be queried in comma-separated format.
              For more information about dataset properties, check zfs(1M) man page.
        default: all
        aliases: [ "props" ]
    type:
        description:
            - Specifies which datasets types to display. Multiple values have to be
              provided in comma-separated form.
        choices: [ 'all', 'filesystem', 'volume', 'snapshot', 'bookmark' ]
        default: all
    depth:
        description:
            - Specifies recursion depth.
'''

EXAMPLES = '''
- name: Gather facts about ZFS dataset rpool/export/home
  zfs_facts:
    dataset: rpool/export/home

- name: Report space usage on ZFS filesystems under data/home
  zfs_facts:
    name: data/home
    recurse: yes
    type: filesystem

- debug:
    msg: 'ZFS dataset {{ item.name }} consumes {{ item.used }} of disk space.'
  with_items: '{{ ansible_zfs_datasets }}'
'''

RETURN = '''
name:
    description: ZFS dataset name
    returned: always
    type: str
    sample: rpool/var/spool
parsable:
    description: if parsable output should be provided in machine friendly format.
    returned: if 'parsable' is set to True
    type: bool
    sample: True
recurse:
    description: if we should recurse over ZFS dataset
    returned: if 'recurse' is set to True
    type: bool
    sample: True
zfs_datasets:
    description: ZFS dataset facts
    returned: always
    type: str
    sample:
            {
                "aclinherit": "restricted",
                "aclmode": "discard",
                "atime": "on",
                "available": "43.8G",
                "canmount": "on",
                "casesensitivity": "sensitive",
                "checksum": "on",
                "compression": "off",
                "compressratio": "1.00x",
                "copies": "1",
                "creation": "Thu Jun 16 11:37 2016",
                "dedup": "off",
                "devices": "on",
                "exec": "on",
                "filesystem_count": "none",
                "filesystem_limit": "none",
                "logbias": "latency",
                "logicalreferenced": "18.5K",
                "logicalused": "3.45G",
                "mlslabel": "none",
                "mounted": "yes",
                "mountpoint": "/rpool",
                "name": "rpool",
                "nbmand": "off",
                "normalization": "none",
                "org.openindiana.caiman:install": "ready",
                "primarycache": "all",
                "quota": "none",
                "readonly": "off",
                "recordsize": "128K",
                "redundant_metadata": "all",
                "refcompressratio": "1.00x",
                "referenced": "29.5K",
                "refquota": "none",
                "refreservation": "none",
                "reservation": "none",
                "secondarycache": "all",
                "setuid": "on",
                "sharenfs": "off",
                "sharesmb": "off",
                "snapdir": "hidden",
                "snapshot_count": "none",
                "snapshot_limit": "none",
                "sync": "standard",
                "type": "filesystem",
                "used": "4.41G",
                "usedbychildren": "4.41G",
                "usedbydataset": "29.5K",
                "usedbyrefreservation": "0",
                "usedbysnapshots": "0",
                "utf8only": "off",
                "version": "5",
                "vscan": "off",
                "written": "29.5K",
                "xattr": "on",
                "zoned": "off"
            }
'''

from collections import defaultdict

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


SUPPORTED_TYPES = ['all', 'filesystem', 'volume', 'snapshot', 'bookmark']


class ZFSFacts(object):
    def __init__(self, module):

        self.module = module

        self.name = module.params['name']
        self.recurse = module.params['recurse']
        self.parsable = module.params['parsable']
        self.properties = module.params['properties']
        self.type = module.params['type']
        self.depth = module.params['depth']

        self._datasets = defaultdict(dict)
        self.facts = []

    def dataset_exists(self):
        cmd = [self.module.get_bin_path('zfs')]

        cmd.append('list')
        cmd.append(self.name)

        (rc, out, err) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            return False

    def get_facts(self):
        cmd = [self.module.get_bin_path('zfs')]

        cmd.append('get')
        cmd.append('-H')
        if self.parsable:
            cmd.append('-p')
        if self.recurse:
            cmd.append('-r')
        if int(self.depth) != 0:
            cmd.append('-d')
            cmd.append('%s' % self.depth)
        if self.type:
            cmd.append('-t')
            cmd.append(self.type)
        cmd.append('-o')
        cmd.append('name,property,value')
        cmd.append(self.properties)
        cmd.append(self.name)

        (rc, out, err) = self.module.run_command(cmd)

        if rc == 0:
            for line in out.splitlines():
                dataset, property, value = line.split('\t')

                self._datasets[dataset].update({property: value})

            for k, v in iteritems(self._datasets):
                v.update({'name': k})
                self.facts.append(v)

            return {'ansible_zfs_datasets': self.facts}
        else:
            self.module.fail_json(msg='Error while trying to get facts about ZFS dataset: %s' % self.name,
                                  stderr=err,
                                  rc=rc)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, aliases=['ds', 'dataset'], type='str'),
            recurse=dict(required=False, default=False, type='bool'),
            parsable=dict(required=False, default=False, type='bool'),
            properties=dict(required=False, default='all', type='str'),
            type=dict(required=False, default='all', type='str', choices=SUPPORTED_TYPES),
            depth=dict(required=False, default=0, type='int')
        ),
        supports_check_mode=True
    )

    zfs_facts = ZFSFacts(module)

    result = {}
    result['changed'] = False
    result['name'] = zfs_facts.name

    if zfs_facts.parsable:
        result['parsable'] = zfs_facts.parsable

    if zfs_facts.recurse:
        result['recurse'] = zfs_facts.recurse

    if zfs_facts.dataset_exists():
        result['ansible_facts'] = zfs_facts.get_facts()
    else:
        module.fail_json(msg='ZFS dataset %s does not exist!' % zfs_facts.name)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
