# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.facts.system.fips import FipsFactCollector


@pytest.mark.parametrize(("return_value", "expected"), [('1', True), ('0', False)])
def test_fips(mocker, return_value, expected):
    mocker.patch('ansible.module_utils.facts.system.fips.get_file_content', return_value=return_value)
    fips_mgr = FipsFactCollector().collect()
    assert fips_mgr['fips'] is expected
