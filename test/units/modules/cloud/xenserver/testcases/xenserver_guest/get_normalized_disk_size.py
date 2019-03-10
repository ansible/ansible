# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


testcase_get_normalized_disk_size_failures = {
    "params": [
        (
            {
                "size": "abcd",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size": "a128",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size": "-128",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size": "0",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size": "0.1",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size_gb": "abcd",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size_gb": "a128",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size_gb": "-128",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size_gb": "0",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size_": "0.1",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size_gb": "1mb",
            },
            "failed to parse disk size! Please review value provided using documentation.",
        ),
        (
            {
                "size": "1jb",
            },
            "'jb' is not a supported unit for disk size! Supported units are ['b', 'kb', 'mb', 'gb', 'tb'].",
        ),
        (
            {
                "size": "1 JB",
            },
            "'jb' is not a supported unit for disk size! Supported units are ['b', 'kb', 'mb', 'gb', 'tb'].",
        ),
        (
            {
                "size_jb": "1",
            },
            "'jb' is not a supported unit for disk size! Supported units are ['b', 'kb', 'mb', 'gb', 'tb'].",
        ),
        (
            {
                "size_JB": "1",
            },
            "'jb' is not a supported unit for disk size! Supported units are ['b', 'kb', 'mb', 'gb', 'tb'].",
        ),
    ],
    "ids": [
        "size-abcd",
        "size-a128",
        "size--128",
        "size-0",
        "size-0.1",
        "size_gb-abcd",
        "size_gb-a128",
        "size_gb--128",
        "size_gb-0",
        "size_-0.1",
        "size_gb-1mb",
        "size-1jb",
        "size-1 JB",
        "size_jb-1",
        "size_JB-1",
    ],
}

testcase_get_normalized_disk_size = {
    "params": [
        (
            {
                "size": "2gb",
                "size_mb": "1",
                "size_kb": "1",
            },
            2147483648,
        ),
        (
            {
                "size": "1tb",
            },
            1099511627776,
        ),
        (
            {
                "size": "2 gb",
            },
            2147483648,
        ),
        (
            {
                "size": "4MB",
            },
            4194304,
        ),
        (
            {
                "size": "3 Kb",
            },
            3072,
        ),
        (
            {
                "size": "8",
            },
            8,
        ),
        (
            {
                "size": "1.5kb",
            },
            1536,
        ),
        (
            {
                "size": "4.5 kb",
            },
            4608,
        ),
        (
            {
                "size_tb": "1",
            },
            1099511627776,
        ),
        (
            {
                "size_GB": "2",
            },
            2147483648,
        ),
        (
            {
                "size_Mb": "4",
            },
            4194304,
        ),
        (
            {
                "size_kB": "3",
            },
            3072,
        ),
        (
            {
                "size_b": "8",
            },
            8,
        ),
        (
            {
                "size_": "16",
            },
            16,
        ),
        (
            {
                "size_kb": "1.5",
            },
            1536,
        ),
        (
            {
                "size_b": "32.55",
            },
            32,
        ),
        (
            {},
            None,
        ),
    ],
    "ids": [
        "size+size_mb+size_kb",
        "size-1tb",
        "size-2 gb",
        "size-4MB",
        "size-3 Kb",
        "size-8",
        "size-1.5kb",
        "size-4.5 kb",
        "size_tb-1",
        "size_GB-2",
        "size_Mb-4",
        "size_kB-3",
        "size_b-8",
        "size_16",
        "size_kb-1.5",
        "size_b-32.55",
        "size-not-specified",
    ],
}
