#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Sophie Herold <sophie@hemio.de>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: virt_vol
author: "Sophie Herold (@sophie-h)"
version_added: "2.4"
short_description: Manage libvirt storage volumes
description:
    - Manage I(libvirt) storage volumes.
'''

EXAMPLES = '''
- virt_vol:
   pool: default
   name: mailserver-var
   capacity: 1 TB
   options:
    allocation: 0
'''

import re

fail = None

try:
    import libvirt
except ImportError:
    fail = 'The `libvirt` module is not importable. Check the requirements.'

try:
    from lxml import etree
except ImportError:
    fail = 'The `lxml` module is not importable. Check the requirements.'

from ansible.module_utils.basic import AnsibleModule


class VirtStoragePool(object):

    def __init__(self, uri, module, pool_name):
        self.module = module

        self.conn = libvirt.open(uri)
        if not self.conn:
            raise Exception("hypervisor connection failure")

        self.pool = self.conn.storagePoolLookupByName(pool_name)

    def getVolume(self, vol_name):
        try:
            return self.pool.storageVolLookupByName(vol_name)
        except libvirt.libvirtError:
            return None

    def define(self, xml):
        if not self.module.check_mode:
            return self.pool.createXML(xml)


def parse_number(value):
    units = {
        'B': 1,
        'BYTES': 1,
        'KB': 10**3,
        'K': 2**10,
        'KIB': 2**10,
        'MB': 10**6,
        'M': 2**20,
        'MIB': 2**20,
        'GB': 10**9,
        'G': 2**30,
        'GIB': 2**30,
        'TB': 10**12,
        'T': 2**40,
        'TIB': 2**40,
        'PB': 10**15,
        'P': 2**50,
        'PIB': 2**50,
        'EB': 10**18,
        'E': 2**60,
        'EIB': 2**60
    }

    re_unit = re.compile(r"^\s*(\d+)\s*([a-zA-Z]*)\s*$")

    match = re_unit.match(str(value))

    if match is None:
        raise Exception("invalid size format '{}'".format(value))

    size, unit = match.group(1, 2)

    if unit:
        try:
            return int(size) * units[unit.upper()]
        except KeyError:
            raise Exception("invalid unit '{}'".format(unit))
    else:
        return int(size)


class DictToXml:
    unit_fields = ["capacity", "allocation"]

    def __init__(self, root_name, data):
        self.root = etree.Element(root_name)
        self.append_data(self.root, data)

    def append_data(self, node, data):
        for field, value in data.items():
            child = etree.SubElement(node, field)
            if isinstance(value, dict):
                self.append_data(child, value)
            elif field in self.unit_fields:
                child.text = str(parse_number(value))
            else:
                child.text = str(value)

    def to_string(self):
        return etree.tostring(self.root, pretty_print=True)


def core(module):

    pool = module.params['pool']
    name = module.params['name']
    capacity = parse_number(module.params['capacity'])
    resize = module.params['resize']
    options = module.params['options']
    uri = module.params['uri']

    v = VirtStoragePool(uri, module, pool)

    options['name'] = name
    options['capacity'] = capacity

    volume = v.getVolume(name)
    result = dict()

    if volume is None:
        v.define(DictToXml('volume', options).to_string())
        result['changed'] = True
        volume = v.getVolume(name)
    else:
        # info(): [Type, Capacity, Allocation]
        cur_capacity = volume.info()[1]

        if cur_capacity < capacity and resize == 'enlarge':
            if not module.check_mode:
                volume.resize(capacity)
            result['changed'] = True
        elif cur_capacity != capacity:
            result['warnings'] = ['Capacity remained unchanged']

    if volume is None:
        result['vol_path'] = None
    else:
        result['vol_path'] = volume.path()

    module.exit_json(**result)


def main():

    if fail:
        module.fail_json(msg=fail)

    module = AnsibleModule(
        argument_spec=dict(
            pool=dict(required=True),
            name=dict(required=True, aliases=['volume']),
            capacity=dict(required=True),
            resize=dict(default='no', choices=['no', 'enlarge']),
            options=dict(default={}, type='dict'),
            uri=dict(default='qemu:///system'),
        ),
        supports_check_mode=True
    )

    try:
        result = core(module)
    except Exception as e:
        module.fail_json(msg=repr(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
