# Copyright: (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from oneview_module_loader import OneViewModuleBase
from ansible.modules.remote_management.oneview.oneview_storage_pool_facts import StoragePoolFactsModule
from hpe_test_utils import OneViewBaseFactsTest

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Test Storage Pools"
)

PARAMS_GET_REACHABLE_STORAGE_POOLS = dict(
    config='config.json',
    name="Test Storage Pools",
    options=["reachableStoragePools"],
    params={
        'networks': ['rest/fake/network']
    }
)


@pytest.mark.resource(TestStoragePoolFactsModule='storage_pools')
class TestStoragePoolFactsModule(OneViewBaseFactsTest):
    def test_should_get_all_storage_pool(self):
        self.resource.get_all.return_value = {"name": "Storage Pool Name"}
        self.mock_ansible_module.params = PARAMS_GET_ALL

        StoragePoolFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(storage_pools=({"name": "Storage Pool Name"}))
        )

    def test_should_get_storage_pool_by_name(self):
        self.resource.get_by.return_value = {"name": "Storage Pool Name"}
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        StoragePoolFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(storage_pools=({"name": "Storage Pool Name"}))
        )

    def test_should_get_reachable_storage_pools(self):
        self.mock_ov_client.api_version = 500
        self.resource.get_by.return_value = {"name": "Storage Pool Name"}
        self.resource.get_reachable_storage_pools.return_value = [{'reachable': 'test'}]
        self.mock_ansible_module.params = PARAMS_GET_REACHABLE_STORAGE_POOLS

        StoragePoolFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(
                storage_pools_reachable_storage_pools=[{'reachable': 'test'}],
                storage_pools={"name": "Storage Pool Name"})
        )


if __name__ == '__main__':
    pytest.main([__file__])
