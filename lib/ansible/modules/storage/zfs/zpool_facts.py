#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Adam Števko <adam.stevko@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zpool_facts
short_description: Gather facts about ZFS pools.
description:
  - Gather facts from ZFS pool properties.
version_added: "2.3"
author: Adam Števko (@xen0l)
options:
    name:
        description:
            - ZFS pool name.
        aliases: [ "pool", "zpool" ]
        required: false
    parsable:
        description:
            - Specifies if property values should be displayed in machine
              friendly format.
        type: bool
        default: False
        required: false
    properties:
        description:
            - Specifies which dataset properties should be queried in comma-separated format.
              For more information about dataset properties, check zpool(1M) man page.
        aliases: [ "props" ]
        default: all
        required: false
'''

EXAMPLES = '''
# Gather facts about ZFS pool rpool
zpool_facts: pool=rpool

# Gather space usage about all imported ZFS pools
zpool_facts: properties='free,size'
debug: msg='ZFS pool {{ item.name }} has {{ item.free }} free space out of {{ item.size }}.'
with_items: '{{ ansible_zfs_pools }}'
'''

RETURN = '''
name:
    description: ZFS pool name
    returned: always
    type: string
    sample: rpool
parsable:
    description: if parsable output should be provided in machine friendly format.
    returned: if 'parsable' is set to True
    type: boolean
    sample: True
zfs_pools:
    description: ZFS pool facts
    returned: always
    type: string
    sample:
            {
                "allocated": "3.46G",
                "altroot": "-",
                "autoexpand": "off",
                "autoreplace": "off",
                "bootfs": "rpool/ROOT/openindiana",
                "cachefile": "-",
                "capacity": "6%",
                "comment": "-",
                "dedupditto": "0",
                "dedupratio": "1.00x",
                "delegation": "on",
                "expandsize": "-",
                "failmode": "wait",
                "feature@async_destroy": "enabled",
                "feature@bookmarks": "enabled",
                "feature@edonr": "enabled",
                "feature@embedded_data": "active",
                "feature@empty_bpobj": "active",
                "feature@enabled_txg": "active",
                "feature@extensible_dataset": "enabled",
                "feature@filesystem_limits": "enabled",
                "feature@hole_birth": "active",
                "feature@large_blocks": "enabled",
                "feature@lz4_compress": "active",
                "feature@multi_vdev_crash_dump": "enabled",
                "feature@sha512": "enabled",
                "feature@skein": "enabled",
                "feature@spacemap_histogram": "active",
                "fragmentation": "3%",
                "free": "46.3G",
                "freeing": "0",
                "guid": "15729052870819522408",
                "health": "ONLINE",
                "leaked": "0",
                "listsnapshots": "off",
                "name": "rpool",
                "readonly": "off",
                "size": "49.8G",
                "version": "-"
            }
'''

from collections import defaultdict

from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule


class ZPoolFacts(object):
    def __init__(self, module):

        self.module = module

        self.name = module.params['name']
        self.parsable = module.params['parsable']
        self.properties = module.params['properties']

        self._pools = defaultdict(dict)
        self.facts = []

    def pool_exists(self):
        cmd = [self.module.get_bin_path('zpool')]

        cmd.append('list')
        cmd.append(self.name)

        (rc, out, err) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            return False

    def get_facts(self):
        cmd = [self.module.get_bin_path('zpool')]

        cmd.append('get')
        cmd.append('-H')
        if self.parsable:
            cmd.append('-p')
        cmd.append('-o')
        cmd.append('name,property,value')
        cmd.append(self.properties)
        if self.name:
            cmd.append(self.name)

        (rc, out, err) = self.module.run_command(cmd)

        if rc == 0:
            for line in out.splitlines():
                pool, property, value = line.split('\t')

                self._pools[pool].update({property: value})

            for k, v in iteritems(self._pools):
                v.update({'name': k})
                self.facts.append(v)

            return {'ansible_zfs_pools': self.facts}
        else:
            self.module.fail_json(msg='Error while trying to get facts about ZFS pool: %s' % self.name,
                                  stderr=err,
                                  rc=rc)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=False, aliases=['pool', 'zpool'], type='str'),
            parsable=dict(required=False, default=False, type='bool'),
            properties=dict(required=False, default='all', type='str'),
        ),
        supports_check_mode=True
    )

    zpool_facts = ZPoolFacts(module)

    result = {}
    result['changed'] = False
    result['name'] = zpool_facts.name

    if zpool_facts.parsable:
        result['parsable'] = zpool_facts.parsable

    if zpool_facts.name is not None:
        if zpool_facts.pool_exists():
            result['ansible_facts'] = zpool_facts.get_facts()
        else:
            module.fail_json(msg='ZFS pool %s does not exist!' % zpool_facts.name)
    else:
        result['ansible_facts'] = zpool_facts.get_facts()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
