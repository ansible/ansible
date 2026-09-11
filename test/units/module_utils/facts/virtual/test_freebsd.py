# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.facts.virtual.freebsd import FreeBSDVirtual


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


def test_freebsd_jail_on_bhyve_host_is_reported_as_jail(mocker):
    # Regression test: a jail shares the host kernel, so `kldstat -q -m vmm`
    # succeeds inside a jail running on a bhyve host (the host has vmm(4)
    # loaded). The hypervisor probe must not overwrite the jail facts
    # (jails/guest) with the host's bhyve facts (bhyve/host).
    mocker.patch('os.path.exists', return_value=False)
    module = _make_module(
        mocker,
        {
            'kern.vm_guest': 'none\n',
            'hw.hv_vendor': '\n',
            'security.jail.jailed': '1\n',
            'hw.model': 'Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz\n',
        },
        kldstat_rc=0,
    )

    facts = FreeBSDVirtual(module).get_virtual_facts()

    assert facts['virtualization_type'] == 'jails'
    assert facts['virtualization_role'] == 'guest'
    assert facts['virtualization_tech_guest'] == {'jails'}
    assert 'bhyve' not in facts['virtualization_tech_host']


def test_freebsd_jail_on_non_bhyve_host_is_reported_as_jail(mocker):
    mocker.patch('os.path.exists', return_value=False)
    module = _make_module(
        mocker,
        {
            'kern.vm_guest': 'none\n',
            'hw.hv_vendor': '\n',
            'security.jail.jailed': '1\n',
            'hw.model': 'Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz\n',
        },
        kldstat_rc=1,
    )

    facts = FreeBSDVirtual(module).get_virtual_facts()

    assert facts['virtualization_type'] == 'jails'
    assert facts['virtualization_role'] == 'guest'
    assert facts['virtualization_tech_guest'] == {'jails'}


def test_freebsd_bhyve_hypervisor_is_reported_as_host(mocker):
    # The kldstat(8) probe must still detect a bare-metal host running the
    # bhyve hypervisor (vmm(4) loaded), which is not itself a guest.
    mocker.patch('os.path.exists', return_value=False)
    module = _make_module(
        mocker,
        {
            'kern.vm_guest': 'none\n',
            'hw.hv_vendor': '\n',
            'security.jail.jailed': '0\n',
            'hw.model': 'Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz\n',
        },
        kldstat_rc=0,
    )

    facts = FreeBSDVirtual(module).get_virtual_facts()

    assert facts['virtualization_type'] == 'bhyve'
    assert facts['virtualization_role'] == 'host'
    assert facts['virtualization_tech_host'] == {'bhyve'}


def test_freebsd_bhyve_guest_vm_is_not_reported_as_host(mocker):
    # A VM running under bhyve is a guest (kern.vm_guest=bhyve); the kldstat(8)
    # probe must not turn it into bhyve/host even if it somehow exits 0.
    mocker.patch('os.path.exists', return_value=False)
    module = _make_module(
        mocker,
        {
            'kern.vm_guest': 'bhyve\n',
            'hw.hv_vendor': 'bhyve\n',
            'security.jail.jailed': '0\n',
            'hw.model': 'Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz\n',
        },
        kldstat_rc=0,
    )

    facts = FreeBSDVirtual(module).get_virtual_facts()

    assert facts['virtualization_type'] == 'bhyve'
    assert facts['virtualization_role'] == 'guest'
    assert facts['virtualization_tech_guest'] == {'bhyve'}
