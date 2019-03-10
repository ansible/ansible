# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


testcase_get_cdrom_type = {
    "params": [
        (
            {
                "empty": True,
            },
            "none",
        ),
        (
            {
                "empty": False,
            },
            "iso",
        ),
    ],
    "ids": [
        "cdrom-type-none",
        "cdrom-type-iso",
    ],
}
