#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 1.2
# Copyright (C) 2019 Dell Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# All rights reserved. Dell, EMC, and other trademarks are trademarks of Dell Inc. or its subsidiaries.
# Other trademarks may be trademarks of their respective owners.
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ome_device_info
short_description: Retrieves the information about Device.
version_added: "2.9"
description:
   - This module retrieves the list of all devices information with the exhaustive inventory of each
     device.
options:
    hostname:
        description:
            - Target IP Address or hostname.
        type: str
        required: True
    username:
        description:
            - Target username.
        type: str
        required: True
    password:
        description:
            - Target user password.
        type: str
        required: True
    port:
        description:
            - Target HTTPS port.
        type: int
        default: 443
    fact_subset:
        description:
            - C(basic_inventory) returns the list of the devices.
            - C(detailed_inventory) returns the inventory details of specified devices.
            - C(subsystem_health) returns the health status of specified devices.
        type: str
        choices: [basic_inventory, detailed_inventory, subsystem_health ]
        default: basic_inventory
    system_query_options:
        description:
            - I(system_query_options) applicable for the choices of the fact_subset. Either I(device_id) or I(device_service_tag)
              is mandatory for C(detailed_inventory) and C(subsystem_health) or both can be applicable.
        type: dict
        suboptions:
            device_id:
                 description:
                    - A list of unique identifier is applicable
                      for C(detailed_inventory) and C(subsystem_health).
                 type: list
            device_service_tag:
                 description:
                    - A list of service tags are applicable for C(detailed_inventory)
                      and C(subsystem_health).
                 type: list
            inventory_type:
                description:
                    - For C(detailed_inventory), it returns details of the specified inventory type.
                type: str
            filter:
                description:
                    - For C(basic_inventory), it filters the collection of devices.
                      I(filter) query format should be aligned with OData standards.
                type: str

requirements:
    - "python >= 2.7.5"
author: "Sajna Shetty(@Sajna-Shetty)"
'''

EXAMPLES = """
---
- name: Retrieve basic inventory of all devices.
  ome_device_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"

- name: Retrieve basic inventory for devices identified by IDs 33333 or 11111 using filtering.
  ome_device_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    fact_subset: "basic_inventory"
    system_query_options:
      filter: "Id eq 33333 or Id eq 11111"

- name: Retrieve inventory details of specified devices identified by IDs 11111 and 22222.
  ome_device_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    fact_subset: "detailed_inventory"
    system_query_options:
      device_id:
        - 11111
        - 22222

- name: Retrieve inventory details of specified devices identified by service tags MXL1234 and MXL4567.
  ome_device_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    fact_subset: "detailed_inventory"
    system_query_options:
      device_service_tag:
        - MXL1234
        - MXL4567

- name: Retrieve details of specified inventory type of specified devices identified by ID and service tags.
  ome_device_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    fact_subset: "detailed_inventory"
    system_query_options:
      device_id:
        - 11111
      device_service_tag:
        - MXL1234
        - MXL4567
      inventory_type: "serverDeviceCards"

- name: Retrieve subsystem health of specified devices identified by service tags.
  ome_device_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    fact_subset: "subsystem_health"
    system_query_options:
      device_service_tag:
        - MXL1234
        - MXL4567

"""

RETURN = '''
---
msg:
  type: str
  description: Over all device information status.
  returned: on error
  sample: "Failed to fetch the device information"
device_info:
  type: dict
  description: Returns the information collected from the Device.
  returned: success
  sample: {
  "value": [
        {
            "Actions": null,
            "AssetTag": null,
            "ChassisServiceTag": null,
            "ConnectionState": true,
            "DeviceManagement": [
                {
                    "DnsName": "dnsname.host.com",
                    "InstrumentationName": "MX-12345",
                    "MacAddress": "11:10:11:10:11:10",
                    "ManagementId": 12345,
                    "ManagementProfile": [
                        {
                            "HasCreds": 0,
                            "ManagementId": 12345,
                            "ManagementProfileId": 12345,
                            "ManagementURL": "https://192.168.0.1:443",
                            "Status": 1000,
                            "StatusDateTime": "2019-01-21 06:30:08.501"
                        }
                    ],
                    "ManagementType": 2,
                    "NetworkAddress": "192.168.0.1"
                }
            ],
            "DeviceName": "MX-0003I",
            "DeviceServiceTag": "MXL1234",
            "DeviceSubscription": null,
            "LastInventoryTime": "2019-01-21 06:30:08.501",
            "LastStatusTime": "2019-01-21 06:30:02.492",
            "ManagedState": 3000,
            "Model": "PowerEdge MX7000",
            "PowerState": 17,
            "SlotConfiguration": {},
            "Status": 4000,
            "SystemId": 2031,
            "Type": 2000
        }
    ]
  }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.dellemc.ome import RestOME
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.urls import ConnectionError, SSLValidationError

