# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import pytest

from ansible.module_utils.facts.virtual.sysctl import VirtualSysctlDetectionMixin


class MockVirtualSysctl(VirtualSysctlDetectionMixin):
    def __init__(self, module):
        self.module = module


@pytest.mark.parametrize("expected_path", ["/usr/sbin/sysctl", "/sbin/sysctl"])
def test_detect_sysctl(mocker, expected_path):
    module = mocker.Mock()
    module.get_bin_path.return_value = expected_path
    mixin = MockVirtualSysctl(module=module)
    mixin.detect_sysctl()

    assert mixin.sysctl_path == expected_path


@pytest.mark.parametrize(
    ("virt_product", "expected_guest"),
    [
        pytest.param(
            "KVM",
            "kvm",
            id="KVM-all-caps",
        ),
        pytest.param(
            "kvm",
            "kvm",
            id="kvm",
        ),
        pytest.param(
            "Bochs",
            "kvm",
            id="Bochs",
        ),
        pytest.param(
            "SmartDC",
            "kvm",
            id="SmartDC",
        ),
        pytest.param(
            "VMware",
            "VMware",
            id="VMware",
        ),
        pytest.param(
            "VirtualBox",
            "virtualbox",
            id="VirtualBox",
        ),
        pytest.param(
            "HVM domU",
            "xen",
            id="Xen-HVM",
        ),
        pytest.param(
            "XenPVH",
            "xen",
            id="Xen-PVH",
        ),
        pytest.param(
            "XenPV",
            "xen",
            id="Xen-PV",
        ),
        pytest.param(
            "XenPVHVM",
            "xen",
            id="Xen-PVHVM",
        ),
        pytest.param(
            "Hyper-V",
            "Hyper-V",
            id="Hyper-V",
        ),
        pytest.param(
            "Parallels",
            "parallels",
            id="Parallels",
        ),
        pytest.param(
            "RHEV Hypervisor",
            "RHEV",
            id="RHEV",
        ),
        pytest.param(
            "1",
            "jails",
            id="Jails",
        ),
    ],
)
def test_detect_virt_product(mocker, virt_product, expected_guest):
    module = mocker.Mock()
    module.get_bin_path.return_value = "/usr/bin/sysctl"
    module.run_command.return_value = (0, virt_product, "")
    mixin = MockVirtualSysctl(module=module)
    guest_facts = mixin.detect_virt_product("security.jail.jailed")
    expected = {
        "virtualization_role": "guest",
        "virtualization_tech_guest": set([expected_guest]),
        "virtualization_tech_host": set(),
        "virtualization_type": expected_guest,
    }
    assert guest_facts == expected


@pytest.mark.parametrize(
    ("virt_product", "expected_guest"),
    [
        pytest.param(
            "QEMU",
            "kvm",
            id="QEMU",
        ),
        pytest.param(
            "OpenBSD",
            "vmm",
            id="OpenBSD-vmm",
        ),
    ],
)
def test_detect_virt_vendor(mocker, virt_product, expected_guest):
    module = mocker.Mock()
    module.get_bin_path.return_value = "/usr/bin/sysctl"
    module.run_command.return_value = (0, virt_product, "")
    mixin = MockVirtualSysctl(module=module)
    guest_facts = mixin.detect_virt_vendor("security.jail.jailed")
    expected = {
        "virtualization_role": "guest",
        "virtualization_tech_guest": set([expected_guest]),
        "virtualization_tech_host": set(),
        "virtualization_type": expected_guest,
    }
    assert guest_facts == expected
