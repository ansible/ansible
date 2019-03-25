# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


def fake_xenapi_ref(xenapi_class):
    return "OpaqueRef:fake-xenapi-%s-ref" % xenapi_class


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
