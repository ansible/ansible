# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


testcase_get_changes_failures = {
    "params": [
        (
            {
                "name": "nonexistent-vm-name",
            },
            "Called get_changes on non existing VM!",
        ),
        (
            {
                "uuid": "nonexistent-vm-uuid",
            },
            "Called get_changes on non existing VM!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "uuid": "nonexistent-vm-uuid",
            },
            "Called get_changes on non existing VM!",
        ),
        (
            {
                "name": "CentOS 7",
            },
            "VM check: targeted VM is a template! Template reconfiguration is not supported.",
        ),
        (
            {
                "name": "ansible-test-vm-4-snap",
            },
            "VM check: targeted VM is a snapshot! Snapshot reconfiguration is not supported.",
        ),
        (
            {
                "name": "",
                "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
            },
            "VM check name: VM name cannot be an empty string!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "home_server": "nonexistent-host",
            },
            "VM check home_server: home server with name 'nonexistent-host' not found!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "num_cpus": "abcd",
                },
            },
            "VM check hardware.num_cpus: parameter should be an integer value!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "num_cpus": "-2",
                },
            },
            "VM check hardware.num_cpus: parameter should be greater than zero!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "num_cpu_cores_per_socket": "abcd",
                },
            },
            "VM check hardware.num_cpu_cores_per_socket: parameter should be an integer value!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "num_cpu_cores_per_socket": "-2",
                },
            },
            "VM check hardware.num_cpu_cores_per_socket: parameter should be greater than zero!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "num_cpus": 2,
                    "num_cpu_cores_per_socket": 4,
                },
            },
            "VM check hardware.num_cpus: parameter should be a multiple of hardware.num_cpu_cores_per_socket!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "memory_mb": "abcd",
                },
            },
            "VM check hardware.memory_mb: parameter should be an integer value!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "memory_mb": "-2",
                },
            },
            "VM check hardware.memory_mb: parameter should be greater than zero!",
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "disks": [{}],
            },
            "VM check disks: provided disks configuration has less disks than the target VM (1 < 2)!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "disks": [
                    {
                        "name": "",
                    },
                ],
            },
            "VM check disks[0]: disk name cannot be an empty string!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "disks": [
                    {
                        "size": "1",
                    },
                ],
            },
            "VM check disks[0]: disk size is smaller than existing (1 bytes < 42949672960 bytes). Reducing disk size is not allowed!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "disks": [
                    {},
                    {},
                ],
            },
            "VM check disks[1]: no valid disk size specification found!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "disks": [
                    {},
                    {
                        "size": "10gb",
                        "sr": "nonexistent-sr",
                    },
                ],
            },
            "VM check disks[1]: SR with name 'nonexistent-sr' not found!",
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
            "VM check disks[1]: no default SR found! You must specify SR explicitly.",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "cdrom": {
                    "iso_name": "nonexistent-iso",
                },
            },
            "VM check cdrom.iso_name: ISO image with name 'nonexistent-iso' not found!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [{}],
            },
            "VM check networks: provided networks configuration has less interfaces than the target VM (1 < 2)!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "name": "",
                    },
                    {},
                ],
            },
            "VM check networks[0]: network name cannot be an empty string!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "name": "nonexistent-network",
                    },
                    {},
                ],
            },
            "VM check networks[0]: network with name 'nonexistent-network' not found!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "mac": "bad-mac",
                    },
                    {},
                ],
            },
            "VM check networks[0]: specified MAC address 'bad-mac' is not valid!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "ip": "bad-ip",
                    },
                    {},
                ],
            },
            "VM check networks[0]: specified IPv4 address 'bad-ip' is not valid!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "ip": "127.0.0.1/bad-prefix",
                    },
                    {},
                ],
            },
            "VM check networks[0]: specified IPv4 prefix 'bad-prefix' is not valid!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "type": "static",
                        "netmask": "bad-netmask",
                    },
                    {},
                ],
            },
            "VM check networks[0]: specified IPv4 netmask 'bad-netmask' is not valid!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "gateway": "bad-gateway",
                    },
                    {},
                ],
            },
            "VM check networks[0]: specified IPv4 gateway 'bad-gateway' is not valid!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "ip6": "bad-ip6",
                    },
                    {},
                ],
            },
            "VM check networks[0]: specified IPv6 address 'bad-ip6' is not valid!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "ip6": "::1/bad-prefix6",
                    },
                    {},
                ],
            },
            "VM check networks[0]: specified IPv6 prefix 'bad-prefix6' is not valid!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {
                        "gateway6": "bad-gateway6",
                    },
                    {},
                ],
            },
            "VM check networks[0]: specified IPv6 gateway 'bad-gateway6' is not valid!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {},
                    {},
                    {},
                ],
            },
            "VM check networks[2]: network name is required for new network interface!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                        "ip": "127.0.0.1",
                    },
                ],
            },
            "VM check networks[2]: IPv4 netmask or prefix is required for new network interface!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                        "ip6": "::1",
                    },
                ],
            },
            "VM check networks[2]: IPv6 prefix is required for new network interface!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "custom_params": [
                    {
                        "key": "nonexistent-vm-param",
                    },
                ],
            },
            "VM check custom_params[0]: unknown VM param 'nonexistent-vm-param'!",
        ),
    ],
    "ids": [
        "vm-not-found-name",
        "vm-not-found-uuid",
        "vm-not-found-name+uuid",
        "vm-is-template",
        "vm-is-snapshot",
        "vm-name-is-empty-string",
        "home_server-not-found",
        "num_cpus-not-an-int",
        "num_cpus-is-negative",
        "num_cpu_cores_per_socket-not-an-int",
        "num_cpu_cores_per_socket-is-negative",
        "num_cpus-not-multiple-of-num_cpu_cores_per_socket",
        "memory_mb-not-an-int",
        "memory_mb-is-negative",
        "disks-less-than",
        "disks-name-is-empty-string",
        "disks-size-is-smaller-than",
        "disks-size-not-specified",
        "disks-sr-not-found",
        "disks-no-default-sr",
        "cdrom-iso-not-found",
        "networks-less-than",
        "networks-name-is-empty-string",
        "networks-not-found",
        "networks-bad-mac",
        "networks-bad-ip",
        "networks-bad-prefix",
        "networks-bad-netmask",
        "networks-bad-gateway",
        "networks-bad-ip6",
        "networks-bad-prefix6",
        "networks-bad-gateway6",
        "networks-name-not-specified",
        "networks-netmask-not-specified",
        "networks-prefix6-not-specified",
        "custom_param-not-found",
    ],
}

