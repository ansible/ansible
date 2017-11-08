# Copyright: (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.compat.tests import unittest
from oneview_module_loader import OneViewModuleBase
from ansible.modules.remote_management.oneview.oneview_storage_system_facts import StorageSystemFactsModule
from hpe_test_utils import FactsParamsTestCase

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Test Storage Systems"
)

PARAMS_GET_BY_HOSTNAME = dict(
    config='config.json',
    storage_hostname='10.0.0.0'
)

PARAMS_GET_HOST_TYPES = dict(
    config='config.json',
    options=["hostTypes"]
)

PARAMS_GET_REACHABLE_PORTS = dict(
    config='config.json',
    storage_hostname='10.0.0.0',
    options=["reachablePorts"]
)

PARAMS_GET_TEMPLATES = dict(
    config='config.json',
    storage_hostname='10.0.0.0',
    options=["templates"]
)

HOST_TYPES = [
    "Citrix Xen Server 5.x/6.x",
    "IBM VIO Server",
]

PARAMS_GET_POOL_BY_NAME = dict(
    config='config.json',
    name="Test Storage Systems",
    options=["storagePools"]
)

PARAMS_GET_POOL_BY_IP_HOSTNAME = dict(
    config='config.json',
    storage_hostname='10.0.0.0',
    options=["storagePools"]
)


class StorageSystemFactsSpec(unittest.TestCase,
                             FactsParamsTestCase):
    def setUp(self):
        self.configure_mocks(self, StorageSystemFactsModule)
        self.storage_systems = self.mock_ov_client.storage_systems
        self.mock_ov_client.api_version = 300
        FactsParamsTestCase.configure_client_mock(self, self.storage_systems)

    def test_should_get_all_storage_system(self):
        self.storage_systems.get_all.return_value = {"name": "Storage System Name"}
        self.mock_ansible_module.params = PARAMS_GET_ALL

        StorageSystemFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(storage_systems=({"name": "Storage System Name"}))
        )

    def test_should_get_storage_system_by_name(self):
        self.storage_systems.get_by_name.return_value = {"name": "Storage System Name"}
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        StorageSystemFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(storage_systems=({"name": "Storage System Name"}))
        )

    def test_should_get_storage_system_by_ip_hostname(self):
        self.storage_systems.get_by_ip_hostname.return_value = {"ip_hostname": "10.0.0.0"}
        self.mock_ansible_module.params = PARAMS_GET_BY_HOSTNAME

        StorageSystemFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(storage_systems=({"ip_hostname": "10.0.0.0"}))
        )

    def test_should_get_storage_system_by_hostname(self):
        self.mock_ov_client.api_version = 500
        self.storage_systems.get_by_hostname.return_value = {"hostname": "10.0.0.0"}
        self.mock_ansible_module.params = PARAMS_GET_BY_HOSTNAME

        StorageSystemFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(storage_systems=({"hostname": "10.0.0.0"}))
        )

    def test_should_get_all_host_types(self):
        self.storage_systems.get_host_types.return_value = HOST_TYPES
        self.storage_systems.get_all.return_value = [{"name": "Storage System Name"}]
        self.mock_ansible_module.params = PARAMS_GET_HOST_TYPES

        StorageSystemFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(
                storage_system_host_types=HOST_TYPES,
                storage_systems=[{"name": "Storage System Name"}])
        )

    def test_should_get_reachable_ports(self):
        self.mock_ov_client.api_version = 500
        self.storage_systems.get_reachable_ports.return_value = [{'port': 'port1'}]
        self.storage_systems.get_by_hostname.return_value = {"name": "Storage System Name", "uri": "rest/123"}
        self.mock_ansible_module.params = PARAMS_GET_REACHABLE_PORTS

        StorageSystemFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(
                storage_system_reachable_ports=[{'port': 'port1'}],
                storage_systems={"name": "Storage System Name", "uri": "rest/123"})
        )

    def test_should_get_templates(self):
        self.mock_ov_client.api_version = 500
        self.storage_systems.get_templates.return_value = [{'template': 'temp'}]
        self.storage_systems.get_by_hostname.return_value = {"name": "Storage System Name", "uri": "rest/123"}
        self.mock_ansible_module.params = PARAMS_GET_TEMPLATES

        StorageSystemFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(
                storage_system_templates=[{'template': 'temp'}],
                storage_systems={"name": "Storage System Name", "uri": "rest/123"})
        )

    def test_should_get_storage_pools_system_by_name(self):
        self.storage_systems.get_by_name.return_value = {"name": "Storage System Name", "uri": "uri"}
        self.storage_systems.get_storage_pools.return_value = {"name": "Storage Pool"}
        self.mock_ansible_module.params = PARAMS_GET_POOL_BY_NAME

        StorageSystemFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(
                storage_system_pools=({"name": "Storage Pool"}),
                storage_systems={"name": "Storage System Name", "uri": "uri"}
            )
        )

    def test_should_get_storage_system_pools_by_ip_hostname(self):
        self.storage_systems.get_by_ip_hostname.return_value = {"ip_hostname": "10.0.0.0", "uri": "uri"}
        self.storage_systems.get_storage_pools.return_value = {"name": "Storage Pool"}
        self.mock_ansible_module.params = PARAMS_GET_POOL_BY_IP_HOSTNAME

        StorageSystemFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(
                storage_system_pools=({"name": "Storage Pool"}),
                storage_systems={"ip_hostname": "10.0.0.0", "uri": "uri"}
            )
        )


if __name__ == '__main__':
    unittest.main()
