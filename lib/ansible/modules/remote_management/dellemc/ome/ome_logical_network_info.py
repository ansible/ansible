#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.1
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
module: ome_logical_network_info
short_description: Retrieves the information about logical networks present in device.
version_added: "2.9"
description:
   - This module retrieves the list of all logical networks with their detailed information.
   - This module retrieves specific logical network information if unique identifier or name of logical
     network is passed.
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
    logical_network_id:
        description:
            - Unique identifier of the logical network available in the device, if both I(logical_network_id)
              and I(logical_network_name) are passed, I(logical_network_id) will be used.
        type: int
    logical_network_name:
        description:
            - Unique name of the logical network available in the device, if both I(logical_network_id)
              and I(logical_network_name) are passed, I(logical_network_id) will be used.
        type: str

requirements:
    - "python >= 2.7.5"
author: "Deepak Joshi(@deepakjoshishri)"
'''

EXAMPLES = """
---
- name: Retrieve information about all logical networks available in device.
  ome_logical_network_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"

- name: Retrieve information about logical network with Id 12345 available in device.
  ome_logical_network_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    logical_network_id: 12345

- name: Retrieve information about logical network with name "Logical Network - 1" available in device.
  ome_logical_network_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    logical_network_name: "Logical Network - 1"
"""

RETURN = '''
---
msg:
  type: str
  description: Over all logical networks information status.
  returned: on error
  sample: "Failed to fetch the Open Manage Enterprise logical network information"
logical_network_info:
  type: dict
  description: Details information of the Logical Networks.
  returned: success
  sample: {
    "value": [
        {
            "CreatedBy": "admin",
            "CreationTime": "2019-06-29 12:52:47.802",
            "Description": "Logical Network configured to demonstrate sample usage.",
            "Id": 27923,
            "InternalRefNWUUId": "f4fecb81-3115-47fe-b6a2-996f85a765f8",
            "Name": "Logical Network - 1",
            "Type": 10,
            "UpdatedBy": null,
            "UpdatedTime": "2019-06-29 12:52:47.802",
            "VlanMaximum": 2327,
            "VlanMinimum": 2327
        },
        {
            "CreatedBy": "admin",
            "CreationTime": "2019-06-29 12:53:42.393",
            "Description": "Logical Network configured to demonstrate usage of ansible module.",
            "Id": 27924,
            "InternalRefNWUUId": "bbaaa898-fe71-4ecd-98cf-28bf5860642d",
            "Name": "Logical Network - 2",
            "Type": 6,
            "UpdatedBy": null,
            "UpdatedTime": "2019-06-29 12:53:42.393",
            "VlanMaximum": 777,
            "VlanMinimum": 777
        },
        {
            "CreatedBy": "admin",
            "CreationTime": "2019-06-29 12:54:37.616",
            "Description": "Logical Network created for sample of ansible module.",
            "Id": 27925,
            "InternalRefNWUUId": "f84cb6c1-7d4a-4f89-bfd8-b6fb526b62d2",
            "Name": "Logical Network - 3",
            "Type": 8,
            "UpdatedBy": null,
            "UpdatedTime": "2019-06-29 12:54:37.616",
            "VlanMaximum": 1223,
            "VlanMinimum": 1223
        }
    ]
}
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.dellemc.ome import RestOME
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.urls import ConnectionError, SSLValidationError

# Base URI to fetch all logical networks information
LOGICAL_NETWORK_BASE_URI = "NetworkConfigurationService/Networks"


def _get_logical_network_id_from_logical_network_name(logical_network_name, rest_obj):
    """
    Get logical network id from logical network name
    Returns :dict : logical_network_id to logical_network_name map
    :arg logical_network_name: unique name of logical network
    :arg rest_obj: RestOME class object in case of request with session.
    :returns: logical_network_id: False if not found, Id of logical network if found
    """
    logical_network_id = False
    # Fetch all logical networks information
    resp = rest_obj.invoke_request('GET', LOGICAL_NETWORK_BASE_URI)
    if resp.success:
        # Search for specified logical network name and
        # return ID of logical network if found, else false
        logical_networks_list = resp.json_data["value"]
        for item in logical_networks_list:
            if item["Name"] == logical_network_name:
                logical_network_id = item["Id"]
                break
    else:
        raise ValueError(resp.json_data)
    return logical_network_id


def main():
    module = AnsibleModule(
        argument_spec={
            "hostname": {"required": True, "type": 'str'},
            "username": {"required": True, "type": 'str'},
            "password": {"required": True, "type": 'str', "no_log": True},
            "port": {"required": False, "default": 443, "type": 'int'},
            "logical_network_id": {"required": False, "type": 'int'},
            "logical_network_name": {"required": False, "type": 'str'}
        },
        supports_check_mode=False)
    try:
        with RestOME(module.params, req_session=True) as rest_obj:
            # Form URI to fetch all logical networks information
            logical_network_uri = LOGICAL_NETWORK_BASE_URI
            if module.params.get("logical_network_id"):
                # Form URI to fetch specific logical network information if logical_network_id is provided
                logical_network_uri = "{0}({1})".format(logical_network_uri, module.params.get("logical_network_id"))
            elif module.params.get("logical_network_name"):
                # Form URI to fetch specific logical network information if logical_network_name is provided,
                # by fetching logical_network_id from logical_network_uri
                logical_network_name = module.params.get("logical_network_name")
                logical_network_id = _get_logical_network_id_from_logical_network_name(logical_network_name, rest_obj)
                if logical_network_id:
                    logical_network_uri = "{0}({1})".format(logical_network_uri, logical_network_id)
                else:
                    module.fail_json(msg="Provided logical network name - '{0}' does not exist in the device".
                                     format(logical_network_name))
            resp = rest_obj.invoke_request('GET', logical_network_uri)
            logical_network_info = resp.json_data
        if resp.status_code == 200:
            module.exit_json(logical_network_info=logical_network_info)
        else:
            module.fail_json(msg="Failed to fetch the device logical network information")
    except (URLError, HTTPError, SSLValidationError, ConnectionError, TypeError, ValueError) as err:
        module.fail_json(msg=str(err))


if __name__ == '__main__':
    main()
