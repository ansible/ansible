# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from units.compat import unittest
from ansible.modules.remote_management.oneview.oneview_logical_interconnect_group_info import LogicalInterconnectGroupInfoModule
from hpe_test_utils import FactsParamsTestCase


ERROR_MSG = 'Fake message error'

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Test Logical Interconnect Group"
)

PRESENT_LIGS = [{
    "name": "Test Logical Interconnect Group",
    "uri": "/rest/logical-interconnect-groups/ebb4ada8-08df-400e-8fac-9ff987ac5140"
}]


class LogicalInterconnectGroupInfoSpec(unittest.TestCase, FactsParamsTestCase):
    def setUp(self):
        self.configure_mocks(self, LogicalInterconnectGroupInfoModule)
        self.logical_interconnect_groups = self.mock_ov_client.logical_interconnect_groups
        FactsParamsTestCase.configure_client_mock(self, self.logical_interconnect_groups)

    def test_should_get_all_ligs(self):
        self.logical_interconnect_groups.get_all.return_value = PRESENT_LIGS
        self.mock_ansible_module.params = PARAMS_GET_ALL

        LogicalInterconnectGroupInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            logical_interconnect_groups=(PRESENT_LIGS)
        )

    def test_should_get_lig_by_name(self):
        self.logical_interconnect_groups.get_by.return_value = PRESENT_LIGS
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        LogicalInterconnectGroupInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            logical_interconnect_groups=(PRESENT_LIGS)
        )


if __name__ == '__main__':
    unittest.main()
