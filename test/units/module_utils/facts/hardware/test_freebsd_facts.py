# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pathlib
import json

import pytest

from ansible.module_utils.facts.hardware import freebsd
from ansible.module_utils.facts.sysctl import get_sysctl


class TestFreeBSDHardwareFacts:
    fixtures = pathlib.Path(__file__).parent / "fixtures"

    def _get_mock_sysctl_data(self):
        return (self.fixtures / "sysctl_freebsd.txt").read_text()

    def _get_mock_dmesg_data(self):
        return (self.fixtures / "dmesg_freebsd.txt").read_text()

    @pytest.fixture()
    def mocked_module(self, mocker, request):
        request.cls.module = mocker.MagicMock()
        yield request.cls.module

    def test_get_dmi_facts(self, mocker, mocked_module):
        freebsd_hardware = freebsd.FreeBSDHardware(mocked_module)
        mocker.patch.object(
            mocked_module,
            "get_bin_path",
            side_effect=[
                "/usr/local/sbin/dmidecode",
            ],
        )
        expected_dmi_facts = {
            "bios_date": "2024-05-10",
            "bios_vendor": "American Megatrends Inc.",
            "bios_version": "1.2.3",
            "board_asset_tag": "MyAssetTag1",
            "board_name": "Motherboard X399",
            "board_serial": "1234ABCD-EFGH-5678",
            "board_vendor": "Gigabyte Technology Co., Ltd.",
            "board_version": "A00",
            "chassis_asset_tag": "MyChassisTag",
            "chassis_serial": "9876-FEDC-BA09",
            "chassis_vendor": "InWin Development Inc.",
            "chassis_version": "Not Available",
            "form_factor": "8 (Tower)",
            "product_name": "ProBook 450 G8",
            "product_serial": "CDEFG1234567890A",
            "product_uuid": "123e4567-e89b-12d3-a456-426655440000",
            "product_version": "Not Available",
            "system_vendor": "Hewlett-Packard",
        }
        side_effect_list = [(0, i, "") for i in expected_dmi_facts.values()]

        mocker.patch.object(mocked_module, "run_command", side_effect=side_effect_list)

        dmi_facts = freebsd_hardware.get_dmi_facts()
        assert dmi_facts == expected_dmi_facts

    def test_get_cpu_facts(self, mocker, mocked_module):
        mocker.patch.object(
            mocked_module,
            "get_bin_path",
            side_effect=[
                "/sbin/sysctl",
                "/sbin/dmesg",
            ],
        )
        mocker.patch.object(
            mocked_module,
            "run_command",
            side_effect=[
                (0, self._get_mock_sysctl_data(), ""),
                (0, self._get_mock_dmesg_data(), ""),
            ],
        )

        freebsd_hardware = freebsd.FreeBSDHardware(mocked_module)
        freebsd_hardware.sysctl = get_sysctl(mocked_module, ["hw", "vm.stats"])

        cpu_facts = freebsd_hardware.get_cpu_facts()
        expected_cpu_facts = {
            "processor": [
                "Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz (2893.05-MHz K8-class CPU)"
            ],
            "processor_cores": "2",
            "processor_count": "4",
        }
        assert cpu_facts == expected_cpu_facts

    def test_get_memory_facts(self, mocked_module):
        mocked_module.get_bin_path.side_effect = [
            "/sbin/sysctl",
            "/usr/sbin/swapinfo",
        ]

        mocked_swapinfo_k_output = (self.fixtures / "swapinfo_freebsd.txt").read_text()
        mocked_module.run_command.side_effect = [
            (0, self._get_mock_sysctl_data(), ""),
            (0, mocked_swapinfo_k_output, ""),
        ]
        freebsd_hardware = freebsd.FreeBSDHardware(mocked_module)
        freebsd_hardware.sysctl = get_sysctl(mocked_module, ["hw", "vm.stats"])

        memory_facts = freebsd_hardware.get_memory_facts()
        expected_memory_facts = {
            "memtotal_mb": 3967,
            "memfree_mb": 267,
            "swapfree_mb": 1024,
            "swaptotal_mb": 1024,
        }
        assert memory_facts == expected_memory_facts

    def test_get_uptime_facts(self, mocked_module):
        freebsd_hardware = freebsd.FreeBSDHardware(mocked_module)
        mocked_module.run_command.return_value = (
            0,
            b"\xc0\xa0\x05f\x00\x00\x00\x00\xac-\x05\x00\x00\x00\x00\x00",
            "",
        )
        uptime_facts = freebsd_hardware.get_uptime_facts()
        assert "uptime_seconds" in uptime_facts

    def _mock_get_statvfs_output(self, mount_point):
        mount_info = {
            "/": {
                "size_total": 494384795648,
                "size_available": 331951407104,
                "block_size": 1048576,
                "block_total": 120699413,
                "block_available": 81042824,
                "block_used": 39656589,
                "inode_total": 3242116715,
                "inode_available": 3241712960,
                "inode_used": 403755,
            }
        }
        return mount_info.get(mount_point, {})

    def test_get_mount_facts(self, mocker, mocked_module):
        freebsd_hardware = freebsd.FreeBSDHardware(mocked_module)
        mocked_fstab_output = (self.fixtures / "fstab_freebsd.txt").read_text()
        mocker.patch(
            "ansible.module_utils.facts.hardware.freebsd.get_file_content",
            return_value=mocked_fstab_output,
        )
        mocker.patch(
            "ansible.module_utils.facts.hardware.freebsd.get_mount_size",
            side_effect=self._mock_get_statvfs_output,
        )

        fstab_facts = freebsd_hardware.get_mount_facts()
        expected_fstab_facts = {
            "mounts": [
                {
                    "mount": "/",
                    "device": "/dev/gpt/rootfs",
                    "fstype": "ufs",
                    "options": "rw",
                    "size_total": 494384795648,
                    "size_available": 331951407104,
                    "block_size": 1048576,
                    "block_total": 120699413,
                    "block_available": 81042824,
                    "block_used": 39656589,
                    "inode_total": 3242116715,
                    "inode_available": 3241712960,
                    "inode_used": 403755,
                },
                {
                    "mount": "none",
                    "device": "/dev/gpt/swapfs",
                    "fstype": "swap",
                    "options": "sw",
                },
                {
                    "mount": "/boot/efi",
                    "device": "/dev/gpt/efiesp",
                    "fstype": "msdosfs",
                    "options": "rw",
                },
            ]
        }
        assert fstab_facts == expected_fstab_facts

    def test_get_device_facts(self, mocker):
        dev_dir = (self.fixtures / "devices_freebsd.txt").read_text().split()
        with open(self.fixtures / "expected_devices_freebsd.txt", "r") as fd:
            expected_dev_dir = json.load(fd)

        mocker.patch("os.path.isdir", return_value=True)
        mocker.patch("os.listdir", return_value=dev_dir)

        freebsd_hardware = freebsd.FreeBSDHardware(None)
        facts = freebsd_hardware.get_device_facts()
        assert facts == expected_dev_dir
