# Copyright: (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from hpe_test_utils import mock_ov_client, mock_ansible_module
from oneview_module_loader import OneViewModuleBase
from ansible.modules.remote_management.oneview.oneview_storage_system_facts import StorageSystemFactsModule

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


def test_should_get_all_storage_system(mock_ov_client, mock_ansible_module):
    mock_ansible_module.params = PARAMS_GET_ALL
    mock_ov_client.storage_systems.get_all = lambda: [{"name": "Storage System Name"}]

    StorageSystemFactsModule().run()

    mock_ansible_module.exit_json.assert_called_once_with(
        changed=False,
        ansible_facts=dict(storage_systems=([{"name": "Storage System Name"}]))
    )


def test_should_get_storage_system_by_name(mock_ov_client, mock_ansible_module):
    mock_ansible_module.params = PARAMS_GET_BY_NAME
    mock_ov_client.storage_systems.get_by_name = lambda x: {"name": "Storage System Name"}

    StorageSystemFactsModule().run()

    mock_ansible_module.exit_json.assert_called_once_with(
        changed=False,
        ansible_facts=dict(storage_systems=({"name": "Storage System Name"}))
    )


def test_should_get_storage_system_by_ip_hostname(mock_ov_client, mock_ansible_module):
    mock_ansible_module.params = PARAMS_GET_BY_HOSTNAME
    mock_ov_client.storage_systems.get_by_ip_hostname = lambda x: {"ip_hostname": "10.0.0.0"}

    StorageSystemFactsModule().run()

    mock_ansible_module.exit_json.assert_called_once_with(
        changed=False,
        ansible_facts=dict(storage_systems=({"ip_hostname": "10.0.0.0"}))
    )


def test_should_get_storage_system_by_hostname(mock_ov_client, mock_ansible_module):
    mock_ov_client.api_version = 500
    mock_ansible_module.params = PARAMS_GET_BY_HOSTNAME
    mock_ov_client.storage_systems.get_by_hostname = lambda x: {"hostname": "10.0.0.0"}

    StorageSystemFactsModule().run()

    mock_ansible_module.exit_json.assert_called_once_with(
        changed=False,
        ansible_facts=dict(storage_systems=({"hostname": "10.0.0.0"}))
    )


def test_should_get_all_host_types(mock_ov_client, mock_ansible_module):
    mock_ansible_module.params = PARAMS_GET_HOST_TYPES
    mock_ov_client.storage_systems.get_host_types = lambda: HOST_TYPES
    mock_ov_client.storage_systems.get_all = lambda: [{"name": "Storage System Name"}]

    StorageSystemFactsModule().run()

    mock_ansible_module.exit_json.assert_called_once_with(
        changed=False,
        ansible_facts=dict(
            storage_system_host_types=HOST_TYPES,
            storage_systems=[{"name": "Storage System Name"}])
    )


def test_should_get_reachable_ports(mock_ov_client, mock_ansible_module):
    mock_ov_client.api_version = 500
    mock_ansible_module.params = PARAMS_GET_REACHABLE_PORTS
    mock_ov_client.storage_systems.get_reachable_ports = lambda x: [{'port': 'port1'}]
    mock_ov_client.storage_systems.get_by_hostname = lambda x: {"name": "Storage System Name", "uri": "rest/123"}

    StorageSystemFactsModule().run()

    mock_ansible_module.exit_json.assert_called_once_with(
        changed=False,
        ansible_facts=dict(
            storage_system_reachable_ports=[{'port': 'port1'}],
            storage_systems={"name": "Storage System Name", "uri": "rest/123"})
    )


def test_should_get_templates(mock_ov_client, mock_ansible_module):
    mock_ov_client.api_version = 500
    mock_ansible_module.params = PARAMS_GET_TEMPLATES
    mock_ov_client.storage_systems.get_templates = lambda x: [{'template': 'temp'}]
    mock_ov_client.storage_systems.get_by_hostname = lambda x: {"name": "Storage System Name", "uri": "rest/123"}

    StorageSystemFactsModule().run()

    mock_ansible_module.exit_json.assert_called_once_with(
        changed=False,
        ansible_facts=dict(
            storage_system_templates=[{'template': 'temp'}],
            storage_systems={"name": "Storage System Name", "uri": "rest/123"})
    )


def test_should_get_storage_pools_system_by_name(mock_ov_client, mock_ansible_module):
    mock_ansible_module.params = PARAMS_GET_POOL_BY_NAME
    mock_ov_client.storage_systems.get_by_name = lambda x: {"name": "Storage System Name", "uri": "uri"}
    mock_ov_client.storage_systems.get_storage_pools = lambda x: {"name": "Storage Pool"}

    StorageSystemFactsModule().run()

    mock_ansible_module.exit_json.assert_called_once_with(
        changed=False,
        ansible_facts=dict(
            storage_system_pools=({"name": "Storage Pool"}),
            storage_systems={"name": "Storage System Name", "uri": "uri"}
        )
    )


def test_should_get_storage_system_pools_by_ip_hostname(mock_ov_client, mock_ansible_module):
    mock_ansible_module.params = PARAMS_GET_POOL_BY_IP_HOSTNAME
    mock_ov_client.storage_systems.get_by_ip_hostname = lambda x: {"ip_hostname": "10.0.0.0", "uri": "uri"}
    mock_ov_client.storage_systems.get_storage_pools = lambda x: {"name": "Storage Pool"}

    StorageSystemFactsModule().run()

    mock_ansible_module.exit_json.assert_called_once_with(
        changed=False,
        ansible_facts=dict(
            storage_system_pools=({"name": "Storage Pool"}),
            storage_systems={"ip_hostname": "10.0.0.0", "uri": "uri"}
        )
    )
