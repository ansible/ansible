#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import re
import tacp
from tacp.rest import ApiException
from uuid import UUID, uuid4


def get_component_fields_by_name(name, component,
                                 api_client, fields=['name', 'uuid']):
    """
    Returns the UUID of a named component if it exists in a given
    ThinkAgile CP cloud, otherwise return None.

    :param name The name of the component that may or may not exist yet
    :type name str
    :param component The type of component in question, must be one of
    """

    valid_components = ["storage_pool", "application",
                        "template", "datacenter", "migration_zone",
                        "vnet", "vlan"]

    if component not in valid_components:
        return "Invalid component"
    if component == "storage_pool":
        api_instance = tacp.FlashPoolsApi(api_client)
        try:
            # View flash pools for an organization
            api_response = api_instance.get_flash_pools_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_flash_pools_using_get: %s\n" % e
    elif component == "application":
        api_instance = tacp.ApplicationsApi(api_client)
        try:
            # View applications for an organization
            api_response = api_instance.get_applications_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_applications_using_get: %s\n" % e
    elif component == "template":
        api_instance = tacp.TemplatesApi(api_client)
        try:
            # View templates for an organization
            api_response = api_instance.get_templates_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_templates_using_get: %s\n" % e
    elif component == "datacenter":
        api_instance = tacp.DatacentersApi(api_client)
        try:
            # View datacenters for an organization
            api_response = api_instance.get_datacenters_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_datacenters_using_get: %s\n" % e
    elif component == "migration_zone":
        api_instance = tacp.MigrationZonesApi(api_client)
        try:
            # View migration zones for an organization
            api_response = api_instance.get_migration_zones_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_migration_zones_using_get: %s\n" % e
    elif component == "vlan":
        api_instance = tacp.VlansApi(api_client)
        try:
            # View VLAN networks for an organization
            api_response = api_instance.get_vlans_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_vlans_using_get: %s\n" % e
    elif component == "vnet":
        api_instance = tacp.VnetsApi(api_client)
        try:
            # View VNET networks for an organization
            api_response = api_instance.get_vnets_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_vnets_using_get: %s\n" % e

    if (api_response):
        if fields == ['name', 'uuid']:
            for result in api_response:
                if result.name == name:
                    return result.uuid
        if 'bootOrder' in fields:
            for result in api_response:
                if result.name == name:
                    boot_order = []
                    for order_item in result.boot_order:
                        str_dict = str(order_item).replace(
                            "\n", "").replace("'", '"').replace("None", '""')

                        json_dict = json.loads(str_dict)

                        disk_uuid = json_dict['disk_uuid'] if json_dict['disk_uuid'] else None
                        name = json_dict['name'] if json_dict['name'] else None
                        order = json_dict['order'] if json_dict['order'] else None
                        vnic_uuid = json_dict['vnic_uuid'] if json_dict['vnic_uuid'] else None

                        boot_order_payload = tacp.ApiBootOrderPayload(disk_uuid=disk_uuid,
                                                                      name=name,
                                                                      order=order,
                                                                      vnic_uuid=vnic_uuid)
                        boot_order.append(boot_order_payload)
                    return boot_order
    return None
    

def convert_memory_abbreviation_to_bytes(value):
    """Validate memory argument. Returns the memory value in bytes."""
    MEMORY_RE = re.compile(
        r"^(?P<amount>[0-9]+)(?P<unit>t|tb|g|gb|m|mb|k|kb)?$")

    matches = MEMORY_RE.match(value.lower())
    if matches is None:
        raise ValueError(
            '%s is not a valid value for memory amount' % value)
    amount_str, unit = matches.groups()
    amount = int(amount_str)
    amount_in_bytes = amount
    if unit is None:
        amount_in_bytes = amount
    elif unit in ['k', 'kb', 'K', 'KB']:
        amount_in_bytes = amount * 1024
    elif unit in ['m', 'mb', 'M', 'MB']:
        amount_in_bytes = amount * 1024 * 1024
    elif unit in ['g', 'gb', 'G', 'GB']:
        amount_in_bytes = amount * 1024 * 1024 * 1024
    elif unit in ['t', 'tb', 'T', 'TB']:
        amount_in_bytes = amount * 1024 * 1024 * 1024 * 1024

    return amount_in_bytes


def is_valid_uuid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

    Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test
