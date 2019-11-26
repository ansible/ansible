# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible.modules.remote_management.oneview.oneview_datacenter_info import DatacenterInfoModule
from hpe_test_utils import FactsParamsTest

PARAMS_GET_CONNECTED = dict(
    config='config.json',
    name="MyDatacenter",
    options=['visualContent']
)


class TestDatacenterInfoModule(FactsParamsTest):
    @pytest.fixture(autouse=True)
    def setUp(self, mock_ansible_module, mock_ov_client):
        self.resource = mock_ov_client.datacenters
        self.mock_ansible_module = mock_ansible_module
        self.mock_ov_client = mock_ov_client

    def test_should_get_all_datacenters(self):
        self.resource.get_all.return_value = {"name": "Data Center Name"}

        self.mock_ansible_module.params = dict(config='config.json',)

        DatacenterInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            datacenters=({"name": "Data Center Name"})
        )

    def test_should_get_datacenter_by_name(self):
        self.resource.get_by.return_value = [{"name": "Data Center Name"}]

        self.mock_ansible_module.params = dict(config='config.json', name="MyDatacenter")

        DatacenterInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            datacenters=([{"name": "Data Center Name"}])
        )

    def test_should_get_datacenter_visual_content(self):
        self.resource.get_by.return_value = [{"name": "Data Center Name", "uri": "/rest/datacenter/id"}]

        self.resource.get_visual_content.return_value = {
            "name": "Visual Content"}

        self.mock_ansible_module.params = PARAMS_GET_CONNECTED

        DatacenterInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            datacenter_visual_content={'name': 'Visual Content'},
            datacenters=[{'name': 'Data Center Name', 'uri': '/rest/datacenter/id'}]
        )

    def test_should_get_none_datacenter_visual_content(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_GET_CONNECTED

        DatacenterInfoModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            datacenter_visual_content=None,
            datacenters=[]
        )
