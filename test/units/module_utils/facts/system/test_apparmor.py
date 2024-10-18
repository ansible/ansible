# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.facts.system.apparmor import ApparmorFactCollector


class TestApparmorFacts:
    @pytest.mark.parametrize(
        ("test_input", "expected"),
        [
            pytest.param(
                True,
                "enabled",
                id="enabled",
            ),
            pytest.param(
                False,
                "disabled",
                id="disabled",
            ),
        ],
    )
    def test_apparmor_status(self, mocker, test_input, expected):
        mocker.patch("os.path.exists", return_value=test_input)
        apparmor_facts = ApparmorFactCollector().collect()
        assert "apparmor" in apparmor_facts
        assert "status" in apparmor_facts["apparmor"]
        assert apparmor_facts["apparmor"]["status"] == expected