DEVICES_INVENTORY_DETAILS = "detailed_inventory"
DEVICES_SUBSYSTEM_HEALTH = "subsystem_health"
DEVICES_INVENTORY_TYPE = "inventory_type"
DEVICE_LIST = "basic_inventory"
DESC_HTTP_ERROR = "HTTP Error 404: Not Found"
device_fact_error_report = {}

DEVICE_RESOURCE_COLLECTION = {
    DEVICE_LIST: {"resource": "DeviceService/Devices"},
    DEVICES_INVENTORY_DETAILS: {"resource": "DeviceService/Devices({Id})/InventoryDetails"},
    DEVICES_INVENTORY_TYPE: {"resource": "DeviceService/Devices({Id})/InventoryDetails('{InventoryType}')"},
    DEVICES_SUBSYSTEM_HEALTH: {"resource": "DeviceService/Devices({Id})/SubSystemHealth"},
}


def _get_device_id_from_service_tags(service_tags, rest_obj):
    """
    Get device ids from device service tag
    Returns :dict : device_id to service_tag map
    :arg service_tags: service tag
    :arg rest_obj: RestOME class object in case of request with session.
    :returns: dict eg: {1345:"MXL1245"}
    """
    try:
        path = DEVICE_RESOURCE_COLLECTION[DEVICE_LIST]["resource"]
        resp = rest_obj.invoke_request('GET', path)
        if resp.success:
            devices_list = resp.json_data["value"]
            service_tag_dict = {}
            for item in devices_list:
                if item["DeviceServiceTag"] in service_tags:
                    service_tag_dict.update({item["Id"]: item["DeviceServiceTag"]})
            available_service_tags = service_tag_dict.values()
            not_available_service_tag = list(set(service_tags) - set(available_service_tags))
            device_fact_error_report.update(dict((tag, DESC_HTTP_ERROR) for tag in not_available_service_tag))
        else:
            raise ValueError(resp.json_data)
    except (URLError, HTTPError, SSLValidationError, ConnectionError, TypeError, ValueError) as err:
        raise err
    return service_tag_dict


def is_int(val):
    """check when device_id numeric represented value is int"""
    try:
        int(val)
        return True
    except ValueError:
        return False


def _check_duplicate_device_id(device_id_list, service_tag_dict):
    """If service_tag is duplicate of device_id, then updates the message as Duplicate report
    :arg1: device_id_list : list of device_id
    :arg2: service_tag_id_dict: dictionary of device_id to service tag map"""
    if device_id_list:
        device_id_represents_int = [int(device_id) for device_id in device_id_list if device_id and is_int(device_id)]
        common_val = list(set(device_id_represents_int) & set(service_tag_dict.keys()))
        for device_id in common_val:
            device_fact_error_report.update(
                {service_tag_dict[device_id]: "Duplicate report of device_id: {0}".format(device_id)})
            del service_tag_dict[device_id]


def _get_device_identifier_map(module_params, rest_obj):
    """
    Builds the identifiers mapping
    :returns: the dict of device_id to server_tag map
     eg: {"device_id":{1234: None},"device_service_tag":{1345:"MXL1234"}}"""
    system_query_options_param = module_params.get("system_query_options")
    device_id_service_tag_dict = {}
    if system_query_options_param is not None:
        device_id_list = system_query_options_param.get("device_id")
        device_service_tag_list = system_query_options_param.get("device_service_tag")
        if device_id_list:
            device_id_dict = dict((device_id, None) for device_id in list(set(device_id_list)))
            device_id_service_tag_dict["device_id"] = device_id_dict
        if device_service_tag_list:
            service_tag_dict = _get_device_id_from_service_tags(device_service_tag_list,
                                                                rest_obj)

            _check_duplicate_device_id(device_id_list, service_tag_dict)
            device_id_service_tag_dict["device_service_tag"] = service_tag_dict
    return device_id_service_tag_dict


def _get_query_parameters(module_params):
    """
    Builds query parameter
    :returns: dictionary, which is applicable builds the query format
     eg : {"$filter":"Type eq 2000"}
     """
    system_query_options_param = module_params.get("system_query_options")
    query_parameter = None
    if system_query_options_param:
        filter_by_val = system_query_options_param.get("filter")
        if filter_by_val:
            query_parameter = {"$filter": filter_by_val}
    return query_parameter


