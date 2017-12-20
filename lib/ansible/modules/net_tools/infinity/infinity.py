#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c), meiliu@fusionlayer.com, 2017
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: infinity
short_description: "manage Infinity IPAM using Rest API"
description:
  - "Manage Infinity IPAM using REST API"
version_added: "2.4"
author:
  - "Meirong Liu"
options:
  server_ip:
    description:
      - Infinity server_ip with IP address
    required: true
  username:
    description:
      - Username to access Infinity
      - The user must have Rest API privileges
    required: true
  password:
    description:
      - Infinity password
    required: true
  action:
    description:
      - Action to perform
    required: true
    choices:
      - reserve_next_available_ip
      - release_ip
      - delete_network
      - add_network
      - reserve_network
      - release_network
      - get_network_id

  network_id:
    description:
      - Network ID
    default: ''
  ip_address:
    description:
      - IP Address for a reservation or a release
    default: ''
  network_address:
    description:
      - Network address with CIDR format (e.g., 192.168.310.0)
    required: false
    default: ""
  network_size:
    description:
      - Network bitmask (e.g. 255.255.255.220) or CIDR format (e.g., /26)
    default: ''
  network_name:
    description:
      - The name of a network
    default: ''
  network_location:
    description:
      - the parent network id for a given network
    default: -1
  network_type:
    description:
      - Network type defined by Infinity
    choices:
      - lan
      - shared_lan
      - supernet
    default: "lan"
  network_family:
    description:
      - Network family defined by Infinity, e.g. IPv4, IPv6 and Dual stack
    choices:
      - 4
      - 6
      - dual
    default: "4"

"""


EXAMPLES = """
---
- hosts: localhost
  connection: local
  strategy: debug
  tasks:
    - name: Reserve network into Infinity IPAM
      infinity:
        server_ip: "80.75.107.12"
        username: "username"
        password: "password"
        action: "reserve_network"
        network_name: "reserve_new_ansible_network"
        network_family: "4"
        network_type: 'lan'
        network_id: "1201"
        network_size: "/28"
      register: infinity

"""

RETURN = """
network_id:
    description: id for a given network
    returned: success
    type: string
    sample: '1501'
ip_info:
    description: when reserve next available ip address from a network, the ip address info ) is returned.
    returned: success
    type: string
    sample: '{"address": "192.168.10.3", "hostname": "", "FQDN": "", "domainname": "", "id": 3229}'
network_info:
    description: when reserving a LAN network from a Infinity supernet by providing network_size, the information about the reserved network is returned.
    returned: success
    type: string
    sample:  {"network_address": "192.168.10.32/28","network_family": "4", "network_id": 3102,
    "network_size": null,"description": null,"network_location": "3085",
    "ranges": { "id": 0, "name": null,"first_ip": null,"type": null,"last_ip": null},
    "network_type": "lan","network_name": "'reserve_new_ansible_network'"}