testcase_get_changes_device_limits = {
    "params": [
        (
            {
                "name": "ansible-test-vm-1",
                "disks": [
                    {},
                    {
                        "size": "10gb"
                    },
                    {
                        "size": "10gb"
                    },
                    {
                        "size": "10gb"
                    },
                ],
            },
            4,
            7,
            "VM check disks[3]: maximum number of devices reached!",
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "disks": [
                    {},
                    {},
                    {
                        "size": "10gb"
                    },
                ],
            },
            4,
            7,
            "VM check disks[2]: new disk position 4 is out of bounds!",
        ),
        (
            {
                "name": "ansible-test-vm-4",
                "disks": [
                    {
                        "size": "10gb"
                    },
                    {
                        "size": "10gb"
                    },
                ],
                "cdrom": {
                    "type": "none",
                },
            },
            2,
            7,
            "VM check cdrom: maximum number of devices reached!",
        ),
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
            7,
            2,
            "VM check networks[2]: maximum number of network interfaces reached!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                    },
                    {
                        "name": "Host internal management network",
                    },
                    {
                        "name": "Host internal management network",
                    },
                ],
            },
            7,
            4,
            "VM check networks[4]: maximum number of network interfaces reached!",
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                    },
                ],
            },
            7,
            3,
            "VM check networks[2]: new network interface position 3 is out of bounds!",
        ),
    ],
    "ids": [
        "max-disks-reached",
        "disk-out-of-bounds",
        "cdrom-out-of-bounds",
        "max-network-interfaces-reached-single",
        "max-network-interfaces-reached-multiple",
        "network-interface-out-of-bounds",
    ],
}

