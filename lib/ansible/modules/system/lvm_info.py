#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Daniele Marcocci <daniele.marcocci@par-tec.it>
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
author:
  - Daniele Marcocci (@danielino)
module: lvm_info
short_description: This is a sample module to get info about lvm devices
version_added: "2.4"
description:
  - This module get info about lvm devices
options:
  name:
    description:
      - This is the name of "device"
    required: False
  type:
    choices: [ pv, vg, lv ]
    description:
      - this is the type of "device"
    required: True
notes:
  - Uses lvm commands
'''

EXAMPLES = '''
# get physical volume devices
- name:
  lvm:
    type: pv

# get single device
- name:
  lvm:
    type: pv

# get volume group
- name:
  lvm:
    type: vg

# get logical volume
- name:
  lvm:
    type: lv

'''

RETURN = '''
result:
  description: The output message for disks configuration
  returned: success
  type: list
  sample: >
    [
        {
            "attr": {
                "allocation_policy": {
                    "anywhere": false,
                    "cling": false,
                    "contiguous": false,
                    "inherited": false,
                    "normal": true
                },
                "cluster": false,
                "exported": false,
                "partial": false,
                "r/w": "w",
                "read": true,
                "resizeable": true,
                "write": true
            },
            "lv_count": "3",
            "pv_count": "1",
            "snap_count": "0",
            "vfree": "64,00m",
            "vg": "centos",
            "vsize": "99,51g"
        }
    ]

'''

from ansible.module_utils.basic import AnsibleModule
import os
import subprocess


def sh(cmd):
    out = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
    return out.splitlines()


def cmd_to_fmt(cmd, head):
    ret = sh(cmd)
    items = [filter(None, x.split(' ')) for x in ret]
    return [dict(zip(head[:len(x)], x)) for x in items]


class FileSystem:

    @staticmethod
    def get_fs(device):
        ret = sh("df -Th %s  | tail -1" % device)[0]
        head = ["device", "type", "size", "used", "free", "percent_used", "mountpoint"]
        item = filter(None, ret.split(' '))
        return dict(zip(head, item))


class PhysicalVolume:

    @staticmethod
    def get(name):
        for k in PhysicalVolume.getAll():
            if name == k['pv']:
                return k
        return None

    @staticmethod
    def getAll():
        head = ["pv", "vg", "fmt", "attr", "psize", "pfree"]
        t = cmd_to_fmt("pvs | egrep -i '^.+/' | sed 's/^  //g'", head)
        tmp = []
        for item in t:
            item['lvs'] = LogicalVolume.getByVg(item['vg'])
            tmp.append(item)

        return tmp


class VolumeGroup:

    @staticmethod
    def get(name):
        for k in VolumeGroup.getAll():
            if name == k['vg']:
                return k
        return None

    @staticmethod
    def getAll():
        head = ["vg", "pv_count", "lv_count", "snap_count", "attr", "vsize", "vfree"]
        r = cmd_to_fmt("vgs | egrep -v '^.+VG.+' | sed 's/^  //g'", head)
        count = 0
        for item in r:
            attr = list(r[count]['attr'])
            r[count]['attr'] = {
                "read": False if attr[1] == 'w' else True,
                "write": False if attr[1] == 'r' else True,
                "r/w": attr[0],
                "resizeable": False if attr[1] == '-' else True,
                "exported": False if attr[2] == '-' else True,
                "partial": False if attr[3] == '-' else True,
                "allocation_policy": {
                    "contiguous": True if attr[4] == 'c' else False,
                    "cling": True if attr[4] == 'l' else False,
                    "normal": True if attr[4] == 'n' else False,
                    "anywhere": True if attr[4] == 'a' else False,
                    "inherited": True if attr[4] == 'i' else False,
                },
                "cluster": True if attr[5] == 'c' else False
            }
            count += 1

        return r


class LogicalVolume:

    @staticmethod
    def get(name):
        k = None
        for k in LogicalVolume.getAll():
            if '-' in name:
                name = name.replace('/dev/mapper/', '')
                vg, lv = name.split('-')
                if k['lv'] == lv and k['vg'] == vg:
                    k['device'] = "/dev/mapper/%s" % name
                    k['filesystem'] = FileSystem.get_fs(k['device'])
            else:
                if name == k['lv']:
                    k['device'] = "/dev/mapper/%s-%s" % (k['vg'], k['lv'])
                    k['filesystem'] = FileSystem.get_fs(k['device'])
        return k

    @staticmethod
    def getAll():
        head = ["lv", "vg", "attr", "lsize", "pool", "origin", "data_percent", "meta_percent", "move", "log", "cpy_percent_sync", "convert"]
        return cmd_to_fmt("lvs | egrep -v '^.+LV.+' | sed 's/^  //g'", head)

    @staticmethod
    def getByVg(vg):
        t = VolumeGroup.getAll()
        tmp = []
        for i in t:
            if i['vg'] == vg:
                for k in LogicalVolume.getAll():
                    if k['vg'] == vg:
                        tmp.append(LogicalVolume.get(k['lv']))
        return tmp


class TypeSwitcher(object):

    def __init__(self):
        pass

    def switch(self, value, name=''):
        method_name = 'switch_' + str(value)
        method = getattr(self, method_name, lambda: None)
        return method(name)

    def __base(self, object, name=None):
        if not name:
            return object.getAll()
        return object.get(name)

    def switch_lv(self, name=None):
        return self.__base(LogicalVolume, name)

    def switch_vg(self, name=None):
        return self.__base(VolumeGroup, name)

    def switch_pv(self, name=None):
        return self.__base(PhysicalVolume, name)


def main():
    global module

    module = AnsibleModule(
        argument_spec={
            'name': {'required': False, 'type': 'str'},
            'type': {
                'required': True,
                'type': 'str',
                'choices': ["pv", "lv", "vg"]
            },
            'method': {
                'required': False,
                'default': 'get'
            }
        },
    )

    result = dict(
        changed=False,
        result=TypeSwitcher().switch(module.params['type'], module.params['name'])
    )

    module.exit_json(**result)

if __name__ == "__main__":
    main()
