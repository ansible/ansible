# !/usr/bin/python

# meiliu@fusionlayer.com
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from ansible.module_utils.basic import *
import requests
import json

try:
    import requests
    requests.packages.urllib3.disable_warnings()
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


DOCUMENTATION = """
module: infinity
short_description: manage Infinity IPAM using  Web API
description:
  - Manage Infinity IPAM using Web API
version_added: "1.0"
author:
  - "Meirong Liu"
requirements:
  - "requests >= 2.9.1"
options:
  server:
    description:
      - Infinity IP
    required: True
  username:
    description:
      -  username to access Infinity
      - The user must have Rest API privileges
    required: True
  password:
    description:
      - Infinity password
    required: True
  action:
    description:
      - Action to perform
    required: True
    choices:  [ 'reserve_next_available_ip', 'release_ip' , 'delete_network',
    'add_network' ,  'reserve_network', 'release_network', 'get_network_id'],

  network_id:
    description:
      - Network ID
      - Must be indicated as a network_id
    required: False
    default: False
  ip_address:
    description:
      - IP Address for reservation or for release
    required: False
    default: False
  network_address:
    description:
      - nework address  CIDR format (e.g 192.168.310.0)
    required: False
    default: False
 network_size:
    description:
      - nework bitmask (e.g. 255.255.255.220)or CIDR format (e.g  /26)
    required: False
    default: False
 network_name:
    description:
      - nework name
    required: False
    default: False
 network_location:
    description:
        the parent network id for a given network
    required: False
    default: -1
 network_type:
    description:
      - network type defined by     Infinity
    required: False
    "choices": ['lan', 'shared_lan', 'supernet']
    default: "lan"
 network_family:
    description:
      - network family defined by  Infinity, e.g. IPv4, IPv6 , Dual stack
    required: False
    "choices": ['4', '6', 'dual']
    default: "4"

"""

RETURN = """
result:
  {
    "network_address": "192.168.10.32/28",
    "information": [

        {
            "name": "Country Location",
            "value": "Australia",
            "type": "one_of",
            "required": true
        },
        {
            "name": "Customer Email",
            "value": "relaxed.admin@ease.com",
            "type": "unicode_string",
            "required": true
        },

        {
            "name": "Location City",
            "value": "City Name",
            "type": "unicode_string",
            "required": true
        }
    ],
    "network_family": "4",
    "network_id": 3102,
    "network_size": null,
    "description": null,
    "network_location": "3085",
    "ranges": {
        "id": 0,
        "name": null,
        "first_ip": null,
        "type": null,
        "last_ip": null
    },
    "network_type": "lan",
    "network_name": "'reserve_new_ansible_network'"
}
"""