testcase_get_changes_no_change = {
    "params": [
        {
            "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
        },
        {
            "uuid": "0a05d5ad-3e4b-f0dc-6101-8c56623958bc",
        },
        {
            "uuid": "8f5bc97c-42fa-d619-aba4-d25eced735e0",
        },
        {
            "uuid": "92181f0c-4a6b-ca53-25dc-6fda6a9f6835",
        },
        {
            "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
            "hardware": {},
            "disks": [{}],
            "cdrom": {},
            "networks": [
                {},
                {},
            ],
            "custom_params": [],
        },
        {
            "uuid": "0a05d5ad-3e4b-f0dc-6101-8c56623958bc",
            "hardware": {},
            "disks": [
                {},
                {},
            ],
            "cdrom": {},
            "networks": [
                {},
                {}
            ],
            "custom_params": [],
        },
        {
            "uuid": "8f5bc97c-42fa-d619-aba4-d25eced735e0",
            "hardware": {},
            "disks": [{}],
            "cdrom": {},
            "networks": [
                {},
                {},
            ],
            "custom_params": [],
        },
        {
            "uuid": "92181f0c-4a6b-ca53-25dc-6fda6a9f6835",
            "hardware": {},
            "disks": [],
            "cdrom": {},
            "networks": [],
            "custom_params": [],
        },
        {
            "name": "ansible-test-vm-1",
            "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
            "name_desc": "Created by Ansible",
            "folder": "/Ansible/Test",
            "home_server": "",
            "hardware": {
                "num_cpus": 2,
                "num_cpu_cores_per_socket": 2,
                "memory_mb": 2048,
            },
            "disks": [
                {
                    "name": "ansible-test-vm-1-C",
                    "name_desc": "C:\\",
                    "size": "40gb",
                    "sr": "Ansible Test Storage 1",
                    "sr_uuid": "767b30e4-f8db-a83d-8ba7-f5e6e732e06f",
                },
            ],
            "cdrom": {
                "type": "none",
                "iso_name": "",
            },
            "networks": [
                {
                    "name": "Host internal management network",
                    "mac": "7a:a6:48:1e:31:46",
                    "type": "static",
                    "ip": "192.168.0.11/24",
                    "netmask": "255.255.255.0",
                    "gateway": "192.168.0.1",
                    "type6": "static",
                    "ip6": "fc00::b/48",
                    "gateway6": "fc00::1",
                },
                {
                    "name": "Host internal management network",
                    "mac": "0a:ae:29:2f:1c:65",
                    "type": "none",
                    "ip": "",
                    "netmask": "",
                    "gateway": "",
                    "type6": "none",
                    "ip6": "",
                    "gateway6": "",
                },
            ],
            "custom_params": [
                {
                    "key": "HVM_boot_params",
                    "value": {
                        "order": "dc",
                    },
                },
            ],
        },
        {
            "name": "ansible-test-vm-2",
            "uuid": "0a05d5ad-3e4b-f0dc-6101-8c56623958bc",
            "name_desc": "Created by Ansible",
            "folder": "/Ansible/Test",
            "home_server": "ansible-test-host-2",
            "hardware": {
                "num_cpus": 1,
                "num_cpu_cores_per_socket": 1,
                "memory_mb": 1024,
            },
            "disks": [
                {
                    "name": "ansible-test-vm-2-root",
                    "name_desc": "/",
                    "size": "10gb",
                    "sr": "Ansible Test Storage 1",
                    "sr_uuid": "767b30e4-f8db-a83d-8ba7-f5e6e732e06f",
                },
                {
                    "name": "ansible-test-vm-2-mysql",
                    "name_desc": "/var/lib/mysql",
                    "size": "1gb",
                    "sr": "Ansible Test Storage 1",
                    "sr_uuid": "767b30e4-f8db-a83d-8ba7-f5e6e732e06f",
                },
            ],
            "cdrom": {
                "type": "iso",
                "iso_name": "guest-tools.iso",
            },
            "networks": [
                {
                    "name": "Host internal management network",
                    "mac": "16:87:31:70:d6:31",
                    "type": "static",
                    "ip": "192.168.0.12/24",
                    "netmask": "255.255.255.0",
                    "gateway": "192.168.0.1",
                    "type6": "static",
                    "ip6": "fc00::c/48",
                    "gateway6": "fc00::1",
                },
                {
                    "name": "Host internal management network",
                    "mac": "8a:f2:3e:a2:e4:e6",
                    "type": "dhcp",
                    "ip": "",
                    "netmask": "",
                    "gateway": "",
                    "type6": "dhcp",
                    "ip6": "",
                    "gateway6": "",
                }
            ],
            "custom_params": [],
        },
        {
            "name": "ansible-test-vm-3",
            "uuid": "8f5bc97c-42fa-d619-aba4-d25eced735e0",
            "name_desc": "Created by Ansible",
            "folder": "",
            "home_server": "",
            "hardware": {
                "num_cpus": 1,
                "num_cpu_cores_per_socket": 1,
                "memory_mb": 1024,
            },
            "disks": [
                {
                    "name": "ansible-test-vm-3-root",
                    "name_desc": "/",
                    "size": "8gb",
                    "sr": "Ansible Test Storage 1",
                    "sr_uuid": "767b30e4-f8db-a83d-8ba7-f5e6e732e06f",
                },
            ],
            "cdrom": {
                "iso_name": "guest-tools.iso",
            },
            "networks": [
                {
                    "name": "Host internal management network",
                    "mac": "72:fb:c7:ac:b9:97",
                    "type": "none",
                    "ip": "",
                    "netmask": "",
                    "gateway": "",
                    "type6": "none",
                    "ip6": "",
                    "gateway6": "",
                },
                {
                    "name": "Host internal management network",
                    "mac": "66:3f:64:93:0f:42",
                    "type": "none",
                    "ip": "",
                    "netmask": "",
                    "gateway": "",
                    "type6": "none",
                    "ip6": "",
                    "gateway6": "",
                },
            ],
            "custom_params": [],
        },
        {
            "name": "ansible-test-vm-4",
            "uuid": "92181f0c-4a6b-ca53-25dc-6fda6a9f6835",
            "name_desc": "",
            "folder": "",
            "home_server": "",
            "hardware": {
                "num_cpus": 8,
                "num_cpu_cores_per_socket": 4,
                "memory_mb": 8192,
            },
            "disks": [],
            "cdrom": {},
            "networks": [],
            "custom_params": [],
        },
    ],
    "ids": [
        "ansible-test-vm-1-no-params-specified",
        "ansible-test-vm-2-no-params-specified",
        "ansible-test-vm-3-no-params-specified",
        "ansible-test-vm-4-no-params-specified",
        "ansible-test-vm-1-params-none",
        "ansible-test-vm-2-params-none",
        "ansible-test-vm-3-params-none",
        "ansible-test-vm-4-params-none",
        "ansible-test-vm-1-no-params-changed",
        "ansible-test-vm-2-no-params-changed",
        "ansible-test-vm-3-no-params-changed",
        "ansible-test-vm-4-no-params-changed",
    ],
}

