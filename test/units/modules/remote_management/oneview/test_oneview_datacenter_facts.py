# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.compat.tests import unittest
from oneview_module_loader import OneViewModuleBase
from ansible.modules.remote_management.oneview.oneview_datacenter_facts import DatacenterFactsModule
from hpe_test_utils import FactsParamsTestCase

ERROR_MSG = 'Fake message error'

PARAMS_MANDATORY_MISSING = dict(
    config='config.json',
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="MyDatacenter"
)

PARAMS_GET_ALL = dict(
    config='config.json',
)

PARAMS_GET_CONNECTED = dict(
    config='config.json',
    name="MyDatacenter",
    options=['visualContent']
)


class DatacentersFactsSpec(unittest.TestCase,
                           FactsParamsTestCase):
    def setUp(self):
        self.configure_mocks(self, DatacenterFactsModule)
        self.datacenters = self.mock_ov_client.datacenters

        FactsParamsTestCase.configure_client_mock(self, self.datacenters)

    def test_should_get_all_datacenters(self):
        self.datacenters.get_all.return_value = {"name": "Data Center Name"}

        self.mock_ansible_module.params = PARAMS_GET_ALL

        DatacenterFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(datacenters=({"name": "Data Center Name"}))
        )

    def test_should_get_datacenter_by_name(self):
        self.datacenters.get_by.return_value = [{"name": "Data Center Name"}]

        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        DatacenterFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(datacenters=([{"name": "Data Center Name"}]))
        )

    def test_should_get_datacenter_visual_content(self):
        self.datacenters.get_by.return_value = [{"name": "Data Center Name", "uri": "/rest/datacenter/id"}]

        self.datacenters.get_visual_content.return_value = {
            "name": "Visual Content"}

        self.mock_ansible_module.params = PARAMS_GET_CONNECTED

        DatacenterFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts={'datacenter_visual_content': {'name': 'Visual Content'},
                           'datacenters': [{'name': 'Data Center Name', 'uri': '/rest/datacenter/id'}]}
        )

    def test_should_get_none_datacenter_visual_content(self):
        self.datacenters.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_GET_CONNECTED

        DatacenterFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts={'datacenter_visual_content': None,
                           'datacenters': []}
        )


if __name__ == '__main__':
    unittest.main()
