# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import pytest

from ansible.module_utils.facts.virtual.sunos import SunOSVirtual


class MockVirtualSysctl(SunOSVirtual):
    def __init__(self, module):
        self.module = module


def mock_get_bin_path(filename):
    cmd_bins = {
        "zonename": "/usr/bin/zonename",
        "virtinfo": "/usr/sbin/virtinfo",
    }
    return cmd_bins.get(filename, None)


def test_get_virtual_facts_global(mocker):
    module = mocker.Mock()
    module.get_bin_path.side_effect = mock_get_bin_path
    module.run_command.return_value = (0, "global", "")
    mixin = MockVirtualSysctl(module=module)
    guest_facts = mixin.get_virtual_facts()
    expected = {
        "virtualization_tech_guest": set(),
        "virtualization_tech_host": set(["zone"]),
    }

    assert guest_facts == expected


@pytest.mark.parametrize(
    ("guest_tech", "expected_guest"),
    [
        pytest.param(
            "VMware",
            "vmware",
            id="VMware",
        ),
        pytest.param(
            "VirtualBox",
            "virtualbox",
            id="VirtualBox",
        ),
    ],
)
def test_get_virtual_facts_guest(mocker, guest_tech, expected_guest):
    module = mocker.Mock()
    module.get_bin_path.side_effect = [
        "/usr/bin/zonename",
        "/usr/sbin/modinfo",
        "/usr/sbin/virtinfo",
    ]
    module.run_command.side_effect = [
        (0, "local", ""),
        (0, guest_tech, ""),
        (0, "", ""),
    ]
    mixin = MockVirtualSysctl(module=module)
    guest_facts = mixin.get_virtual_facts()
    expected = {
        "virtualization_tech_guest": set([expected_guest, "zone"]),
        "virtualization_tech_host": set(),
        "virtualization_type": expected_guest,
        "virtualization_role": "guest",
        "container": "zone",
    }

    assert guest_facts == expected


@pytest.mark.parametrize(
    ("guest_tech", "expected_guest"),
    [
        pytest.param(
            "VMware",
            "vmware",
            id="VMware",
        ),
        pytest.param(
            "VirtualBox",
            "virtualbox",
            id="VirtualBox",
        ),
    ],
)
def test_get_virtual_facts_ldoms(mocker, guest_tech, expected_guest):
    module = mocker.Mock()
    module.get_bin_path.side_effect = [
        "/usr/bin/zonename",
        "/usr/sbin/modinfo",
        "/usr/sbin/virtinfo",
    ]
    module.run_command.side_effect = [
        (0, "local", ""),
        (0, guest_tech, ""),
        (0, "DOMAINROLE|impl=LDoms", ""),
    ]
    mixin = MockVirtualSysctl(module=module)
    guest_facts = mixin.get_virtual_facts()
    expected = {
        "virtualization_tech_guest": set(["ldom", expected_guest, "zone"]),
        "virtualization_tech_host": set(),
        "virtualization_type": "ldom",
        "virtualization_role": "guest",
        "container": "zone",
    }

    assert guest_facts == expected


@pytest.mark.parametrize(
    ("guest_tech", "expected_guest"),
    [
        pytest.param(
            "VMware",
            "vmware",
            id="VMware",
        ),
        pytest.param(
            "VirtualBox",
            "virtualbox",
            id="VirtualBox",
        ),
        pytest.param(
            "Parallels",
            "parallels",
            id="Parallels",
        ),
        pytest.param(
            "HVM domU",
            "xen",
            id="Xen",
        ),
        pytest.param(
            "KVM",
            "kvm",
            id="KVM",
        ),
    ],
)
def test_get_virtual_facts_smbios(mocker, guest_tech, expected_guest):
    module = mocker.Mock()
    module.get_bin_path.side_effect = [
        "/usr/bin/zonename",
        None,
        None,
        "/usr/sbin/smbios",
    ]
    module.run_command.side_effect = [
        (0, "local", ""),
        (0, guest_tech, ""),
    ]
    mixin = MockVirtualSysctl(module=module)
    guest_facts = mixin.get_virtual_facts()
    expected = {
        "virtualization_tech_guest": set([expected_guest, "zone"]),
        "virtualization_tech_host": set(),
        "virtualization_type": expected_guest,
        "virtualization_role": "guest",
        "container": "zone",
    }

    assert guest_facts == expected


def test_get_virtual_facts_openvz(mocker):
    mocker.patch("os.path.exists", return_value=True)
    module = mocker.Mock()
    module.get_bin_path.side_effect = [
        None,  # zonename
        "/usr/sbin/virtinfo",
    ]
    module.run_command.return_value = (0, "", "")
    mixin = MockVirtualSysctl(module=module)
    guest_facts = mixin.get_virtual_facts()
    expected = {
        "virtualization_role": "guest",
        "virtualization_tech_guest": set(["virtuozzo"]),
        "virtualization_tech_host": set(),
        "virtualization_type": "virtuozzo",
    }

    assert guest_facts == expected