testcase_get_changes_need_poweredoff = {
    "params": [
        (
            {
                "name": "ansible-test-vm-1",
                "is_template": True,
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "num_cpus": 4,
                },
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "num_cpu_cores_per_socket": 4,
                },
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "hardware": {
                    "memory_mb": 4096,
                },
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "disks": [
                    {
                        "size": "50gb",
                    },
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {
                        "type": "none",
                    },
                    {},
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {
                        "ip": "192.168.2.12",
                    },
                    {},
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {
                        "ip": "192.168.0.12/25",
                    },
                    {},
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {
                        "type": "static",
                        "netmask": "255.255.255.128",
                    },
                    {},
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {
                        "type": "static",
                        "gateway": "192.168.2.1",
                    },
                    {},
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {
                        "type6": "none",
                    },
                    {},
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {
                        "ip6": "fc00::2:c/48",
                    },
                    {},
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {
                        "ip6": "fc00::c/64",
                    },
                    {},
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {
                        "type6": "static",
                        "gateway6": "fc00::2:1",
                    },
                    {},
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                        "type": "dhcp",
                    },
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                        "ip": "192.168.0.32/24",
                    },
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                        "type": "static",
                        "netmask": "255.255.255.0",
                    },
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                        "type": "static",
                        "gateway": "192.168.0.1",
                    },
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                        "type6": "dhcp",
                    },
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                        "ip6": "fc00::20/48",
                    },
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "networks": [
                    {},
                    {},
                    {
                        "name": "Host internal management network",
                        "type6": "static",
                        "gateway6": "fc00::1",
                    },
                ],
            },
            True,
        ),
        (
            {
                "name": "ansible-test-vm-1-new",
                "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
                "name_desc": "Created by Ansible New",
                "folder": "/Ansible/Test/New",
                "home_server": "ansible-test-host-1",
                "disks": [
                    {
                        "name": "ansible-test-vm-1-C-new",
                        "name_desc": "C:\\ New",
                    },
                    {
                        "name": "ansible-test-vm-1-D",
                        "name_desc": "D:\\",
                        "size": "10gb",
                        "sr": "Ansible Test Storage 1",
                        "sr_uuid": "767b30e4-f8db-a83d-8ba7-f5e6e732e06f",
                    },
                ],
                "cdrom": {
                    "type": "iso",
                    "iso_name": "guest-tools.iso",
                },
                "networks": [
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "7a:a6:48:1e:31:47",
                        "type": "static",
                        "ip": "192.168.1.11",
                        "netmask": "255.255.255.128",
                        "gateway": "192.168.1.1",
                        "type6": "static",
                        "ip6": "fc00::1:b/64",
                        "gateway6": "fc00::1:1",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "0a:ae:29:2f:1c:66",
                        "type": "static",
                        "ip": "192.168.0.21/24",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::15/48",
                        "gateway6": "fc00::1",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "type": "static",
                        "ip": "192.168.0.31",
                        "netmask": "255.255.255.0",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::1f/48",
                        "gateway6": "fc00::1",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "type": "dhcp",
                        "type6": "dhcp",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "type": "none",
                        "type6": "none",
                    },
                ],
                "custom_params": [
                    {
                        "key": "HVM_boot_params",
                        "value": {
                            "order": "ncd",
                        },
                    },
                ],
            },
            False,
        ),
        (
            {
                "name": "ansible-test-vm-2-new",
                "uuid": "0a05d5ad-3e4b-f0dc-6101-8c56623958bc",
                "name_desc": "",
                "folder": "",
                "home_server": "",
                "disks": [
                    {
                        "name": "ansible-test-vm-2-root-new",
                        "name_desc": "",
                    },
                    {
                        "name": "ansible-test-vm-2-mysql-new",
                        "name_desc": "",
                    },
                    {
                        "name": "ansible-test-vm-2-mongo",
                        "name_desc": "",
                        "size": "10gb",
                        "sr": "Ansible Test Storage 1",
                        "sr_uuid": "767b30e4-f8db-a83d-8ba7-f5e6e732e06f",
                    },
                ],
                "cdrom": {
                    "type": "none",
                },
                "networks": [
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "16:87:31:70:d6:32",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "8a:f2:3e:a2:e4:e7",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                    },
                ],
                "custom_params": [
                    {
                        "key": "HVM_boot_params",
                        "value": {
                            "order": "ncd",
                        },
                    },
                ],
            },
            False,
        ),
    ],
    "ids": [
        "ansible-test-vm-1-is_template",
        "ansible-test-vm-1-num_cpus",
        "ansible-test-vm-1-num_cpu_cores_per_socket",
        "ansible-test-vm-1-memory_mb",
        "ansible-test-vm-1-disk-size",
        "ansible-test-vm-2-existing-network-type",
        "ansible-test-vm-2-existing-network-ip",
        "ansible-test-vm-2-existing-network-prefix",
        "ansible-test-vm-2-existing-network-netmask",
        "ansible-test-vm-2-existing-network-gateway",
        "ansible-test-vm-2-existing-network-type6",
        "ansible-test-vm-2-existing-network-ip6",
        "ansible-test-vm-2-existing-network-prefix6",
        "ansible-test-vm-2-existing-network-gateway6",
        "ansible-test-vm-2-new-network-type",
        "ansible-test-vm-2-new-network-ip",
        "ansible-test-vm-2-new-network-netmask",
        "ansible-test-vm-2-new-network-gateway",
        "ansible-test-vm-2-new-network-type6",
        "ansible-test-vm-2-new-network-ip6",
        "ansible-test-vm-2-new-network-gateway6",
        "ansible-test-vm-1-no-need_poweredoff",
        "ansible-test-vm-2-no-need_poweredoff",
    ],
}

