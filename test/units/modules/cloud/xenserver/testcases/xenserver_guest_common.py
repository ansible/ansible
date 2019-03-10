# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


testcase_vm_found = {
    "params": [
        (
            {
                "name": "ansible-test-vm-1",
            },
            "ansible-test-vm-1.json",
        ),
        (
            {
                "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
            },
            "ansible-test-vm-1.json",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "uuid": "81c373d7-a407-322f-911b-31386eb5215d",
            },
            "ansible-test-vm-1.json",
        ),
        (
            {
                "name": "ansible-test-vm-2",
            },
            "ansible-test-vm-2.json",
        ),
        (
            {
                "uuid": "0a05d5ad-3e4b-f0dc-6101-8c56623958bc",
            },
            "ansible-test-vm-2.json",
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "uuid": "0a05d5ad-3e4b-f0dc-6101-8c56623958bc",
            },
            "ansible-test-vm-2.json",
        ),
        (
            {
                "name": "ansible-test-vm-3",
            },
            "ansible-test-vm-3.json",
        ),
        (
            {
                "uuid": "8f5bc97c-42fa-d619-aba4-d25eced735e0",
            },
            "ansible-test-vm-3.json",
        ),
        (
            {
                "name": "ansible-test-vm-3",
                "uuid": "8f5bc97c-42fa-d619-aba4-d25eced735e0",
            },
            "ansible-test-vm-3.json",
        ),
        (
            {
                "name": "ansible-test-vm-4",
            },
            "ansible-test-vm-4.json",
        ),
        (
            {
                "uuid": "92181f0c-4a6b-ca53-25dc-6fda6a9f6835",
            },
            "ansible-test-vm-4.json",
        ),
        (
            {
                "name": "ansible-test-vm-4",
                "uuid": "92181f0c-4a6b-ca53-25dc-6fda6a9f6835",
            },
            "ansible-test-vm-4.json",
        ),
    ],
    "ids": [
        "ansible-test-vm-1-name",
        "ansible-test-vm-1-uuid",
        "ansible-test-vm-1-name+uuid",
        "ansible-test-vm-2-name",
        "ansible-test-vm-2-uuid",
        "ansible-test-vm-2-name+uuid",
        "ansible-test-vm-3-name",
        "ansible-test-vm-3-uuid",
        "ansible-test-vm-3-name+uuid",
        "ansible-test-vm-4-name",
        "ansible-test-vm-4-uuid",
        "ansible-test-vm-4-name+uuid",
    ],
}

testcase_vm_not_found = {
    "params": [
        {
            "name": "nonexistent-vm-name",
        },
        {
            "uuid": "nonexistent-vm-uuid",
        },
        {
            "name": "ansible-test-vm-1",
            "uuid": "nonexistent-vm-uuid",
        },
    ],
    "ids": [
        "nonexistent-vm-name",
        "nonexistent-vm-uuid",
        "nonexistent-vm-name+uuid",
    ],
}