"""


from ansible.module_utils.basic import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url


class Infinity(object):
    """
    Class for manage REST API calls with the Infinity.
    """

    def __init__(self, module, server_ip, username, password):
        self.module = module
        self.auth_user = username
        self.auth_pass = password
        self.base_url = "https://%s/rest/v1/" % (str(server_ip))

    def _get_api_call_ansible_handler(
            self,
            method='get',
            resource_url='',
            stat_codes=None,
            params=None,
            payload_data=None):
        """
        Perform the HTTPS request by using anible get/delete method
        """
        stat_codes = [200] if stat_codes is None else stat_codes
        request_url = str(self.base_url) + str(resource_url)
        response = None
        headers = {'Content-Type': 'application/json'}
        if not request_url:
            self.module.exit_json(
                msg="When sending Rest api call , the resource URL is empty, please check.")
        if payload_data and not isinstance(payload_data, str):
            payload_data = json.dumps(payload_data)
        response_raw = open_url(
            str(request_url),
            method=method,
            timeout=20,
            headers=headers,
            url_username=self.auth_user,
            url_password=self.auth_pass,
            validate_certs=False,
            force_basic_auth=True,
            data=payload_data)

        response = response_raw.read()
        payload = ''
        if response_raw.code not in stat_codes:
            self.module.exit_json(
                changed=False,
                meta=" openurl response_raw.code show error and error code is %r" %
                (response_raw.code))
        else:
            if isinstance(response, str) and len(response) > 0:
                payload = response
            elif method.lower() == 'delete' and response_raw.code == 204:
                payload = 'Delete is done.'
        if isinstance(payload, dict) and "text" in payload:
            self.module.exit_json(
                changed=False,
                meta="when calling rest api, returned data is not json ")
            raise Exception(payload["text"])
        return payload

    # ---------------------------------------------------------------------------
    # get_network()
    # ---------------------------------------------------------------------------
    def get_network(self, network_id, network_name, limit=-1):
        """
        Search network_name inside Infinity by using rest api
        Network id  or network_name needs to be provided
        return the details of a given with given network_id or name
        """
        if network_name is None and network_id is None:
            self.module.exit_json(
                msg="You must specify  one of the options 'network_name' or 'network_id'.")
        method = "get"
        resource_url = ''
        params = {}
        response = None
        if network_id:
            resource_url = "networks/" + str(network_id)
            response = self._get_api_call_ansible_handler(method, resource_url)
        if network_id is None and network_name:
            method = "get"
            resource_url = "search"
            params = {"query": json.dumps(
                {"name": network_name, "type": "network"})}
            response = self._get_api_call_ansible_handler(
                method, resource_url, payload_data=json.dumps(params))
            if response and isinstance(response, str):
                response = json.loads(response)
            if response and isinstance(response, list) and len(
                    response) > 1 and limit == 1:
                response = response[0]
                response = json.dumps(response)
        return response

    # ---------------------------------------------------------------------------
    # get_network_id()
    # ---------------------------------------------------------------------------
    def get_network_id(self, network_name="", network_type='lan'):
        """
        query network_id from Infinity  via rest api based on given network_name
        """
        method = 'get'
        resource_url = 'search'
        response = None
        if network_name is None:
            self.module.exit_json(
                msg="You must specify the option 'network_name'")
        params = {"query": json.dumps(
            {"name": network_name, "type": "network"})}
        response = self._get_api_call_ansible_handler(
            method, resource_url, payload_data=json.dumps(params))
        network_id = ""
        if response and isinstance(response, str):
            response = json.loads(response)
        if response and isinstance(response, list):
            response = response[0]
            network_id = response['id']
        return network_id

    # ---------------------------------------------------------------------------
    # reserve_next_available_ip()
    # ---------------------------------------------------------------------------
    def reserve_next_available_ip(self, network_id=""):
        """
        Reserve ip address via  Infinity by using rest api
        network_id:  the id of the network that users would like to reserve network from
        return the next available ip address from that given network
        """
        method = "post"
        resource_url = ''
        response = None
        ip_info = ''
        if not network_id:
            self.module.exit_json(
                msg="You must specify the option 'network_id'.")
        if network_id:
            resource_url = "networks/" + str(network_id) + "/reserve_ip"
            response = self._get_api_call_ansible_handler(method, resource_url)
            if response and response.find(
                    "[") >= 0 and response.find("]") >= 0:
                start_pos = response.find("{")
                end_pos = response.find("}")
                ip_info = response[start_pos: (end_pos + 1)]
        return ip_info

    # -------------------------
    # release_ip()
    # -------------------------
    def release_ip(self, network_id="", ip_address=""):
        """
        Reserve ip address via  Infinity by using rest api
        """
        method = "get"
        resource_url = ''
        response = None
        if ip_address is None or network_id is None:
            self.module.exit_json(
                msg="You must specify  those two options: 'network_id' and 'ip_address'.")

        resource_url = "networks/" + str(network_id) + "/children"
        response = self._get_api_call_ansible_handler(method, resource_url)
        if not response:
            self.module.exit_json(
                msg="There is an error in release ip %s from network  %s." %
                (ip_address, network_id))

        ip_list = json.loads(response)
        ip_idlist = []
        for ip_item in ip_list:
            ip_id = ip_item['id']
            ip_idlist.append(ip_id)
        deleted_ip_id = ''
        for ip_id in ip_idlist:
            ip_response = ''
            resource_url = "ip_addresses/" + str(ip_id)
            ip_response = self._get_api_call_ansible_handler(
                method,
                resource_url,
                stat_codes=[200])
            if ip_response and json.loads(
                    ip_response)['address'] == str(ip_address):
                deleted_ip_id = ip_id
                break
        if deleted_ip_id:
            method = 'delete'
            resource_url = "ip_addresses/" + str(deleted_ip_id)
            response = self._get_api_call_ansible_handler(
                method, resource_url, stat_codes=[204])
        else:
            self.module.exit_json(
                msg=" When release ip, could not find the ip address %r from the given network %r' ." %
                (ip_address, network_id))

        return response

    # -------------------
    # delete_network()
    # -------------------
    def delete_network(self, network_id="", network_name=""):
        """
        delete network from  Infinity by using rest api
        """
        method = 'delete'
        resource_url = ''
        response = None
        if network_id is None and network_name is None:
            self.module.exit_json(
                msg="You must specify one of those options: 'network_id','network_name' .")
        if network_id is None and network_name:
            network_id = self.get_network_id(network_name=network_name)
        if network_id:
            resource_url = "networks/" + str(network_id)
            response = self._get_api_call_ansible_handler(
                method, resource_url, stat_codes=[204])
        return response

    # reserve_network()
    # ---------------------------------------------------------------------------
    def reserve_network(self, network_id="",
                        reserved_network_name="", reserved_network_description="",
                        reserved_network_size="", reserved_network_family='4',
                        reserved_network_type='lan', reserved_network_address="",):
        """
        Reserves the first available network of specified size from a given supernet
         <dt>network_name (required)</dt><dd>Name of the network</dd>
            <dt>description (optional)</dt><dd>Free description</dd>
            <dt>network_family (required)</dt><dd>Address family of the network. One of '4', '6', 'IPv4', 'IPv6', 'dual'</dd>
            <dt>network_address (optional)</dt><dd>Address of the new network. If not given, the first network available will be created.</dd>
            <dt>network_size (required)</dt><dd>Size of the new network in /&lt;prefix&gt; notation.</dd>
            <dt>network_type (required)</dt><dd>Type of network. One of 'supernet', 'lan', 'shared_lan'</dd>

        """
        method = 'post'
        resource_url = ''
        network_info = None
        if network_id is None or reserved_network_name is None or reserved_network_size is None:
            self.module.exit_json(
                msg="You must specify those options: 'network_id', 'reserved_network_name' and 'reserved_network_size'")
        if network_id:
            resource_url = "networks/" + str(network_id) + "/reserve_network"
        if not reserved_network_family:
            reserved_network_family = '4'
        if not reserved_network_type:
            reserved_network_type = 'lan'
        payload_data = {
            "network_name": reserved_network_name,
            'description': reserved_network_description,
            'network_size': reserved_network_size,
            'network_family': reserved_network_family,
            'network_type': reserved_network_type,
            'network_location': int(network_id)}
        if reserved_network_address:
            payload_data.update({'network_address': reserved_network_address})

        network_info = self._get_api_call_ansible_handler(
            method, resource_url, stat_codes=[200, 201], payload_data=payload_data)

        return network_info

    # ---------------------------------------------------------------------------
    # release_network()
    # ---------------------------------------------------------------------------
    def release_network(
            self,
            network_id="",
            released_network_name="",
            released_network_type='lan'):
        """
        Release the network with name 'released_network_name' from the given  supernet network_id
        """
        method = 'get'
        response = None
        if network_id is None or released_network_name is None:
            self.module.exit_json(
                msg="You must specify those options 'network_id', 'reserved_network_name' and 'reserved_network_size'")
        matched_network_id = ""
        resource_url = "networks/" + str(network_id) + "/children"
        response = self._get_api_call_ansible_handler(method, resource_url)
        if not response:
            self.module.exit_json(
                msg=" there is an error in releasing network %r  from network  %s." %
                (network_id, released_network_name))
        if response:
            response = json.loads(response)
            for child_net in response:
                if child_net['network'] and child_net['network']['network_name'] == released_network_name:
                    matched_network_id = child_net['network']['network_id']
                    break
        response = None
        if matched_network_id:
            method = 'delete'
            resource_url = "networks/" + str(matched_network_id)
            response = self._get_api_call_ansible_handler(
                method, resource_url, stat_codes=[204])
        else:
            self.module.exit_json(
                msg=" When release network , could not find the network   %r from the given superent %r' " %
                (released_network_name, network_id))

        return response

    # ---------------------------------------------------------------------------
    # add_network()
    # ---------------------------------------------------------------------------
    def add_network(
            self, network_name="", network_address="",
            network_size="", network_family='4',
            network_type='lan', network_location=-1):
        """
        add a new LAN network into a given supernet Fusionlayer Infinity via rest api  or default supernet
        required fields=['network_name', 'network_family', 'network_type',  'network_address','network_size' ]
        """
        method = 'post'
        resource_url = 'networks'
        response = None
        if network_name is None or network_address is None or network_size is None:
            self.module.exit_json(
                msg="You must specify  those options 'network_name', 'network_address' and 'network_size'")

        if not network_family:
            network_family = '4'
        if not network_type:
            network_type = 'lan'
        if not network_location:
            network_location = -1
        payload_data = {
            "network_name": network_name,
            'network_address': network_address,
            'network_size': network_size,
            'network_family': network_family,
            'network_type': network_type,
            'network_location': network_location}
        response = self._get_api_call_ansible_handler(
            method='post', resource_url=resource_url,
            stat_codes=[200], payload_data=payload_data)
        return response


def main():
    my_module = AnsibleModule(argument_spec=dict(
        server_ip=dict(required=True, type='str'),
        username=dict(required=True, type='str'),
        password=dict(required=True, type='str', no_log=True),
        network_id=dict(type='str'),
        ip_address=dict(type='str'),
        network_name=dict(type='str'),
        network_location=dict(default=-1, type='int'),
        network_family=dict(default='4', choices=['4', '6', 'dual']),
        network_type=dict(default='lan', choices=['lan', 'shared_lan', 'supernet']),
        network_address=dict(type='str'),
        network_size=dict(type='str'),
        action=dict(required=True, choices=['get_network', 'reserve_next_available_ip', 'release_ip',
                                            'delete_network', 'reserve_network', 'release_network',
                                            'add_network', 'get_network_id'],),
    ), required_together=(['username', 'password'],),)
    server_ip = my_module.params["server_ip"]
    username = my_module.params["username"]
    password = my_module.params["password"]
    action = my_module.params["action"]
    network_id = my_module.params["network_id"]
    released_ip = my_module.params["ip_address"]
    network_name = my_module.params["network_name"]
    network_family = my_module.params["network_family"]
    network_type = my_module.params["network_type"]
    network_address = my_module.params["network_address"]
    network_size = my_module.params["network_size"]
    network_location = my_module.params["network_location"]
    my_infinity = Infinity(my_module, server_ip, username, password)
    result = ''
    if action == "reserve_next_available_ip":
        if network_id:
            result = my_infinity.reserve_next_available_ip(network_id)
            if not result:
                result = 'There is an error in calling method of reserve_next_available_ip'
                my_module.exit_json(changed=False, meta=result)
            my_module.exit_json(changed=True, meta=result)
    elif action == "release_ip":
        if network_id and released_ip:
            result = my_infinity.release_ip(
                network_id=network_id, ip_address=released_ip)
            my_module.exit_json(changed=True, meta=result)
    elif action == "delete_network":
        result = my_infinity.delete_network(
            network_id=network_id, network_name=network_name)
        my_module.exit_json(changed=True, meta=result)

    elif action == "get_network_id":
        result = my_infinity.get_network_id(
            network_name=network_name, network_type=network_type)
        my_module.exit_json(changed=True, meta=result)
    elif action == "get_network":
        result = my_infinity.get_network(
            network_id=network_id, network_name=network_name)
        my_module.exit_json(changed=True, meta=result)
    elif action == "reserve_network":
        result = my_infinity.reserve_network(
            network_id=network_id,
            reserved_network_name=network_name,
            reserved_network_size=network_size,
            reserved_network_family=network_family,
            reserved_network_type=network_type,
            reserved_network_address=network_address)
        my_module.exit_json(changed=True, meta=result)
    elif action == "release_network":
        result = my_infinity.release_network(
            network_id=network_id,
            released_network_name=network_name,
            released_network_type=network_type)
        my_module.exit_json(changed=True, meta=result)

    elif action == "add_network":
        result = my_infinity.add_network(
            network_name=network_name,
            network_location=network_location,
            network_address=network_address,
            network_size=network_size,
            network_family=network_family,
            network_type=network_type)

        my_module.exit_json(changed=True, meta=result)


if __name__ == '__main__':
    main()
