#!/usr/bin/env python

# (c) 2017, Ahmed AbouZaid <http://aabouzaid.com/>
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import yaml
import argparse
import requests
try:
    import json
except ImportError:
    import simplejson as json


# Script.
def cli_arguments():
    """Script cli arguments.
    By default Ansible calls "--list" as argument.
    """

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--config-file",
                        default=os.getenv("NETBOX_CONFIG_FILE", "netbox.yml"),
                        help="""Path for script's configuration. Also "NETBOX_CONFIG_FILE"
                                could be used as env var to set conf file path.""")
    parser.add_argument("--list", help="Print all hosts with vars as Ansible dynamic inventory syntax.",
                        action="store_true")
    parser.add_argument("--host", help="Print specific host vars as Ansible dynamic inventory syntax.",
                        action="store")
    arguments = parser.parse_args()
    return arguments


# Utils.
def reduce_path(source_dict, key_path):
    for key in key_path:
        if isinstance(source_dict.get(key), dict) and len(key_path) > 1:
            source_dict = source_dict.get(key)
            key_path = key_path[1:]
            reduce_path(source_dict, key_path)
        else:
            return source_dict[key]


def get_value_by_path(source_dict, key_path, ignore_key_error=False):
    """Get key value from nested dict by path.

    Args:
        source_dict: The dict that we look into.
        key_path: The path of key in dot notion. e.g. "parent_dict.child_dict.key_name"
        ignore_key_error: Ignore KeyError if the key not found in provided path.

    Returns:
        If key found in provided path, it will be returned.
        If not, None will be returned.
    """

    try:
        key_output = reduce_path(source_dict, key_path)
    except KeyError as key_name:
        if ignore_key_error:
            key_output = None
        else:
            print("The key %s is not found. Please remember, Python is case sensitive." % key_name)
            sys.exit(1)
    return key_output


def open_yaml_file(yaml_file):
    """Open YAML file.

    Args:
        yaml_file: Relative or absolute path to YAML file.

    Returns:
        Content of YAML the file.
    """

    # Load content of YAML file.
    try:
        with open(yaml_file, 'r') as config_yaml_file:
            try:
                yaml_file_content = yaml.safe_load(config_yaml_file)
            except yaml.YAMLError as yaml_error:
                print(yaml_error)
                sys.exit(1)
    except IOError as io_error:
        print("Cannot open YAML file.\n%s" % (io_error))
        sys.exit(1)
    return yaml_file_content


