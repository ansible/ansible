#!/usr/bin/env python
from __future__ import absolute_import

import os
import json
import yaml
import pytest
import tempfile
from netbox import netbox
from requests.models import Response

# Import Mock.
try:
    # Python 3.
    from unittest.mock import patch, MagicMock
except ImportError:
    # Python 2.
    from mock import patch, MagicMock

#
# Init.
###############################################################################

#
# Netbox config file.
netbox_config = '''
netbox:
    main:
        api_url: 'http://localhost/api/dcim/devices/'

    # How servers will be grouped.
    # If no group specified here, inventory script will return all servers.
    group_by:
        # Default section in Netbox.
        default:
            - device_role
            - rack
            - platform
        # Custom sections (custom_fields) could be used.
        #custom:
        #    - env

    # Use Netbox sections as host variables.
    hosts_vars:
        # Sections related to IPs e.g. "primary_ip" or "primary_ip4".
        ip:
            ansible_ssh_host: primary_ip
        # Any other sections.
        general:
            rack_name: rack
        # Custom sections (custom_fields) could be used as vars too.
        #custom:
        #    env: env
'''


# Mock config file.
def mock_config(config_data):
    config_file = tempfile.NamedTemporaryFile(delete=False, mode='a')
    config_file.write(config_data)
    config_file.close()
    return config_file

# Netbox config.
netbox_config_data = yaml.safe_load(netbox_config)

# Valid yaml file.
netbox_config_file = mock_config(netbox_config)

# Invalid yaml file.
netbox_config_file_invalid = mock_config("invalid yaml syntax: ][")


#
# Netbox api output.
netbox_api_output = json.loads('''
[
  {
    "id": 1,
    "name": "fake_host01",
    "display_name": "Fake Host",
    "device_type": {
      "id": 1,
      "manufacturer": {
        "id": 8,
        "name": "Fake Manufacturer",
        "slug": "fake_manufacturer"
      },
      "model": "all",
      "slug": "all"
    },
    "device_role": {
      "id": 8,
      "name": "Fake Server",
      "slug": "fake_server"
    },
    "tenant": null,
    "platform": null,
    "serial": "",
    "asset_tag": "fake_tag",
    "rack": {
      "id": 1,
      "name": "fake_rack01",
      "facility_id": null,
      "display_name": "Fake Rack01"
    },
    "position": null,
    "face": null,
    "parent_device": null,
    "status": true,
    "primary_ip": {
      "id": 1,
      "family": 4,
      "address": "192.168.0.2/32"
    },
    "primary_ip4": {
      "id": 1,
      "family": 4,
      "address": "192.168.0.2/32"
    },
    "primary_ip6": null,
    "comments": "",
    "custom_fields": {
      "label": "Web",
      "env": {
        "id": 1,
        "value": "Prod"
      }
    }
  },
  {
    "id": 2,
    "name": "fake_host02",
    "display_name": "fake_host02",
    "device_type": {
      "id": 1,
      "manufacturer": {
        "id": 8,
        "name": "Super Micro",
        "slug": "super-micro"
      },
      "model": "all",
      "slug": "all"
    },
    "device_role": {
      "id": 8,
      "name": "Server",
      "slug": "server"
    },
    "tenant": null,
    "platform": null,
    "serial": "",
    "asset_tag": "xtag",
    "rack": {
      "id": 1,
      "name": "fake_rack01",
      "facility_id": null,
      "display_name": "Fake Host 02"
    },
    "position": null,
    "face": null,
    "parent_device": null,
    "status": true,
    "primary_ip": null,
    "primary_ip4": null,
    "primary_ip6": null,
    "comments": "",
    "custom_fields": {
      "label": "DB",
      "env": {
        "id": 1,
        "value": "Prod"
      }
    }
  }
]
''')


# Fake Netbox API response.
def netbox_api_response(json_payload):
    response = Response()
    response.status_code = 200
    response.json = MagicMock(return_value=json_payload)
    return MagicMock(return_value=response)

# Fake single host.
fake_host = netbox_api_output[0]

