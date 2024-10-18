# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.facts.system.loadavg import LoadAvgFactCollector


class TestLoadAvgFacts:
    def test_loadaverage(self, mocker):
        expected_load_avg = (2.53271484375, 3.1552734375, 3.48046875)
        mocker.patch("os.getloadavg", return_value=expected_load_avg)
        loadavg_facts = LoadAvgFactCollector().collect()
        assert "loadavg" in loadavg_facts
        assert "1m" in loadavg_facts["loadavg"]
        assert "5m" in loadavg_facts["loadavg"]
        assert "15m" in loadavg_facts["loadavg"]
        assert loadavg_facts["loadavg"]["1m"] == expected_load_avg[0]
        assert loadavg_facts["loadavg"]["5m"] == expected_load_avg[1]
        assert loadavg_facts["loadavg"]["15m"] == expected_load_avg[2]

    def _mock_get_load_avg_exception(self):
        raise OSError("fake os.getloadavg exception")

    def test_loadaverage_negative(self, mocker):
        mocker.patch("os.getloadavg", side_effect=self._mock_get_load_avg_exception)
        loadavg_facts = LoadAvgFactCollector().collect()
        assert "loadavg" not in loadavg_facts
