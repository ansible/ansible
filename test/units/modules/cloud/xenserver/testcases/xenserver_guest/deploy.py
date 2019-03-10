# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


testcase_deploy_failures = {
    "params": [
        (
            {
                "name": "ansible-test-vm-1",
            },
            "Called deploy on existing VM!",
        ),
        (
            {
                "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
            },
            "Called deploy on existing VM!",
        ),
        (
            {
                "name": "some-vm-name",
                "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
            },
            "Called deploy on existing VM!",
        ),
        (
            {
                "name": "some-vm-name",
            },
            "VM deploy: no valid name or UUID supplied for template!",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "nonexistent-template-name",
            },
            "VM deploy: template with name 'nonexistent-template-name' not found!",
        ),
        (
            {
                "name": "some-vm-name",
                "template_uuid": "nonexistent-template-uuid",
            },
            "VM deploy: template with UUID 'nonexistent-template-uuid' not found!",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "nonexistent-template-name",
                "template_uuid": "nonexistent-template-uuid",
            },
            "VM deploy: template with UUID 'nonexistent-template-uuid' not found!",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "ansible-test-vm-1",
            },
            "VM deploy: running VM cannot be used as a template!",
        ),
        (
            {
                "name": "some-vm-name",
                "template_uuid": "81c373d7-a407-322f-911b-31386eb5215d",
            },
            "VM deploy: running VM cannot be used as a template!",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "ansible-test-vm-1",
                "template_uuid": "81c373d7-a407-322f-911b-31386eb5215d",
            },
            "VM deploy: running VM cannot be used as a template!",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "ansible-test-vm-3",
            },
            "VM deploy disks[0]: no default SR found! You must specify SR explicitly.",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "ansible-test-vm-3",
                "template_uuid": None,
                "disks": [],
            },
            "VM deploy disks[0]: no default SR found! You must specify SR explicitly.",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "ansible-test-vm-3",
                "template_uuid": None,
                "disks": [{}],
            },
            "VM deploy disks[0]: no default SR found! You must specify SR explicitly.",
        ),
        (
            {
                "name": "",
                "uuid": "some-uuid",
                "template": "ansible-test-vm-3",
                "disks": [
                    {
                        "sr": "Ansible Test Storage 1",
                    },
                ],
            },
            "VM deploy: VM name must not be an empty string!",
        ),
    ],
    "ids": [
        "vm-found-name",
        "vm-found-uuid",
        "vm-found-name+uuid",
        "template-not-specified",
        "template-not-found-name",
        "template-not-found-uuid",
        "template-not-found-name+uuid",
        "template-running-name",
        "template-running-uuid",
        "template-running-name+uuid",
        "disks-not-specified",
        "disks-empty",
        "disks-no-sr-specified",
        "vm-name-is-empty-string",
    ],
}


testcase_deploy = {
    "params": [
        (
            {
                "name": "some-vm-name",
                "template": "CentOS 7",
            },
            "centos-7-template-deployed.json",
        ),
        (
            {
                "name": "some-vm-name",
                "template_uuid": "11fd3dc9-96cc-49af-b091-a2ca7e94c589",
            },
            "centos-7-template-deployed.json",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "CentOS 7",
                "state": "poweredon",
            },
            "centos-7-template-deployed-poweredon.json",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "CentOS 7",
                "linked_clone": True,
                "state": "poweredon",
            },
            "centos-7-template-deployed-poweredon.json",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "Other install media",
                "state": "poweredon",
            },
            "other-template-deployed-poweredon.json",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "Other install media",
                "linked_clone": True,
                "state": "poweredon",
            },
            "other-template-deployed-poweredon.json",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "ansible-test-vm-3",
                "state": "poweredon",
                "disks": [
                    {
                        "sr": "Ansible Test Storage 1",
                    },
                ],
            },
            "ansible-test-vm-3-template-deployed-poweredon.json",
        ),
        (
            {
                "name": "some-vm-name",
                "template": "ansible-test-vm-3",
                "linked_clone": True,
                "state": "poweredon",
                "disks": [
                    {
                        "sr_uuid": "64863124-6f51-9872-55e7-6790fd8d3d8d",
                    },
                ],
            },
            "ansible-test-vm-3-template-deployed-poweredon.json",
        ),
    ],
    "ids": [
        "centos-7-template-name",
        "centos-7-template-uuid",
        "centos-7-template-poweredon",
        "centos-7-template-linked_clone+poweredon",
        "other-template-poweredon",
        "other-template-linked_clone+poweredon",
        "ansible-test-vm-3-template-sr+poweredon",
        "ansible-test-vm-3-template-sr_uuid+linked_clone+poweredon",
    ],
}
