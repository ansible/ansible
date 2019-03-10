# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from .get_changes import testcase_get_changes


testcase_reconfigure_failures = {
    "params": [
        (
            {
                "name": "nonexistent-vm-name",
            },
            "Called reconfigure on non existing VM!",
        ),
        (
            {
                "uuid": "nonexistent-vm-uuid",
            },
            "Called reconfigure on non existing VM!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "uuid": "nonexistent-vm-uuid",
            },
            "Called reconfigure on non existing VM!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "is_template": True,
            },
            "VM reconfigure: VM has to be in powered off state to reconfigure but force was not specified!",
        ),
    ],
    "ids": [
        "vm-not-found-name",
        "vm-not-found-uuid",
        "vm-not-found-name+uuid",
        "need_poweredoff-no-force",
    ],
}

# We reuse all of the testcases for get_changes() but we override
# fake_vm_changes parameter with apropriate fake_vm_facts .json file.
# We also add some reconfigure() specific test cases.
testcase_reconfigure = {
    "params": [
        (testcase[0], "%s-reconfigured-misc-1.json" % testcase[0]['name'].replace('-new', '')) for testcase in testcase_get_changes['params']
    ] +
    [
        (
            {
                "name": "ansible-test-vm-1",
                "is_template": True,
                "cdrom": {
                    "iso_name": "guest-tools.iso",
                },
                "networks": [
                    {
                        "name": "Host internal management network",
                        "type": "static",
                        "ip": "192.168.1.11",
                        "netmask": "255.255.255.128",
                        "gateway": "192.168.1.1",
                        "type6": "static",
                        "ip6": "fc00::1:b/64",
                        "gateway6": "fc00::1:1",
                    },
                    {
                        "name": "Host internal management network",
                        "type": "static",
                        "ip": "192.168.0.21/24",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::15/48",
                        "gateway6": "fc00::1",
                    },
                ],
                "force": True,
            },
            "ansible-test-vm-1-reconfigured-misc-2.json",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "disks": [
                    {},
                    {
                        "size": "10gb",
                    },
                ],
            },
            "ansible-test-vm-1-reconfigured-new-disk-only-1.json",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "name": "Pool-wide network associated with eth0",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                    },
                ],
            },
            "ansible-test-vm-1-reconfigured-network-only-1.json",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "name": "Host internal management network",
                        "type": "dhcp",
                        "type6": "dhcp",
                    },
                    {},
                ],
            },
            "ansible-test-vm-1-reconfigured-network-only-2.json",
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "cdrom": {
                    "type": "iso",
                    "iso_name": "XenCenter.iso",
                },
                "networks": [
                    {
                        "name": "Host internal management network",
                        "type": "static",
                        "ip": "192.168.1.12",
                        "netmask": "255.255.255.128",
                        "gateway": "192.168.1.1",
                        "type6": "static",
                        "ip6": "fc00::1:c/64",
                        "gateway6": "fc00::1:1",
                    },
                    {
                        "name": "Host internal management network",
                        "type": "static",
                        "ip": "192.168.0.22/24",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::16/48",
                        "gateway6": "fc00::1",
                    },
                ],
                "force": True,
            },
            "ansible-test-vm-2-reconfigured-misc-2.json",
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Pool-wide network associated with eth0"
                    }
                ],
            },
            "ansible-test-vm-2-reconfigured-network-only.json",
        ),
        (
            {
                "name": "ansible-test-vm-3",
                "networks": [
                    {},
                    {
                        "mac": "66:3f:64:93:0f:43",
                    },
                ],
            },
            "ansible-test-vm-3-reconfigured-misc-2.json",
        ),
        (
            {
                "name": "ansible-test-vm-4",
                "cdrom": {
                    "type": "none",
                    "iso_name": "guest-tools.iso",
                },
            },
            "ansible-test-vm-4-reconfigured-misc-2.json",
        ),
    ],
    "ids": [
        "ansible-test-vm-1-reconfigured-misc-1",
        "ansible-test-vm-2-reconfigured-misc-1",
        "ansible-test-vm-3-reconfigured-misc-1",
        "ansible-test-vm-4-reconfigured-misc-1",
        "ansible-test-vm-1-reconfigured-misc-2",
        "ansible-test-vm-1-reconfigured-new-disk-only-1",
        "ansible-test-vm-1-reconfigured-network-only-1",
        "ansible-test-vm-1-reconfigured-network-only-2",
        "ansible-test-vm-2-reconfigured-misc-2",
        "ansible-test-vm-2-reconfigured-network-only",
        "ansible-test-vm-3-reconfigured-misc-2",
        "ansible-test-vm-4-reconfigured-misc-2",
    ],
}

testcase_reconfigure_elifs = {
    "params": [
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                    },
                ],
            },
            "impossible.json",
        ),
    ],
    "ids": [
        "ansible-test-vm-1",
    ],
}

testcase_reconfigure_check_mode = {
    "params": [(testcase[0], "%s.json" % testcase[0]['name'].replace('-new', '')) for testcase in testcase_reconfigure['params']],
    "ids": testcase_reconfigure['ids'],
}
