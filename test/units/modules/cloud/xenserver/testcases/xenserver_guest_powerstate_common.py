# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


testcase_powerstate_change = {
    "params": [
        (
            {
                "name": "ansible-test-vm-1",
                "state": "powered-on",
            },
            "ansible-test-vm-1.json",
            False,
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "state": "powered-off",
            },
            "ansible-test-vm-1-poweredoff.json",
            True,
        ),
        (
            {
                "name": "ansible-test-vm-1",
                "state": "shutdown-guest",
                "state_change_timeout": 10,
            },
            "ansible-test-vm-1-poweredoff.json",
            True,
        ),
        (
            {
                "name": "ansible-test-vm-3",
                "state": "powered-on",
            },
            "ansible-test-vm-3-poweredon.json",
            True,
        ),
        (
            {
                "name": "ansible-test-vm-3",
                "state": "powered-off",
            },
            "ansible-test-vm-3.json",
            False,
        ),
    ],
    "ids": [
        "ansible-test-vm-1-powered-on",
        "ansible-test-vm-1-powered-off",
        "ansible-test-vm-1-shutdown-guest",
        "ansible-test-vm-3-powered-on",
        "ansible-test-vm-3-powered-off",
    ],
}

testcase_powerstate_change_check_mode = {
    "params": [(testcase[0], "%s.json" % testcase[0]['name'], testcase[2]) for testcase in testcase_powerstate_change['params']],
    "ids": testcase_powerstate_change['ids'],
}

testcase_powerstate_change_wait_for_ip_address = {
    "params": [
        (
            {
                "name": "ansible-test-vm-3",
                "state": "powered-on",
                "wait_for_ip_address": True,
            },
            "ansible-test-vm-3-poweredon.json",
            True,
        ),
    ],
    "ids": [
        "ansible-test-vm-3-powered-on-wait-ip",
    ],
}

testcase_no_powerstate_change_wait_for_ip_address = {
    "params": [
        (
            {
                "name": "ansible-test-vm-1",
                "wait_for_ip_address": True,
            },
            "ansible-test-vm-1.json",
            False,
        ),
        (
            {
                "name": "ansible-test-vm-2",
                "state_change_timeout": 10,
                "wait_for_ip_address": True,
            },
            "ansible-test-vm-2.json",
            False,
        ),
    ],
    "ids": [
        "ansible-test-vm-1-present-wait-ip",
        "ansible-test-vm-2-present-wait-ip",
    ],
}
