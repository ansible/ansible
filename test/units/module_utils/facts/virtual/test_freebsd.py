# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import pytest

from ansible.module_utils.facts.virtual.freebsd import FreeBSDVirtual

HW_MODEL = 'Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz\n'


def _make_module(mocker, sysctl_values, kldstat_rc):
    module = mocker.Mock()
    module.get_bin_path.side_effect = lambda name: '/sbin/%s' % name

    def run_command(cmd):
        if cmd.startswith('/sbin/sysctl -n '):
            key = cmd.split(' -n ', 1)[1]
            return (0, sysctl_values.get(key, ''), '')
        if cmd == '/sbin/kldstat -q -m vmm':
            return (kldstat_rc, '', '')
        return (1, '', '')

    module.run_command.side_effect = run_command
    return module


@pytest.mark.parametrize(
    ('sysctl_values', 'kldstat_rc', 'expected'),
    [
        pytest.param(
            {
                'kern.vm_guest': 'none\n',
                'hw.hv_vendor': '\n',
                'security.jail.jailed': '1\n',
                'hw.model': HW_MODEL,
            },
            0,
            {
                'virtualization_type': 'jails',
                'virtualization_role': 'guest',
                'virtualization_tech_guest': {'jails'},
                'virtualization_tech_host': set(),
            },
            id='jail-on-bhyve-host-is-reported-as-jail',
        ),
        pytest.param(
            {
                'kern.vm_guest': 'none\n',
                'hw.hv_vendor': '\n',
                'security.jail.jailed': '1\n',
                'hw.model': HW_MODEL,
            },
            1,
            {
                'virtualization_type': 'jails',
                'virtualization_role': 'guest',
                'virtualization_tech_guest': {'jails'},
                'virtualization_tech_host': set(),
            },
            id='jail-on-non-bhyve-host-is-reported-as-jail',
        ),
        pytest.param(
            {
                'kern.vm_guest': 'none\n',
                'hw.hv_vendor': '\n',
                'security.jail.jailed': '0\n',
                'hw.model': HW_MODEL,
            },
            0,
            {
                'virtualization_type': 'bhyve',
                'virtualization_role': 'host',
                'virtualization_tech_guest': set(),
                'virtualization_tech_host': {'bhyve'},
            },
            id='bhyve-hypervisor-is-reported-as-host',
        ),
        pytest.param(
            {
                'kern.vm_guest': 'bhyve\n',
                'hw.hv_vendor': 'bhyve\n',
                'security.jail.jailed': '0\n',
                'hw.model': HW_MODEL,
            },
            0,
            {
                'virtualization_type': 'bhyve',
                'virtualization_role': 'guest',
                'virtualization_tech_guest': {'bhyve'},
                'virtualization_tech_host': set(),
            },
            id='bhyve-guest-vm-is-not-reported-as-host',
        ),
    ],
)
def test_freebsd_virtual_facts(mocker, sysctl_values, kldstat_rc, expected):
    # Regression test: a jail shares the host kernel, so `kldstat -q -m vmm`
    # succeeds inside a jail running on a bhyve host (the host has vmm(4)
    # loaded). The hypervisor probe must not overwrite the jail facts
    # (jails/guest) with the host's bhyve facts (bhyve/host), while a
    # bare-metal bhyve hypervisor is still reported as bhyve/host and a bhyve
    # guest VM stays a guest.
    mocker.patch('os.path.exists', return_value=False)
    module = _make_module(mocker, sysctl_values, kldstat_rc)

    facts = FreeBSDVirtual(module).get_virtual_facts()

    assert facts == expected