testcase_get_changes = {
    "params": [
        (
            {
                "name": "ansible-test-vm-1-new",
                "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
                "name_desc": "Created by Ansible New",
                "folder": "/Ansible/Test/New",
                "home_server": "ansible-test-host-1",
                "hardware": {
                    "num_cpus": 4,
                    "num_cpu_cores_per_socket": 4,
                    "memory_mb": 4096,
                },
                "disks": [
                    {
                        "name": "ansible-test-vm-1-C-new",
                        "name_desc": "C:\\ New",
                        "size": "50gb",
                    },
                    {
                        "name": "ansible-test-vm-1-D",
                        "name_desc": "D:\\",
                        "size": "10gb",
                        "sr_uuid": "767b30e4-f8db-a83d-8ba7-f5e6e732e06f",
                    },
                ],
                "cdrom": {
                    "type": "iso",
                    "iso_name": "guest-tools.iso",
                },
                "networks": [
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "7a:a6:48:1e:31:47",
                        "type": "static",
                        "ip": "192.168.1.11",
                        "netmask": "255.255.255.128",
                        "gateway": "192.168.1.1",
                        "type6": "static",
                        "ip6": "fc00::1:b/64",
                        "gateway6": "fc00::1:1",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "0a:ae:29:2f:1c:66",
                        "type": "static",
                        "ip": "192.168.0.21/24",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::15/48",
                        "gateway6": "fc00::1",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "type": "static",
                        "ip": "192.168.0.31",
                        "netmask": "255.255.255.0",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::1f/48",
                        "gateway6": "fc00::1",
                    },
                    {
                        "name": "Host internal management network",
                        "type": "dhcp",
                        "type6": "dhcp",
                    },
                    {
                        "name": "Host internal management network",
                        "type": "none",
                        "type6": "none",
                    },
                ],
                "custom_params": [
                    {
                        "key": "HVM_boot_params",
                        "value": {
                            "order": "ncd",
                        },
                    },
                ],
                "force": True,
            },
            "ansible-test-vm-1-all-params-changed.json",
        ),
        (
            {
                "name": "ansible-test-vm-2-new",
                "uuid": "0a05d5ad-3e4b-f0dc-6101-8c56623958bc",
                "name_desc": "",
                "folder": "",
                "home_server": "",
                "hardware": {
                    "num_cpus": 2,
                    "num_cpu_cores_per_socket": 2,
                    "memory_mb": 2048,
                },
                "disks": [
                    {
                        "name": "ansible-test-vm-2-root-new",
                        "name_desc": "",
                        "size": "20gb",
                    },
                    {
                        "name": "ansible-test-vm-2-mysql-new",
                        "name_desc": "",
                        "size": "2gb",
                    },
                    {
                        "name": "ansible-test-vm-2-mongo",
                        "name_desc": "",
                        "size": "10gb",
                        "sr": "Ansible Test Storage 1",
                    },
                ],
                "cdrom": {
                    "type": "none",
                },
                "networks": [
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "16:87:31:70:d6:32",
                        "type": "static",
                        "ip": "192.168.1.12",
                        "netmask": "255.255.255.128",
                        "gateway": "192.168.1.1",
                        "type6": "static",
                        "ip6": "fc00::1:c/64",
                        "gateway6": "fc00::1:1",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "8a:f2:3e:a2:e4:e7",
                        "type": "static",
                        "ip": "192.168.0.22/24",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::16/48",
                        "gateway6": "fc00::1",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "type": "static",
                        "ip": "192.168.0.32/24",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::20/48",
                        "gateway6": "fc00::1",
                    },
                    {
                        "name": "Host internal management network",
                        "type": "dhcp",
                        "type6": "dhcp",
                    },
                    {
                        "name": "Host internal management network",
                        "type": "none",
                        "type6": "none",
                    },
                ],
                "custom_params": [],
                "force": True,
            },
            "ansible-test-vm-2-all-params-changed.json",
        ),
        (
            {
                "name": "ansible-test-vm-3-new",
                "uuid": "8f5bc97c-42fa-d619-aba4-d25eced735e0",
                "name_desc": "Created by Ansible New",
                "folder": "/Ansible/Test/New",
                "home_server": "ansible-test-host-1",
                "hardware": {
                    "num_cpus": 4,
                    "num_cpu_cores_per_socket": 4,
                    "memory_mb": 4096,
                },
                "disks": [
                    {
                        "name": "ansible-test-vm-3-root-new",
                        "name_desc": "/ New",
                        "size": "16gb",
                    },
                    {
                        "name": "ansible-test-vm-3-mysql",
                        "name_desc": "/var/lib/mysql",
                        "size": "10gb",
                        "sr": "Ansible Test Storage 1",
                    },
                ],
                "cdrom": {
                    "iso_name": "",
                },
                "networks": [
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "72:fb:c7:ac:b9:98",
                        "type": "static",
                        "ip": "192.168.0.13",
                        "netmask": "255.255.255.0",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::d/48",
                        "gateway6": "fc00::1",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "mac": "66:3f:64:93:0f:43",
                        "type": "dhcp",
                        "type6": "dhcp",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "type": "static",
                        "ip": "192.168.0.33",
                        "netmask": "255.255.255.0",
                        "gateway": "192.168.0.1",
                        "type6": "static",
                        "ip6": "fc00::21/48",
                        "gateway6": "fc00::1",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "type": "dhcp",
                        "type6": "dhcp",
                    },
                    {
                        "name": "Pool-wide network associated with eth0",
                        "type": "none",
                        "type6": "none",
                    },
                ],
            },
            "ansible-test-vm-3-all-params-changed.json",
        ),
        (
            {
                "name": "ansible-test-vm-4-new",
                "uuid": "92181f0c-4a6b-ca53-25dc-6fda6a9f6835",
                "name_desc": "Created by Ansible New",
                "folder": "/Ansible/Test/New",
                "home_server": "ansible-test-host-2",
                "hardware": {
                    "num_cpus": 4,
                    "num_cpu_cores_per_socket": 1,
                    "memory_mb": 4096,
                },
                "disks": [
                    {
                        "name": "ansible-test-vm-4-root",
                        "name_desc": "/",
                        "size": "10gb",
                    },
                    {
                        "name": "ansible-test-vm-4-mysql",
                        "name_desc": "/var/lib/mysql",
                        "size": "10gb",
                    },
                    {
                        "name": "ansible-test-vm-4-redis",
                        "name_desc": "/var/lib/redis",
                        "size": "10gb",
                    },
                    {
                        "name": "ansible-test-vm-4-mongo",
                        "name_desc": "/var/lib/mongo",
                        "size": "10gb",
                    },
                ],
                "cdrom": {
                    "type": "none",
                    "iso_name": "guest-tools.iso",
                },
                "networks": [
                    {
                        "name": "Host internal management network",
                    },
                ],
            },
            "ansible-test-vm-4-all-params-changed.json",
        ),
    ],
    "ids": [
        "ansible-test-vm-1-all-params-changed",
        "ansible-test-vm-2-all-params-changed",
        "ansible-test-vm-3-all-params-changed",
        "ansible-test-vm-4-all-params-changed",
    ],
}
