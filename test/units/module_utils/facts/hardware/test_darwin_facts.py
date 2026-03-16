# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pathlib

import pytest

from ansible.module_utils.facts.hardware import darwin
from ansible.module_utils.facts.sysctl import get_sysctl


class TestDarwinHardwareFacts:
    def _get_mock_sysctl_data(self, filename="sysctl_darwin_silicon.txt"):
        fixture_file = pathlib.Path(__file__).parent / "fixtures" / filename
        return fixture_file.read_text()

    @pytest.fixture()
    def mocked_module(self, mocker, request):
        request.cls.module = mocker.MagicMock()
        request.cls.module.get_bin_path.return_value = "/usr/sbin/sysctl"
        yield request.cls.module

    def test_get_mac_facts(self, mocked_module):
        mocked_module.run_command.return_value = (0, self._get_mock_sysctl_data(), "")
        darwin_hardware = darwin.DarwinHardware(mocked_module)
        darwin_hardware.sysctl = get_sysctl(
            mocked_module, ["hw", "machdep", "kern", "hw.model"]
        )

        mac_facts = darwin_hardware.get_mac_facts()
        expected_mac_facts = {
            "model": "MacBookPro18,1",
            "product_name": "MacBookPro18,1",
            "osversion": "23E224",
            "osrevision": "199506",
        }
        assert mac_facts == expected_mac_facts

    def test_get_cpu_facts(self, mocked_module):
        mocked_module.run_command.return_value = (0, self._get_mock_sysctl_data(), "")
        darwin_hardware = darwin.DarwinHardware(mocked_module)
        darwin_hardware.sysctl = get_sysctl(
            mocked_module, ["hw", "machdep", "kern", "hw.model"]
        )

        cpu_facts = darwin_hardware.get_cpu_facts()
        expected_cpu_facts = {
            "processor": "Apple M1 Pro",
            "processor_cores": "10",
            "processor_vcpus": "10",
        }
        assert cpu_facts == expected_cpu_facts

    @pytest.mark.parametrize(
        ("vm_stat_file", "sysctl_file", "expected_memory_facts"),
        [
            pytest.param(
                "vm_stat_darwin_intel.txt",
                "sysctl_darwin_intel.txt",
                {'memtotal_mb': 2048, 'memfree_mb': 178},
                id="intel",
            ),
            pytest.param(
                "vm_stat_darwin_silicon.txt",
                "sysctl_darwin_silicon.txt",
                {"memtotal_mb": 32768, "memfree_mb": 7660},
                id="silicon",
            ),
        ],
    )
    def test_get_memory_facts(self, mocked_module, vm_stat_file, sysctl_file, expected_memory_facts):
        fixtures = pathlib.Path(__file__).parent / "fixtures"
        mocked_module.get_bin_path.side_effect = [
            "/usr/sbin/sysctl",
            "/usr/bin/vm_stat",
        ]
        mocked_vm_stat = (fixtures / vm_stat_file).read_text()
        mocked_module.run_command.side_effect = [
            (0, self._get_mock_sysctl_data(filename=sysctl_file), ""),
            (0, mocked_vm_stat, ""),
        ]
        darwin_hardware = darwin.DarwinHardware(mocked_module)
        darwin_hardware.sysctl = get_sysctl(
            mocked_module, ["hw", "machdep", "kern", "hw.model"]
        )

        memory_facts = darwin_hardware.get_memory_facts()
        assert memory_facts == expected_memory_facts

    def test_get_uptime_facts(self, mocked_module):
        darwin_hardware = darwin.DarwinHardware(mocked_module)
        mocked_module.run_command.return_value = (
            0,
            b"\xc0\xa0\x05f\x00\x00\x00\x00\xac-\x05\x00\x00\x00\x00\x00",
            "",
        )
        uptime_facts = darwin_hardware.get_uptime_facts()
        assert "uptime_seconds" in uptime_facts
