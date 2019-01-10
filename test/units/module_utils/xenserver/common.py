# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


fake_xenapi_refs = {
    "sesion": "OpaqueRef:fake-xenapi-session-ref",
    "pool": "OpaqueRef:fake-xenapi-pool-ref",
    "host": "OpaqueRef:fake-xenapi-host-ref",
    "sr": "OpaqueRef:fake-xenapi-sr-ref",
    "vm": "OpaqueRef:fake-xenapi-vm-ref",
    "vm_guest_metrics": "OpaqueRef:fake-xenapi-vm-guest-metrics-ref",
    "task": "OpaqueRef:fake-xenapi-task-ref",
    "VBD": "OpaqueRef:fake-xenapi-VBD-ref",
    "VDI": "OpaqueRef:fake-xenapi-VDI-ref",
    "VIF": "OpaqueRef:fake-xenapi-VIF-ref",
}

testcase_bad_xenapi_refs = {
    "params": [
        None,
        '',
        'OpaqueRef:NULL',
    ],
    "ids": [
        'none',
        'empty',
        'ref-null',
    ],
}
