# -*- coding: utf-8 -*-
# Copyright (c) 2019 Syed Junaid Ali <mailtojunaid@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
import datetime

from ansible.plugins.inventory.active_directory import InventoryModule
from ansible.errors import AnsibleError
from ldap3 import (
    Server,
    Connection,
    ALL,
    MOCK_SYNC,
    ObjectDef,
    AttrDef,
    OFFLINE_AD_2012_R2,
)
import os

config_data = {
    "plugin": "active_directory",
    "username": "ad_admin",
    "password": "sup3rs3cr3t",
    "domain_controllers": ["dc1.ansible.local", "dc1.ansible.local"],
    "organizational_units": [
        "OU=Servers,DC=ansible,DC=local",
        "OU=Desktops,DC=ansible,DC=local",
    ],
    "last_activity": 30,
}


@pytest.fixture(scope="module")
def inventory():
    inventory = InventoryModule()
    inventory._config_data = config_data
    return inventory


@pytest.fixture(scope="module")
def connection():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    server = Server.from_definition(
        "my_fake_server",
        os.path.join(current_dir, "fixtures", "test_active_directory_server_info.json"),
        os.path.join(
            current_dir, "fixtures", "test_active_directory_server_schema.json"
        ),
    )
    connection = Connection(
        server,
        user="cn=admin,ou=users,ou=ansible,o=local",
        password="s3cr3t",
        client_strategy=MOCK_SYNC,
    )
    connection.strategy.entries_from_json(
        os.path.join(current_dir, "fixtures", "test_active_directory_server_data.json")
    )
    connection.bind()
    return connection


@pytest.fixture(scope="module")
def domain_controller_computer_object(connection):
    connection.search(
        search_base="OU=Domain Controllers,DC=ansible,DC=local",
        search_filter="(objectclass=computer)",
        attributes=["lastLogonTimestamp", "operatingSystem", "DNSHostName", "name"],
    )
    return connection.entries[0]


def test_read_config_data(inventory):
    inventory._options = {
        "username": "ANSIBLETEST\\Administrator",
        "password": "sup3rs3cr3t!",
        "domain_controllers": ["dc1.ansible.local", "dc1.ansible.local"],
    }
    inventory._init_data()
    assert inventory.user_name == "ANSIBLETEST\\Administrator"
    assert inventory.user_password == "sup3rs3cr3t!"
    assert inventory.domain_controllers == ["dc1.ansible.local", "dc1.ansible.local"]


def test_insufficient_credentials(inventory):
    inventory._options = {
        "username": "ANSIBLETEST\\Administrator",
        "domain_controllers": ["dc1.ansible.local", "dc1.ansible.local"],
    }
    with pytest.raises(AnsibleError) as error_message:
        inventory._init_data()
        assert "insufficient credentials found" in error_message


def test_missing_domain_controllers_list(inventory):
    inventory._options = {
        "username": "ANSIBLETEST\\Administrator",
        "password": "sup3rs3cr3t!",
    }
    with pytest.raises(AnsibleError) as error_message:
        inventory._init_data()
        assert "domain controllers list is empty" in error_message


def test_loading_computer_objects_from_domain_controllers_organizational_unit(
    domain_controller_computer_object,
):
    assert (
        domain_controller_computer_object.entry_dn
        == "CN=DC,OU=Domain Controllers,DC=ansible,DC=local"
    )
    assert isinstance(
        domain_controller_computer_object.lastLogonTimestamp.value, datetime.datetime
    )
    assert (
        domain_controller_computer_object.operatingSystem
        == "Windows Server 2016 Standard Evaluation"
    )
    assert domain_controller_computer_object.DNSHostName == "dc.ansible.local"
    assert domain_controller_computer_object.name == "DC"


def test_computer_object_inventory_hostname_should_default_to_dns_hostname_attribute(
    inventory, connection
):
    dc_entries = inventory._query(
        connection, "OU=Domain Controllers,DC=ansible,DC=local"
    )
    all_dcs = []
    for entry in dc_entries:
        all_dcs.append(entry)
        assert inventory._get_hostname(entry, hostnames=None) == "dc.ansible.local"


def test_computer_object_inventory_hostname_using_name_attribute(inventory, connection):
    dc_entries = inventory._query(
        connection, "OU=Domain Controllers,DC=ansible,DC=local"
    )
    all_dcs = []
    for entry in dc_entries:
        all_dcs.append(entry)
        assert inventory._get_hostname(entry, hostnames=["name"]) == "dc"


def test_query_domain_controllers_organizational_unit(inventory, connection):
    dc_entries = inventory._query(
        connection, "OU=Domain Controllers,DC=ansible,DC=local"
    )
    all_dcs = []
    for entry in dc_entries:
        all_dcs.append(entry)
    assert len(all_dcs) == 1


