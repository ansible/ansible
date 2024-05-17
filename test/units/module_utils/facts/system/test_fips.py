# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.facts.system.fips import FipsFactCollector


class TestFIPSFacts:
    def test_fips_enabled(self, mocker):
        mocker.patch('ansible.module_utils.facts.system.fips.get_file_content', return_value='1')
        fips_mgr = FipsFactCollector().collect()
        assert fips_mgr['fips'] is True

    def test_fips_disbled(self, mocker):
        mocker.patch('ansible.module_utils.facts.system.fips.get_file_content', return_value='0')
        fips_mgr = FipsFactCollector().collect()
        assert fips_mgr['fips'] is False