# Fake API output.
netbox_api_all_hosts = netbox_api_response(netbox_api_output)
netbox_api_single_host = netbox_api_response(fake_host)


#
# Init Netbox class.
class Args(object):
    config_file = netbox_config_file.name
    host = None
    list = True

netbox_inventory = netbox.NetboxAsInventory(Args, netbox_config_data)
Args.list = False
netbox_inventory_default_args = netbox.NetboxAsInventory(Args, netbox_config_data)
Args.host = "fake_host"
netbox_inventory_single = netbox.NetboxAsInventory(Args, netbox_config_data)


#
# Tests.
###############################################################################


# Test Netbox utils functions.
class TestNetboxUtils(object):

    @pytest.mark.parametrize("source_dict, key_path", [
        ({"a_key": {"b_key": {"c_key": "c_value"}}},
         ["a_key", "b_key", "c_key"])
    ])
    def test_reduce_path(self, source_dict, key_path):
        """
        Test reduce_path function.
        """
        reduced_path = netbox.reduce_path(source_dict, key_path)
        assert reduced_path == "c_value"

    @pytest.mark.parametrize("source_dict, key_path", [
        ({"a_key": {"b_key": {"c_key": "c_value"}}},
         ["a_key", "b_key", "c_key"])
    ])
    def test_get_value_by_path_key_exists(self, source_dict, key_path):
        """
        Test get value by path with exists key.
        """
        reduced_path = netbox.get_value_by_path(source_dict, key_path)
        assert reduced_path == "c_value"

    @pytest.mark.parametrize("source_dict, key_path", [
        ({"a_key": {"b_key": {"c_key": "c_value"}}},
         ["a_key", "b_key", "any"])
    ])
    def test_get_value_by_path_key_not_exists(self, source_dict, key_path):
        """
        Test get value by path with non-exists key.
        """
        with pytest.raises(SystemExit) as key_not_exists:
            netbox.get_value_by_path(source_dict, key_path)
        assert key_not_exists

    @pytest.mark.parametrize("source_dict, key_path, ignore_key_error", [
        ({"a_key": {"b_key": {"c_key": "c_value"}}},
         ["a_key", "b_key", "any"],
         True)
    ])
    def test_get_value_by_path_key_not_exists_ignore_error(self, source_dict, key_path, ignore_key_error):
        """
        Test get value by path with exists key and not ignore error.
        """
        reduced_path = netbox.get_value_by_path(source_dict, key_path, ignore_key_error)
        assert reduced_path is None

    @pytest.mark.parametrize("yaml_file", [
        netbox_config_file.name
    ])
    def test_open_yaml_file_exists(self, yaml_file):
        """
        Test open exists yaml file.
        """
        config_output = netbox.open_yaml_file(yaml_file)
        assert config_output["netbox"]
        assert config_output["netbox"]["main"]["api_url"]

    @pytest.mark.parametrize("yaml_file", [
        "nonexists.yml"
    ])
    def test_open_yaml_file_not_exists(self, yaml_file):
        """
        Test open non-exists yaml file.
        """
        with pytest.raises(SystemExit) as file_not_exists:
            netbox.open_yaml_file(yaml_file)
        assert file_not_exists

    @pytest.mark.parametrize("yaml_file", [
        netbox_config_file_invalid.name
    ])
    def test_open_yaml_file_invalid(self, yaml_file):
        """
        Test open invalid yaml file.
        """
        with pytest.raises(SystemExit) as invalid_yaml_syntax:
            netbox.open_yaml_file(yaml_file)
        assert invalid_yaml_syntax

    @classmethod
    def teardown_class(cls):
        os.unlink(netbox_config_file.name)
        os.unlink(netbox_config_file_invalid.name)