class NetboxAsInventory(object):
    """Netbox as a dynamic inventory for Ansible.

    Retrieves hosts list from netbox API and returns Ansible dynamic inventory (JSON).

    Attributes:
        script_config_data: Content of its config which comes from YAML file.
    """

    def __init__(self, script_args, script_config_data):
        # Script arguments.
        self.config_file = script_args.config_file
        self.list = script_args.list
        self.host = script_args.host

        # Script configuration.
        main_config_key = "netbox"
        script_config = script_config_data.get(main_config_key)
        if script_config:
            self.api_url = script_config["main"].get('api_url')
            self.group_by = script_config.setdefault("group_by", {})
            self.hosts_vars = script_config.setdefault("hosts_vars", {})
        else:
            print("The key '%s' is not found in config file." % main_config_key)
            sys.exit(1)

        # Get value based on key.
        self.key_map = {
            "default": "name",
            "general": "name",
            "custom": "value",
            "ip": "address"
        }

    @staticmethod
    def get_hosts_list(api_url, specific_host=None):
        """Retrieves hosts list from netbox API.

        Returns:
            A list of all hosts from netbox API.
        """

        if not api_url:
            print("Please check API URL in script configuration file.")
            sys.exit(1)

        if specific_host:
            data_source = "{}?name={}".format(api_url, specific_host)
        else:
            data_source = api_url

        hosts_list = requests.get(data_source).json()
        return hosts_list

    @staticmethod
    def add_host_to_group(server_name, group_value, inventory_dict):
        """Add a host to a single group.

        It checks if host in a group and adds the host to that group.
        The group will be added if it's not in the inventory.

        Args:
            server_name: String, the server that will be added to a group.
            group_value: String, name that will be used as a group in the inventory.
            inventory_dict: Dict, the inventory which will be updated.

        Returns:
            This function doesn't return, it updates the dict in place.
        """

        # The value could be None/null.
        if group_value:
            # If the group not in the inventory it will be add.
            if group_value not in inventory_dict:
                inventory_dict.update({group_value: []})

            # If the host not in the group it will be add.
            if server_name not in inventory_dict[group_value]:
                inventory_dict[group_value].append(server_name)

    def add_host_to_inventory(self, groups_categories, inventory_dict, host_data):
        """Add a host to its groups.

        It checks if host in the groups and adds the host to these groups.
        The groups are defined in this inventory script config file.

        Args:
            groups_categories: Dict, it has a categories of groups that will be
                used as Ansible inventory groups.
            inventory_dict: Dict, which is Ansible inventory.
            host_data: Dict, it has the host data that will be added to inventory.

        Returns:
            The same dict "inventory_dict" after update.
        """

        server_name = host_data.get("name")
        categories_source = {
            "default": host_data,
            "custom": host_data.get("custom_fields")
        }

        if groups_categories:
            # There are 2 categories that will be used to group hosts.
            # One for default section in netbox, and another for "custom_fields" which are being defined by netbox user.
            for category in groups_categories:
                key_name = self.key_map[category]
                data_dict = categories_source[category]

                # The groups that will be used to group hosts in the inventory.
                for group in groups_categories[category]:
                    # Try to get group value. If the section not found in netbox, this also will print error message.
                    group_value = get_value_by_path(data_dict, [group, key_name])
                    self.add_host_to_group(server_name, group_value, inventory_dict)

        # If no groups in "group_by" section, the host will go to catch-all group.
        else:
            if "no_group" not in inventory_dict:
                inventory_dict.setdefault("no_group", [server_name])
            else:
                inventory_dict["no_group"].append(server_name)
        return inventory_dict

    def get_host_vars(self, host_data, host_vars):
        """Find host vars.

        These vars will be used for host in the inventory.
        We can select whatever from netbox to be used as Ansible inventory vars.
        The vars are defined in script config file.

        Args:
            host_data: Dict, it has a host data which will be added to inventory.
            host_vars: Dict, it has selected fields to be used as host vars.

        Returns:
            A dict has all vars are associate with the host.
        """

        host_vars_dict = dict()
        if host_vars:
            categories_source = {
                "ip": host_data,
                "general": host_data,
                "custom": host_data.get("custom_fields")
            }

            # Get host vars based on selected vars. (that should come from
            # script's config file)
            for category in host_vars:
                key_name = self.key_map[category]
                data_dict = categories_source[category]

                for var_name, var_data in host_vars[category].items():
                    # This is because "custom_fields" has more than 1 type.
                    # Values inside "custom_fields" could be a key:value or a dict.
                    if isinstance(data_dict.get(var_data), dict):
                        var_value = get_value_by_path(data_dict, [var_data, key_name], ignore_key_error=True)
                    else:
                        var_value = data_dict.get(var_data)

                    if var_value:
                        # Remove CIDR from IP address.
                        if host_vars.get("ip") and var_data in host_vars["ip"].values():
                            var_value = var_value.split("/")[0]
                        # Add var to host dict.
                        host_vars_dict.update({var_name: var_value})
        return host_vars_dict

    def update_host_meta_vars(self, inventory_dict, host_name, host_vars):
        """Update host meta vars.

        Add host and its vars to "_meta.hostvars" path in the inventory.

        Args:
            inventory_dict: A dict for inventory has groups and hosts.
            host_name: Name of the host that will have vars.
            host_vars: A dict has selected fields to be used as host vars.

        Returns:
            This function doesn't return, it updates the dict in place.
        """

        if host_vars and not self.host:
            inventory_dict['_meta']['hostvars'].update({host_name: host_vars})
        elif host_vars and self.host:
            inventory_dict.update({host_name: host_vars})

    def generate_inventory(self):
        """Generate Ansible dynamic inventory.

        Returns:
            A dict has inventory with hosts and their vars.
        """

        inventory_dict = dict()
        netbox_hosts_list = self.get_hosts_list(self.api_url, self.host)
        if netbox_hosts_list:
            inventory_dict.update({"_meta": {"hostvars": {}}})
            for current_host in netbox_hosts_list:
                server_name = current_host.get("name")
                self.add_host_to_inventory(self.group_by, inventory_dict, current_host)
                host_vars = self.get_host_vars(current_host, self.hosts_vars)
                self.update_host_meta_vars(inventory_dict, server_name, host_vars)
        return inventory_dict

    def print_inventory_json(self, inventory_dict):
        """Print inventory.

        Args:
            inventory_dict: Inventory dict has groups and hosts.

        Returns:
            It prints the inventory in JSON format if condition is true.
        """

        if self.host:
            result = inventory_dict.setdefault(self.host, {})
        elif self.list:
            result = inventory_dict
        else:
            result = {}
        print(json.dumps(result))

# Main.
if __name__ == "__main__":
    # Script vars.
    args = cli_arguments()
    config_data = open_yaml_file(args.config_file)

    # Netbox vars.
    netbox = NetboxAsInventory(args, config_data)
    ansible_inventory = netbox.generate_inventory()
    netbox.print_inventory_json(ansible_inventory)
