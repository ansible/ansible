# unit tests for ansible system cmdline fact collectors
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest
from ansible.module_utils.facts.system.cmdline import CmdLineFactCollector

test_data = [
    (
        "crashkernel=auto rd.lvm.lv=fedora_test-elementary-os/root rd.lvm.lv=fedora_test-elementary-os/swap rhgb quiet",
        {
            'crashkernel': 'auto',
            'quiet': True,
            'rd.lvm.lv': [
                'fedora_test-elementary-os/root',
                'fedora_test-elementary-os/swap',
            ],
            'rhgb': True
        }
    ),
    (
        "root=/dev/mapper/vg_ssd-root ro rd.lvm.lv=fedora_xenon/root rd.lvm.lv=fedora_xenon/swap rhgb quiet "
        "resume=/dev/mapper/fedora_xenon-swap crashkernel=128M zswap.enabled=1",
        {
            'crashkernel': '128M',
            'quiet': True,
            'rd.lvm.lv': [
                'fedora_xenon/root',
                'fedora_xenon/swap'
            ],
            'resume': '/dev/mapper/fedora_xenon-swap',
            'rhgb': True,
            'ro': True,
            'root': '/dev/mapper/vg_ssd-root',
            'zswap.enabled': '1'
        }
    ),
    (
        "rhgb",
        {
            "rhgb": True
        }
    ),
    (
        "root=/dev/mapper/vg_ssd-root",
        {
            'root': '/dev/mapper/vg_ssd-root',
        }
    ),
    (
        "",
        {},
    )
]

test_ids = ['lvm_1', 'lvm_2', 'single_without_equal_sign', 'single_with_equal_sign', 'blank_cmdline']


@pytest.mark.parametrize("cmdline, cmdline_dict", test_data, ids=test_ids)
def test_cmd_line_factor(cmdline, cmdline_dict):
    cmdline_facter = CmdLineFactCollector()
    parsed_cmdline = cmdline_facter._parse_proc_cmdline_facts(data=cmdline)
    assert parsed_cmdline == cmdline_dict