def test_query_invalid_path_should_raise_error(inventory, connection):

    try:
        inventory._query(connection=connection, path="UNKNOWN-PATH")
    except AnsibleError as err:
        assert "could not retrieve computer objects" in err


def test_loading_computer_objects_using_simple_organizational_unit(
    inventory, connection
):
    entries = inventory._query(
        connection, "OU=servers-ou-1,OU=Servers,OU=Devices,DC=ansible,DC=local"
    )
    all_computers = []
    for entry in entries:
        all_computers.append(entry)
    assert len(all_computers) == 5


def test_loading_computer_objects_using_nested_organizational_unit(
    inventory, connection
):
    entries = inventory._query(connection, "OU=Servers,OU=Devices,DC=ansible,DC=local")
    all_computers = []
    for entry in entries:
        all_computers.append(entry)
    assert len(all_computers) == 25


def test_get_safe_group_name_with_dashes(inventory):
    group_name = "server-ou-1"
    assert inventory._get_safe_group_name(group_name) == "server_ou_1"


def test_get_safe_group_name_with_spaces(inventory):
    group_name = "server-ou 1"
    assert inventory._get_safe_group_name(group_name) == "server_ou_1"


def test_get_safe_group_name_with_upper_case(inventory):
    group_name = "Server-ou-1"
    assert inventory._get_safe_group_name(group_name) == "server_ou_1"


def test_get_inventory_group_names_from_computer_distinguished_name_fails_for_invalid_input(
    inventory,
):
    entry_dn = "CN=server-001,OU=servers-ou-1,OU=Servers,OU=Devices,DC=ansible,DC=local"
    search_base_ou = "OU=servers-ou-1,OU=Servers,OU=Devices,DC=ansible,DC=locals"
    with pytest.raises(AnsibleError) as error_message:
        inventory._get_inventory_group_names_from_computer_distinguished_name(
            entry_dn, search_base_ou
        )
        assert "could not retrieve computer objects" in error_message


def test_get_inventory_group_names_from_computer_distinguished_name_no_nesting(
    inventory,
):
    entry_dn = "CN=server-001,OU=servers-ou-1,OU=Servers,OU=Devices,DC=ansible,DC=local"
    search_base_ou = "OU=servers-ou-1,OU=Servers,OU=Devices,DC=ansible,DC=local"
    groups = inventory._get_inventory_group_names_from_computer_distinguished_name(
        entry_dn, search_base_ou
    )
    assert len(groups) == 1
    assert groups[0] == "servers-ou-1"


def test_get_inventory_group_names_from_computer_distinguished_name_with_nesting(
    inventory,
):
    entry_dn = "CN=server-001,OU=servers-ou-1,OU=Servers,OU=Devices,DC=ansible,DC=local"
    search_base_ou = "OU=Servers,OU=Devices,DC=ansible,DC=local"
    groups = inventory._get_inventory_group_names_from_computer_distinguished_name(
        entry_dn, search_base_ou
    )
    assert len(groups) == 2
    assert groups[0] == "Servers"
    assert groups[1] == "servers-ou-1"


def test_get_inventory_group_names_from_computer_distinguished_name_for_domain_root(
    inventory,
):
    entry_dn = "CN=server-001,OU=servers-ou-1,OU=Servers,OU=Devices,DC=ansible,DC=local"
    search_base_ou = "DC=ansible,DC=local"
    groups = inventory._get_inventory_group_names_from_computer_distinguished_name(
        entry_dn, search_base_ou
    )
    assert len(groups) == 3
    assert groups[0] == "Devices"
    assert groups[1] == "Servers"
    assert groups[2] == "servers-ou-1"


def test_get_inventory_group_names_from_computer_security_groups_empty_group(inventory):
    security_groups = []
    assert (
        len(
            inventory._get_inventory_group_names_from_computer_security_groups(
                security_groups
            )
        )
        == 0
    )


def test_get_inventory_group_names_from_computer_security_groups_one_group(inventory):
    security_groups = [
        "CN=Pre-Windows 2000 Compatible Access,CN=Builtin,DC=ansible,DC=local"
    ]
    inventory_groups = inventory._get_inventory_group_names_from_computer_security_groups(
        security_groups
    )
    assert len(inventory_groups) == 1
    assert inventory_groups[0] == "Pre-Windows 2000 Compatible Access"


def test_get_inventory_group_names_from_computer_security_groups_multiple_group(
    inventory,
):
    security_groups = [
        "CN=Pre-Windows 2000 Compatible Access,CN=Builtin,DC=ansible,DC=local",
        "CN=Cert Publishers,CN=Users,DC=ansible,DC=local",
    ]
    inventory_groups = inventory._get_inventory_group_names_from_computer_security_groups(
        security_groups
    )
    assert len(inventory_groups) == 2
    assert inventory_groups[0] == "Pre-Windows 2000 Compatible Access"
    assert inventory_groups[1] == "Cert Publishers"