# Test NetboxAsInventory class.
class TestNetboxAsInventory(object):

    @pytest.mark.parametrize("args, config", [
        (Args, {})
    ])
    def test_empty_config_dict(self, args, config):
        """
        Test if Netbox config file is empty.
        """
        with pytest.raises(SystemExit) as empty_config_error:
            netbox.NetboxAsInventory(args, config)
        assert empty_config_error

    @pytest.mark.parametrize("api_url", [
        netbox_inventory.api_url
    ])
    def test_get_hosts_list(self, api_url):
        """
        Test get hosts list from API and make sure it returns a list.
        """
        with patch('requests.get', netbox_api_all_hosts):
            hosts_list = netbox_inventory.get_hosts_list(api_url)
            assert isinstance(hosts_list, list)

    @pytest.mark.parametrize("api_url", [
        None
    ])
    def test_get_hosts_list_none_url_value(self, api_url):
        """
        Test if Netbox URL is invalid.
        """
        with patch('requests.get', netbox_api_all_hosts):
            with pytest.raises(SystemExit) as none_url_error:
                netbox_inventory.get_hosts_list(api_url)
            assert none_url_error

    @pytest.mark.parametrize("api_url, host_name", [
        (netbox_inventory_single.api_url, netbox_inventory_single.host)
    ])
    def test_get_hosts_list_single_host(self, api_url, host_name):
        """
        Test Netbox single host output.
        """

        with patch('requests.get', netbox_api_single_host):
            host_data = netbox_inventory_single.get_hosts_list(
                api_url,
                specific_host=host_name)
            assert host_data["name"] == "fake_host01"

    @pytest.mark.parametrize("server_name, group_value, inventory_dict", [
        ("fake_server", "fake_group", {})
    ])
    def test_add_host_to_group(self, server_name, group_value, inventory_dict):
        """
        Test add host to its group inside inventory dict.
        """
        netbox_inventory.add_host_to_group(server_name, group_value, inventory_dict)
        assert server_name in inventory_dict[group_value]

    @pytest.mark.parametrize("groups_categories, inventory_dict, host_data", [
        ({"default": ["device_role", "rack", "platform"]},
         {"_meta": {"hostvars": {}}},
         fake_host)
    ])
    def test_add_host_to_inventory(self, groups_categories, inventory_dict, host_data):
        """
        Test add host to its group in inventory dict (grouping).
        """
        netbox_inventory.add_host_to_inventory(groups_categories, inventory_dict, host_data)
        assert "hostvars" in inventory_dict["_meta"]
        assert "fake_rack01" in inventory_dict
        assert "fake_host01" in inventory_dict["fake_rack01"]

    @pytest.mark.parametrize("groups_categories, inventory_dict, host_data", [
        ({"arbitrary_category_name": []},
         {"_meta": {"hostvars": {}}},
         fake_host),
    ])
    def test_add_host_to_inventory_with_wrong_category(self, groups_categories, inventory_dict, host_data):
        """
        Test adding host to inventory with wrong category.
        """
        with pytest.raises(KeyError) as wrong_category_error:
            netbox_inventory.add_host_to_inventory(groups_categories, inventory_dict, host_data)
        assert wrong_category_error

    @pytest.mark.parametrize("groups_categories, inventory_dict, host_data", [
        ({},
         {"_meta": {"hostvars": {}}},
         fake_host),
        ({},
         {"no_group": [], "_meta": {"hostvars": {}}},
         fake_host)
    ])
    def test_add_host_to_inventory_with_no_group(self, groups_categories, inventory_dict, host_data):
        """
        Test adding host to inventory with no group.
        """
        netbox_inventory.add_host_to_inventory(groups_categories, inventory_dict, host_data)
        assert "fake_host01" in inventory_dict["no_group"]

    @pytest.mark.parametrize("groups_categories, inventory_dict, host_data", [
        ({"default": ["arbitrary_group_name"]},
         {"_meta": {"hostvars": {}}},
         fake_host),
    ])
    def test_add_host_to_inventory_with_wrong_group(self, groups_categories, inventory_dict, host_data):
        """
        Test add host to inventory with wrong group.
        """
        with pytest.raises(SystemExit) as no_group_error:
            netbox_inventory.add_host_to_inventory(groups_categories, inventory_dict, host_data)
        assert no_group_error

    @pytest.mark.parametrize("host_data, host_vars", [
        (fake_host,
         {"ip": {"ansible_ssh_host": "primary_ip"}, "general": {"rack_name": "rack"}})
    ])
    def test_get_host_vars(self, host_data, host_vars):
        """
        Test get host vars based on specific tags
        (which come from inventory script config file).
        """
        host_vars = netbox_inventory.get_host_vars(host_data, host_vars)
        assert host_vars["ansible_ssh_host"] == "192.168.0.2"
        assert host_vars["rack_name"] == "fake_rack01"

    @pytest.mark.parametrize("inventory_dict, host_name, host_vars", [
        ({"_meta": {"hostvars": {}}},
         "fake_host01",
         {"rack_name": "fake_rack01"})
    ])
    def test_update_host_meta_vars(self, inventory_dict, host_name, host_vars):
        """
        Test update host vars in inventory dict.
        """
        netbox_inventory.update_host_meta_vars(inventory_dict, host_name, host_vars)
        assert inventory_dict["_meta"]["hostvars"]["fake_host01"]["rack_name"] == "fake_rack01"

    @pytest.mark.parametrize("inventory_dict, host_name, host_vars", [
        ({"_meta": {"hostvars": {}}},
         "fake_host01",
         {"rack_name": "fake_rack01"})
    ])
    def test_update_host_meta_vars_single_host(self, inventory_dict, host_name, host_vars):
        """
        Test update host vars in inventory dict.
        """
        netbox_inventory_single.update_host_meta_vars(inventory_dict, host_name, host_vars)
        assert inventory_dict["fake_host01"]["rack_name"] == "fake_rack01"

    def test_generate_inventory(self):
        """
        Test generateing final Ansible inventory before convert it to JSON.
        """
        with patch('requests.get', netbox_api_all_hosts):
            ansible_inventory = netbox_inventory.generate_inventory()
            assert "fake_host01" in ansible_inventory["_meta"]["hostvars"]
            assert isinstance(ansible_inventory["_meta"]["hostvars"]["fake_host02"], dict)

    @pytest.mark.parametrize("inventory_dict", [
        {
            "fake_rack01": ["fake_host01", "fake_host02"],
            "Fake Server": ["fake_host01"],
            "Server": ["fake_host02"],
            "_meta": {
                "hostvars": {
                    "fake_host02": {"rack_name": "fake_rack01"},
                    "fake_host01": {"ansible_ssh_host": "192.168.0.2", "rack_name": "fake_rack01"}
                }
            }
        }
    ])
    def test_print_inventory_json(self, capsys, inventory_dict):
        """
        Test printing final Ansible inventory in JSON format.
        """
        netbox_inventory.print_inventory_json(inventory_dict)
        function_stdout, function_stderr = capsys.readouterr()
        assert not function_stderr
        assert json.loads(function_stdout) == inventory_dict

    @pytest.mark.parametrize("inventory_dict", [
        {
            "fake_host": {
                "ansible_ssh_host": "192.168.0.2",
                "rack_name": "fake_rack01"
            }
        }
    ])
    def test_print_inventory_json_single_host(self, capsys, inventory_dict):
        """
        Test printing final Ansible inventory in JSON format for single host.
        """
        netbox_inventory_single.print_inventory_json(inventory_dict)
        function_stdout, function_stderr = capsys.readouterr()
        assert not function_stderr
        assert json.loads(function_stdout) == inventory_dict["fake_host"]

    @pytest.mark.parametrize("inventory_dict", [
        {
            "fake_rack01": ["fake_host01"],
            "_meta": {
                "hostvars": {
                    "fake_host01": {"ansible_ssh_host": "192.168.0.2", "rack_name": "fake_rack01"}
                }
            }
        }
    ])
    def test_print_inventory_json_no_list_arg(self, capsys, inventory_dict):
        """
        Test printing final Ansible inventory in JSON format without --list argument.
        """
        netbox_inventory_default_args.print_inventory_json(inventory_dict)
        function_stdout, function_stderr = capsys.readouterr()
        assert not function_stderr
        assert json.loads(function_stdout) == {}