def _get_resource_parameters(module_params, rest_obj):
    """
    Identifies the resource path by different states
    :returns: dictionary containing identifier with respective resource path
        eg:{"device_id":{1234:""DeviceService/Devices(1234)/InventoryDetails"},
        "device_service_tag":{"MXL1234":"DeviceService/Devices(1345)/InventoryDetails"}}
    """
    fact_subset = module_params["fact_subset"]
    path_dict = {}
    if fact_subset != DEVICE_LIST:
        inventory_type = None
        device_id_service_tag_dict = _get_device_identifier_map(module_params, rest_obj)
        if fact_subset == DEVICES_INVENTORY_DETAILS:
            system_query_options = module_params.get("system_query_options")
            inventory_type = system_query_options.get(DEVICES_INVENTORY_TYPE)
        path_identifier = DEVICES_INVENTORY_TYPE if inventory_type else fact_subset
        for identifier_type, identifier_dict in device_id_service_tag_dict.items():
            path_dict[identifier_type] = {}
            for device_id, service_tag in identifier_dict.items():
                key_identifier = service_tag if identifier_type == "device_service_tag" else device_id
                path = DEVICE_RESOURCE_COLLECTION[path_identifier]["resource"].format(Id=device_id,
                                                                                      InventoryType=inventory_type)
                path_dict[identifier_type].update({key_identifier: path})
    else:
        path_dict.update({DEVICE_LIST: DEVICE_RESOURCE_COLLECTION[DEVICE_LIST]["resource"]})
    return path_dict


def _check_mutually_inclusive_arguments(val, module_params, required_args):
    """"
     Throws error if arguments detailed_inventory, subsystem_health
     not exists with qualifier device_id or device_service_tag"""
    system_query_options_param = module_params.get("system_query_options")
    if system_query_options_param is None or (system_query_options_param is not None and not any(
            system_query_options_param.get(qualifier) for qualifier in required_args)):
        raise ValueError("One of the following {0} is required for {1}".format(required_args, val))


def _validate_inputs(module_params):
    """validates input parameters"""
    fact_subset = module_params["fact_subset"]
    if fact_subset != "basic_inventory":
        _check_mutually_inclusive_arguments(fact_subset, module_params, ["device_id", "device_service_tag"])


def main():
    system_query_options = {"type": 'dict', "required": False, "options": {
        "device_id": {"type": 'list'},
        "device_service_tag": {"type": 'list'},
        "inventory_type": {"type": 'str'},
        "filter": {"type": 'str', "required": False},
    }}

    module = AnsibleModule(
        argument_spec={
            "hostname": {"required": True, "type": 'str'},
            "username": {"required": True, "type": 'str'},
            "password": {"required": True, "type": 'str', "no_log": True},
            "port": {"required": False, "default": 443, "type": 'int'},
            "fact_subset": {"required": False, "default": "basic_inventory",
                            "choices": ['basic_inventory', 'detailed_inventory', 'subsystem_health']},
            "system_query_options": system_query_options,
        },
        required_if=[['fact_subset', 'detailed_inventory', ['system_query_options']],
                     ['fact_subset', 'subsystem_health', ['system_query_options']], ],
        supports_check_mode=False)

    try:
        _validate_inputs(module.params)
        with RestOME(module.params, req_session=True) as rest_obj:
            device_facts = _get_resource_parameters(module.params, rest_obj)
            resp_status = []
            if device_facts.get("basic_inventory"):
                query_param = _get_query_parameters(module.params)
                resp = rest_obj.invoke_request('GET', device_facts["basic_inventory"], query_param=query_param)
                device_facts = resp.json_data
                resp_status.append(resp.status_code)
            else:
                for identifier_type, path_dict_map in device_facts.items():
                    for identifier, path in path_dict_map.items():
                        try:
                            resp = rest_obj.invoke_request('GET', path)
                            data = resp.json_data
                            resp_status.append(resp.status_code)
                        except HTTPError as err:
                            data = str(err)
                        path_dict_map[identifier] = data
                if any(device_fact_error_report):
                    if "device_service_tag" in device_facts:
                        device_facts["device_service_tag"].update(device_fact_error_report)
                    else:
                        device_facts["device_service_tag"] = device_fact_error_report
        if 200 in resp_status:
            module.exit_json(device_info=device_facts)
        else:
            module.fail_json(msg="Failed to fetch the device information")
    except (URLError, HTTPError, SSLValidationError, ConnectionError, TypeError, ValueError) as err:
        module.fail_json(msg=str(err))


if __name__ == '__main__':
    main()
