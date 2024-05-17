# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pathlib

from ansible.module_utils.facts.system.caps import SystemCapabilitiesFactCollector


class TestSystemCapsFacts:
    fixtures = pathlib.Path(__file__).parent / "fixtures"

    def _get_mock_capsh_data(self, *args, **kwargs):
        return

    def test_capsh_collect_no_data(self):
        cap_mgr = SystemCapabilitiesFactCollector().collect()
        assert "system_capabilities_enforced" in cap_mgr
        assert "system_capabilities" in cap_mgr
        assert cap_mgr["system_capabilities"] == "N/A"
        assert cap_mgr["system_capabilities_enforced"] == "N/A"

    def test_capsh_collect_uncertain(self, mocker):
        module = mocker.MagicMock()
        mocked_output = (self.fixtures / "capsh_uncertain.txt").read_text()
        cap_mgr = SystemCapabilitiesFactCollector().parse_caps_data(
            caps_data=mocked_output
        )
        assert cap_mgr[0] == "False"
        assert cap_mgr[1] == []

    def test_capsh_collect_hybrid(self, mocker):
        module = mocker.MagicMock()
        mocked_output = (self.fixtures / "capsh_hybrid.txt").read_text()
        cap_mgr = SystemCapabilitiesFactCollector().parse_caps_data(
            caps_data=mocked_output
        )
        assert cap_mgr[0] == "True"
        assert cap_mgr[1] == [
            "cap_chown",
            "cap_dac_override",
            "cap_fowner",
            "cap_fsetid",
            "cap_kill",
            "cap_setgid",
            "cap_setuid",
            "cap_setpcap",
            "cap_net_bind_service",
            "cap_net_raw",
            "cap_sys_chroot",
            "cap_mknod",
            "cap_audit_write",
            "cap_setfcap+eip",
        ]