EXAMPLES = """
---
- hosts: localhost
  connection: local
       gather_facts: False
  strategy: debug
  tasks:
    - name: Reserve network into Infinity IPAM
      infinity:
        server: "80.75.107.12"
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


class Infinity(object):
    """
    Class for manage REST API calls with the Infinity.
    """

    def __init__(self, module, server, username, password):
        self.module = module
        self.auth = (username, password)
        self.base_url = "https://{server}/rest/v1/".format(server=server)

    def call_api(
            self,
            method,
            resource_url,
            stat_codes=[200],
            params=None,
            payload_data=None):
        """
        Perform the HTTPS request by using rest api
        """
        requests.packages.urllib3.disable_warnings()
        request_url = self.base_url + resource_url
        response = None
        response = getattr(
            requests,
            method)(
            request_url,
            auth=self.auth,
            verify=False,
            params=params,
            data=payload_data)
        payload = None
        if response.status_code not in stat_codes:
            response.raise_for_status()
        else:
            if len(response.text) > 0:
                payload = response.json()
            elif method.lower() == 'delete' and response.status_code == 204:
                payload = 'Delete is done.'
        if isinstance(payload, dict) and "text" in payload:
            raise Exception(payload["text"])
        else:
            return payload

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
        if not network_id:
            self.module.exit_json(
                msg="You must specify  the  option  'network_id'.")
        if network_id:
            resource_url = "networks/" + str(network_id) + "/reserve_ip"
            response = self.call_api(method, resource_url)
            if response:
                response = response[0]
            else:
                self.module.exit_json(
                    msg="There is no ip address available from this network .")

        return response

    # -------------------------
    # release_ip()
    # -------------------------
    def release_ip(self, network_id="", ip_address=""):
        """
        Reserve ip address via  Infinity by using rest api
        """
        method = "post"
        resource_url = ''
        response = None
        if ip_address is None or network_id is None:
            self.module.exit_json(
                msg="You must specify  those two  options 'network_id' or 'ip_address'.")
        resource_url = "networks/" + str(network_id) + "/deallocateip"
        payload_data = {"ip_address": str(ip_address)}
        response = self.call_api(
            method,
            resource_url,
            stat_codes=[202],
            payload_data=payload_data)
        if not response:
            self.module.exit_json(
                msg="There is  error in release ip %s from network  %s." %
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
                msg="You must specify   one of those the  options 'network_id','network_name' .")
        if network_id is None and network_name:
            network_id = self.get_network_id(network_name=network_name)
        if network_id:
            resource_url = "networks/" + str(network_id)
            response = self.call_api(method, resource_url, stat_codes=[204])
        return response

    # ---------------------------------------------------------------------------
    # add_network()
    # ---------------------------------------------------------------------------
    def add_network(
            self,
            network_name="",
            network_address="",
            network_size="",
            network_family='4',
            network_type='lan',
            network_location=-1):
        """
        add  new nework into    Infinity via rest api  into given supernet or default supernet
        checked_fields=['network_name', 'network_family', 'network_type',  'network_address','network_size' ]

        """
        method = 'post'
        resource_url = 'networks'
        response = None
        if network_name is None or network_address is None or network_size is None:
            self.module.exit_json(
                msg="You must specify  those the  options 'network_name', 'network_address' and 'network_size'")

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
        response = self.call_api(
            method,
            resource_url,
            stat_codes=[200],
            payload_data=payload_data)

        return response

    # ---------------------------------------------------------------------------
    # reserve_network()
    # ---------------------------------------------------------------------------
    def reserve_network(
        self,
        network_id="",
        reserved_network_name="",
        reserved_network_description="",
        reserved_network_size="",
        reserved_network_family='4',
        reserved_network_type='lan',
        reserved_network_address="",
    ):
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
        response = None
        if network_id is None or reserved_network_name is None or reserved_network_size is None:
            self.module.exit_json(
                msg="You must specify  those the  options 'network_id', 'reserved_network_name' and 'reserved_network_size'")
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
        response = self.call_api(
            method, resource_url, stat_codes=[
                200, 201], payload_data=payload_data)
        return response

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
                msg="You must specify  those the  options 'network_id', 'reserved_network_name' and 'reserved_network_size'")
        matched_network_id = ""
        resource_url = "networks/" + str(network_id) + "/children"
        response = self.call_api(method, resource_url, stat_codes=[200])
        if response:
            for child_net in response:
                if child_net['network'] and child_net['network']['network_name'] == released_network_name:
                    matched_network_id = child_net['network']['network_id']
                    break
        response = None
        if matched_network_id:
            method = 'delete'
            resource_url = "networks/" + str(matched_network_id)
            response = self.call_api(method, resource_url, stat_codes=[204])
        return response

    # ---------------------------------------------------------------------------
    # get_network_id()
    # ---------------------------------------------------------------------------
    def get_network_id(self, network_name="", network_type='lan'):
        """
        query network_id from Infinity  via rest api
        query nework_id by network_name

        """
        method = 'get'
        resource_url = 'search'
        response = None
        if network_name is None:
            self.module.exit_json(
                msg="You must specify  the the  option 'network_name'")
        if not network_type:
            network_type = 'lan'
        params = {"query": json.dumps(
            {"name": network_name, "type": "network"})}
        response = self.call_api(
            method,
            resource_url,
            stat_codes=[200],
            params=params)
        network_id = ""
        if response and isinstance(response, list):
            response = response[0]
            network_id = response['id']

        return network_id

    # ---------------------------------------------------------------------------
    # get_network()
    # ---------------------------------------------------------------------------
    def get_network(self, network_id, network_name, limit=-1):
        """
        Search network_name in Infinity by using rest api
        Network id  or network_name needs to be provided
        return the details of a given with given network_id or name
        """
        if network_name is None and network_id is None:
            self.module.exit_json(
                msg="You must specify  one of the options 'network_name' or 'network_id'.")
        # first get list of network with that name, the get the id of the first
        # network and call  rest api again
        method = "get"
        resource_url = ''
        params = {}
        response = None
        if network_id:
            resource_url = "networks/" + str(network_id)
            response = self.call_api(method, resource_url)
        if network_id is None and network_name:
            resource_url = "search"
            params = {"query": json.dumps(
                {"name": network_name, "type": "network"})}
            response = self.call_api(method, resource_url, params=params)
            if response and isinstance(response, list) and len(
                    response) > 1 and limit == 1:
                response = response[0]
            # response  has field 'id', 'network'
        return response


def main():

    fields = {
        "server": {
            "required": True,
            "type": "str"},
        "username": {
            "required": True,
            "type": "str"},
        "password": {
            "required": True,
            "type": "str"},
        "network_id": {
            "required": False},
        "ip_address": {
            "required": False,
            "type": "str"},
        "network_name": {
            "required": False,
            "type": "str"},
        "network_location": {
            "required": False,
            "type": "int",
            "default": -1},
        "network_family": {
            "required": False,
            "type": "str",
            "choices": [
                '4',
                '6',
                'dual']},
        "network_type": {
            "required": False,
            "choices": [
                'lan',
                'shared_lan',
                'supernet']},
        "network_address": {
            "required": False,
            "type": "str"},
        "network_size": {
            "required": False,
            "type": "str"},
        "action": {
            "required": True,
            "choices": [
                'reserve_next_available_ip',
                'release_ip',
                'delete_network',
                'add_network',
                'reserve_network',
                'release_network',
                'get_network',
                'get_network_id'],
        },
    }

    # mutually_exclusive = [ ["network_id", "network_name"] ]
    # required_together = [ ["attr_name", "attr_value"], ]
    # module = AnsibleModule(argument_spec=fields, mutually_exclusive=mutually_exclusive, supports_check_mode=True)
    my_module = AnsibleModule(argument_spec=fields)
    if not HAS_REQUESTS:
        my_module.fail_json(
            msg="Library 'requests' is required. Use 'sudo pip install requests' to fix it.")

    server = my_module.params["server"]
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

    my_infinity = Infinity(my_module, server, username, password)
    result2 = ''
    if action == "reserve_next_available_ip":
        if network_id:
            result2 = my_infinity.reserve_next_available_ip(network_id)
            if not result2:
                result2 = 'There is an error in calling method reserve_next_available_ip'
            my_module.exit_json(changed=True, meta=result2)
    elif action == "release_ip":
        if network_id and released_ip:
            result2 = my_infinity.release_ip(
                network_id=network_id, ip_address=released_ip)
            my_module.exit_json(changed=True, meta=result2)
    elif action == "delete_network":
        result2 = my_infinity.delete_network(
            network_id=network_id, network_name=network_name)
        my_module.exit_json(changed=True, meta=result2)

    elif action == "get_network_id":
        result2 = my_infinity.get_network_id(
            network_name=network_name, network_type=network_type)
        my_module.exit_json(changed=True, meta=result2)
    elif action == "get_network":
        result2 = my_infinity.get_network(
            network_id=network_id, network_name=network_name)
        my_module.exit_json(changed=True, meta=result2)
    elif action == "reserve_network":
        result2 = my_infinity.reserve_network(
            network_id=network_id,
            reserved_network_name=network_name,
            reserved_network_size=network_size,
            reserved_network_family=network_family,
            reserved_network_type=network_type,
            reserved_network_address=network_address)
        my_module.exit_json(changed=True, meta=result2)
    elif action == "release_network":
        result2 = my_infinity.release_network(
            network_id=network_id,
            released_network_name=network_name,
            released_network_type=network_type)
        my_module.exit_json(changed=True, meta=result2)

    elif action == "add_network":
        result2 = my_infinity.add_network(
            network_name=network_name,
            network_location=network_location,
            network_address=network_address,
            network_size=network_size,
            network_family=network_family,
            network_type=network_type)

        my_module.exit_json(changed=True, meta=result2)


if __name__ == '__main__':
    main()
