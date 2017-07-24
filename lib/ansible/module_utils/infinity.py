# !/usr/bin/python
# meiliu@fusionlayer.com
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.


has_url_parse = True
try:
    # python3
    import urllib.request as urllib_request
    import urllib.parse as urllib_parse
    from urllib.request import AbstractHTTPHandler
    has_url_parse = True
except ImportError as e:
    # python2
    has_url_parse = False
    import urllib2 as urllib2_request
    import urllib
    import base64

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *


DOCUMENTATION = """
module: infinity
short_description: manage Infinity IPAM using  Web API
description:
  - Manage Infinity IPAM using Web API
version_added: "1.0"
author:
  - "Meirong Liu"
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
        self.auth_user = username
        self.auth_pass = password
        self.base_url = "https://%s/rest/v1/" % (str(server))

    def _get_api_call_ansible_handler(
            self,
            method='get',
            resource_url='',
            stat_codes=[200],
            params=None,
            payload_data=None):
        """
        Perform the HTTPS request by using anible get/delete method
        """
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
        # get_network works @20170721
        """
        Search network_name in Infinity by using rest api
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
                msg="You must specify  the the  option 'network_name'")
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
        if not network_id:
            self.module.exit_json(
                msg="You must specify  the  option  'network_id'.")
        if network_id:
            resource_url = "networks/" + str(network_id) + "/reserve_ip"
            response = self._get_api_call_ansible_handler(method, resource_url)
            if response and response.find(
                    "[") >= 0 and response.find("]") >= 0:
                start_pos = response.find("{")
                end_pos = response.find("}")
                response = response[start_pos: (end_pos + 1)]
        return response

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
                msg="You must specify  those two  options 'network_id' or 'ip_address'.")

        resource_url = "networks/" + str(network_id) + "/children"
        response = self._get_api_call_ansible_handler(method, resource_url)
        if not response:
            self.module.exit_json(
                msg="There is  error in release ip %s from network  %s." %
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
                msg=" When release ip, could not find the ip address  %r from the given network %r' ." %
                (ip_address, network_id))

        return response

    # -------------------
    # delete_network()
    # -------------------
    def delete_network(self, network_id="", network_name=""):
        """
        delete network from  Infinity by using rest api
        """
        # verfiy that delete network is done
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
            response = self._get_api_call_ansible_handler(
                method, resource_url, stat_codes=[204])
        return response

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

        status_code, response = self.post_data(
            method='post', resource_url=resource_url, stat_codes=[
                200, 201], payload_data=payload_data)
        if status_code == 0:
            if int(response) and int(response) in [400, 403, 404, 422]:
                error_msg_dict = {
                    '400': 'Network  is not a supernet, cannot reserve network',
                    '404': 'SuperNetwork not found',
                    '403': 'Unauthorized',
                    '422': 'Validation error(s) for network parameters'}
                self.module.exit_json(
                    msg="when reserve network from a supernet, get error message %r" %
                    (error_msg_dict.get(
                        str(response))))

        return response

    def post_data(self, method='post',
                  resource_url='',
                  stat_codes=[200],
                  params=None,
                  payload_data=None):
        """
        payload data needs to be dict
        """
        resource_url = str(self.base_url) + str(resource_url)
        data = None
        if has_url_parse:
            # if python3
            if payload_data and isinstance(payload_data, dict):
                data = urllib_parse.urlencode(payload_data)
                data = data.encode('utf-8')  # data must be bytes
            passman = urllib_request.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(
                None, resource_url, str(
                    self.auth_user), str(
                    self.auth_pass))
            authhandler = urllib_request.HTTPBasicAuthHandler(passman)
            opener = urllib_request.build_opener(authhandler)
            urllib_request.install_opener(opener)
            req = urllib_request.Request(resource_url, data)
            req.add_header(
                "Content-Type",
                "application/x-www-form-urlencoded;charset=utf-8")
            post_result = None
            with urllib_request.urlopen(req) as response:
                post_result = response.read()
                post_result = post_result.decode('utf-8')
            return post_result
        else:
            request = urllib2_request.Request(url=resource_url)
            base64string = base64.b64encode(
                '%s:%s' %
                (self.auth_user, self.auth_pass))
            request.add_header("Authorization", "Basic %s" % base64string)
            request.add_data(urllib.urlencode(payload_data))
            result = urllib2_request.urlopen(request)
            resp_status_code = result.getcode()
            if int(resp_status_code) not in stat_codes:
                return 0, resp_status_code
            else:
                final_result = result.read()
                return 1, final_result

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
        response = self._get_api_call_ansible_handler(method, resource_url)
        if not response:
            self.module.exit_json(
                msg=" there is  error  in release network %r  from network  %s." %
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
            self,
            network_name="",
            network_address="",
            network_size="",
            network_family='4',
            network_type='lan',
            network_location=-1):
        """
        add  new nework into    Infinity via rest api  into given supernet or default supernet
        required fields=['network_name', 'network_family', 'network_type',  'network_address','network_size' ]

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
        status_code, response = self.post_data(
            method='post', resource_url=resource_url, stat_codes=[200], payload_data=payload_data)
        if status_code == 0:
            if int(response) and int(response) in [403, 404, 422]:
                error_msg_dict = {
                    '404': 'SuperNetwork not found',
                    '403': 'Unauthorized',
                    '422': 'Validation error(s) for network parameters'}
                self.module.exit_json(
                    msg="when reserve network from a supernet, get error message %r" %
                    (error_msg_dict.get(
                        str(response))))

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
            "default":-1},
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
                'get_network',  # works
                'reserve_next_available_ip',  # works
                'release_ip',  # work
                'delete_network',  # work
                'reserve_network',  # work
                'release_network',  # work
                'add_network',
                'get_network_id'],  # work
        },
    }

    # mutually_exclusive = [ ["network_id", "network_name"] ]
    # required_together = [ ["attr_name", "attr_value"], ]
    # module = AnsibleModule(argument_spec=fields, mutually_exclusive=mutually_exclusive, supports_check_mode=True)
    my_module = AnsibleModule(argument_spec=fields)

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
