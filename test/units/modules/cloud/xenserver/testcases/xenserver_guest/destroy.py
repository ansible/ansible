# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


testcase_destroy_failures = {
    "params": [
        (
            {
                "name": "nonexistent-vm-name",
            },
            "Called destroy on non existing VM!",
        ),
        (
            {
                "uuid": "nonexistent-vm-uuid",
            },
            "Called destroy on non existing VM!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "uuid": "nonexistent-vm-uuid",
            },
            "Called destroy on non existing VM!",
        ),
        (
            {
                "name": "ansible-test-vm-1",
            },
            "VM destroy: VM has to be in powered off state to destroy but force was not specified!",
        ),
    ],
    "ids": [
        "vm-not-found-name",
        "vm-not-found-uuid",
        "vm-not-found-name+uuid",
        "vm-not-poweredoff",
    ],
}

testcase_destroy = {
    "params": [
        (
            {
                "name": "ansible-test-vm-3",
                "state": "absent",
            },
            "ansible-test-vm-3.json",
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "state": "absent",
                "force": True,
                "wait_for_ip_address": True,
                "state_change_timeout": 10,
            },
            "ansible-test-vm-1-poweredoff.json",
        ),
    ],
    "ids": [
        "ansible-test-vm-3",
        "ansible-test-vm-1",
    ],
}

# We reuse testcase_destroy but we override fake_vm_facts .json file to
# default one.
testcase_destroy_check_mode = {
    "params": [(testcase[0], "%s.json" % testcase[0]['name']) for testcase in testcase_destroy['params']],
    "ids": testcase_destroy['ids'],
}
