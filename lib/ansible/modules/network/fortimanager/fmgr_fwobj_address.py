#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = '''
---
module: fmgr_fwobj_address
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Allows the management of firewall objects in FortiManager
description:
  -  Allows for the management of IPv4, IPv6, and multicast address objects within FortiManager.

options:
  host:
    description:
      - The FortiManager address.
    required: true
  username:
    description:
      - The username used to authenticate with the FortiManager.
    required: true
  password:
    description:
      - The password associated with the username account.
    required: true

  adom:
    description:
      - The ADOM the configuration should belong to.

  allow_routing:
    description:
      - Enable/disable use of this address in the static route configuration.
    choices: ['enable', 'disable']

  associated_interface:
    description:
      - Associated interface name.

  cache_ttl:
    description:
      - Minimal TTL of individual IP addresses in FQDN cache. Only applies when type = wildcard-fqdn.

  color:
    description:
      - Color of the object in FortiManager GUI.
      - Takes integers 1-32

  comment:
    description:
      - Comment for the object in FortiManager.

  country:
    description:
      - Country name. Required if type = geographic.

  end_ip:
    description:
      - End IP. Only used when ipv4 = iprange.

  group_members:
    description:
      - Address group member. If this is defined w/out group_name, the operation will fail.

  group_name:
    description:
      - Address group name. If this is defined in playbook task, all other options are ignored.

  ipv4:
    description:
      - Type of IPv4 Object.
      - Must not be specified with either multicast or IPv6 parameters.
    choices: ['ipmask', 'iprange', 'fqdn', 'wildcard', 'geography', 'wildcard-fqdn', 'group']

  ipv4addr:
    description:
      - IP and network mask. If only defining one IP use this parameter. (i.e. 10.7.220.30/255.255.255.255)
      - Can also define subnets (i.e. 10.7.220.0/255.255.255.0)
      - Also accepts CIDR (i.e. 10.7.220.0/24)
      - If Netmask is omitted after IP address, /32 is assumed.
      - When multicast is set to Broadcast Subnet the ipv4addr parameter is used to specify the subnet.

  ipv6:
    description:
      - Puts module into IPv6 mode.
      - Must not be specified with either ipv4 or multicast parameters.
    choices: ['ip', 'iprange', 'group']

  ipv6addr:
    description:
      - IPv6 address in full. (i.e. 2001:0db8:85a3:0000:0000:8a2e:0370:7334)

  fqdn:
    description:
      - Fully qualified domain name.

  mode:
    description:
      - Sets one of three modes for managing the object.
    choices: ['add', 'set', 'delete']
    default: add

  multicast:
    description:
      - Manages Multicast Address Objects.
      - Sets either a Multicast IP Range or a Broadcast Subnet.
      - Must not be specified with either ipv4 or ipv6 parameters.
      - When set to Broadcast Subnet the ipv4addr parameter is used to specify the subnet.
      - Can create IPv4 Multicast Objects (multicastrange and broadcastmask options -- uses start/end-ip and ipv4addr).
    choices: ['multicastrange', 'broadcastmask', 'ip6']

  name:
    description:
      - Friendly Name Address object name in FortiManager.

  obj_id:
    description:
      - Object ID for NSX.

  start_ip:
    description:
      - Start IP. Only used when ipv4 = iprange.

  visibility:
    description:
      - Enable/disable address visibility.
    choices: ['enable', 'disable']

  wildcard:
    description:
      - IP address and wildcard netmask. Required if ipv4 = wildcard.

  wildcard_fqdn:
    description:
      - Wildcard FQDN. Required if ipv4 = wildcard-fqdn.
'''

EXAMPLES = '''
- name: ADD IPv4 IP ADDRESS OBJECT
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv4: "ipmask"
    ipv4addr: "10.7.220.30/32"
    name: "ansible_v4Obj"
    comment: "Created by Ansible"
    color: "6"

- name: ADD IPv4 IP ADDRESS OBJECT MORE OPTIONS
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv4: "ipmask"
    ipv4addr: "10.7.220.34/32"
    name: "ansible_v4Obj_MORE"
    comment: "Created by Ansible"
    color: "6"
    allow_routing: "enable"
    cache_ttl: "180"
    associated_interface: "port1"
    obj_id: "123"

- name: ADD IPv4 IP ADDRESS SUBNET OBJECT
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv4: "ipmask"
    ipv4addr: "10.7.220.0/255.255.255.128"
    name: "ansible_subnet"
    comment: "Created by Ansible"
    mode: "set"

- name: ADD IPv4 IP ADDRESS RANGE OBJECT
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv4: "iprange"
    start_ip: "10.7.220.1"
    end_ip: "10.7.220.125"
    name: "ansible_range"
    comment: "Created by Ansible"

- name: ADD IPv4 IP ADDRESS WILDCARD OBJECT
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv4: "wildcard"
    wildcard: "10.7.220.30/255.255.255.255"
    name: "ansible_wildcard"
    comment: "Created by Ansible"

- name: ADD IPv4 IP ADDRESS WILDCARD FQDN OBJECT
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv4: "wildcard-fqdn"
    wildcard_fqdn: "*.myds.com"
    name: "Synology myds DDNS service"
    comment: "Created by Ansible"

- name: ADD IPv4 IP ADDRESS FQDN OBJECT
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv4: "fqdn"
    fqdn: "ansible.com"
    name: "ansible_fqdn"
    comment: "Created by Ansible"

- name: ADD IPv4 IP ADDRESS GEO OBJECT
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv4: "geography"
    country: "usa"
    name: "ansible_geo"
    comment: "Created by Ansible"

- name: ADD IPv6 ADDRESS
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv6: "ip"
    ipv6addr: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    name: "ansible_v6Obj"
    comment: "Created by Ansible"

- name: ADD IPv6 ADDRESS RANGE
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv6: "iprange"
    start_ip: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    end_ip: "2001:0db8:85a3:0000:0000:8a2e:0370:7446"
    name: "ansible_v6range"
    comment: "Created by Ansible"

- name: ADD IPv4 IP ADDRESS GROUP
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv4: "group"
    group_name: "ansibleIPv4Group"
    group_members: "ansible_fqdn, ansible_wildcard, ansible_range"

- name: ADD IPv6 IP ADDRESS GROUP
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ipv6: "group"
    group_name: "ansibleIPv6Group"
    group_members: "ansible_v6Obj, ansible_v6range"

- name: ADD MULTICAST RANGE
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    multicast: "multicastrange"
    start_ip: "224.0.0.251"
    end_ip: "224.0.0.251"
    name: "ansible_multicastrange"
    comment: "Created by Ansible"

- name: ADD BROADCAST SUBNET
  fmgr_fwobj_address:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    multicast: "broadcastmask"
    ipv4addr: "10.7.220.0/24"
    name: "ansible_broadcastSubnet"
    comment: "Created by Ansible"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""


import re
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager


# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


def fmgr_fwobj_tags(fmg, adom, tag):
    """
    This method sets tag objects so they can be used below
    """
    # GET RID OF ANY WHITESPACE
    tag = tag.strip()

    datagram = {
        "name": tag
    }

    url = '/pm/config/adom/{adom}/obj/system/object-tag'.format(adom=adom)
    response = fmg.set(url, datagram)

    return response


def fmgr_fwobj_ipv4(fmg, paramgram):
    """
    This method sets a ipv4 address object
    """
    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if paramgram["mode"] in ['set', 'add']:
        # CREATE THE DATAGRAM DICTIONARY
        # ENSURE THE DATAGRAM KEYS MATCH THE JSON API GUIDE ATTRIBUTES, NOT WHAT IS IN ANSIBLE
        # SOME PARAMETERS SHOWN IN THIS DICTIONARY WE DON'T EVEN ASK THE USER FOR IN PLAYBOOKS BUT ARE REQUIRED
        datagram = {
            "comment": paramgram["comment"],
            "associated-interface": paramgram["associated-interface"],
            "cache-ttl": paramgram["cache-ttl"],
            "name": paramgram["name"],
            "allow-routing": paramgram["allow-routing"],
            "color": paramgram["color"],
            "meta fields": {},
            "dynamic_mapping": [],
            "visibility": paramgram["allow-routing"],
            "type": paramgram["ipv4"],
        }

        # # PROCESS TAGS
        # if paramgram["tags"] is not None:
        #     tag_list = []
        #     for tag in paramgram["tags"].split(","):
        #         tag = tag.strip()
        #         tag_list.append(tag)
        #     datagram["tags"] = tag_list

        # SET THE CORRECT URL BASED ON THE TYPE (WE'RE DOING GROUPS IN THIS METHOD, TOO)
        if datagram["type"] == "group":
            url = '/pm/config/adom/{adom}/obj/firewall/addrgrp'.format(adom=paramgram["adom"])
        else:
            url = '/pm/config/adom/{adom}/obj/firewall/address'.format(adom=paramgram["adom"])

        #########################
        # IF type = 'ipmask'
        #########################
        if datagram["type"] == "ipmask":
            # CREATE THE SUBNET LIST OBJECT
            subnet = []
            # EVAL THE IPV4ADDR INPUT AND SPLIT THE IP ADDRESS FROM THE MASK AND APPEND THEM TO THE SUBNET LIST
            for subnets in paramgram["ipv4addr"].split("/"):
                subnet.append(subnets)

            # CHECK THAT THE SECOND ENTRY IN THE SUBNET LIST (WHAT WAS TO THE RIGHT OF THE / CHARACTER)
            # IS IN SUBNET MASK FORMAT AND NOT CIDR FORMAT.
            # IF IT IS IN CIDR FORMAT, WE NEED TO CONVERT IT TO SUBNET BIT MASK FORMAT FOR THE JSON API
            if not re.match(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', subnet[1]):
                # IF THE SUBNET PARAMETER INPUT DIDN'T LOOK LIKE xxx.xxx.xxx.xxx TO REGEX...
                # ... RUN IT THROUGH THE CIDR_TO_NETMASK() FUNCTION
                mask = fmgr_cidr_to_netmask(subnet[1])
                # AND THEN UPDATE THE SUBNET LIST OBJECT
                subnet[1] = mask

            # INCLUDE THE SUBNET LIST OBJECT IN THE DATAGRAM DICTIONARY TO BE SUBMITTED
            datagram["subnet"] = subnet

        #########################
        # IF type = 'iprange'
        #########################
        if datagram["type"] == "iprange":
            datagram["start-ip"] = paramgram["start-ip"]
            datagram["end-ip"] = paramgram["end-ip"]
            datagram["subnet"] = ["0.0.0.0", "0.0.0.0"]

        #########################
        # IF type = 'geography'
        #########################
        if datagram["type"] == "geography":
            datagram["country"] = paramgram["country"]

        #########################
        # IF type = 'wildcard'
        #########################
        if datagram["type"] == "wildcard":

            subnet = []
            for subnets in paramgram["wildcard"].split("/"):
                subnet.append(subnets)

            if not re.match(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', subnet[1]):
                mask = fmgr_cidr_to_netmask(subnet[1])
                subnet[1] = mask

            datagram["wildcard"] = subnet

        #########################
        # IF type = 'wildcard-fqdn'
        #########################
        if datagram["type"] == "wildcard-fqdn":
            datagram["wildcard-fqdn"] = paramgram["wildcard-fqdn"]

        #########################
        # IF type = 'fqdn'
        #########################
        if datagram["type"] == "fqdn":
            datagram["fqdn"] = paramgram["fqdn"]

        #########################
        # IF type = 'group'
        #########################
        if datagram["type"] == "group":
            datagram = {
                "comment": paramgram["comment"],
                "name": paramgram["group_name"],
                "color": paramgram["color"],
                "meta fields": {},
                "dynamic_mapping": [],
                "visibility": paramgram["visibility"]
            }

            # PROCESS TAGS
            # if paramgram["tags"] is not None:
            #     tag_list = []
            #     for tag in paramgram["tags"].split(","):
            #         tag = tag.strip()
            #         tag_list.append(tag)
            #     datagram["tags"] = tag_list

            members = []
            group_members = paramgram["group_members"].replace(" ", "")
            try:
                for member in group_members.split(","):
                    members.append(member)
            except Exception:
                pass

            datagram["member"] = members

    # EVAL THE MODE PARAMETER FOR DELETE
    if paramgram["mode"] == "delete":
        # IF A GROUP, SET THE CORRECT NAME AND URL FOR THE GROUP ENDPOINT
        if paramgram["ipv4"] == "group":
            datagram = {}
            url = '/pm/config/adom/{adom}/obj/firewall/addrgrp/{name}'.format(adom=paramgram["adom"],
                                                                              name=paramgram["group_name"])
        # OTHERWISE WE'RE JUST GOING TO USE THE ADDRESS ENDPOINT
        else:
            datagram = {}
            url = '/pm/config/adom/{adom}/obj/firewall/address/{name}'.format(adom=paramgram["adom"],
                                                                              name=paramgram["name"])

    # IF MODE = SET -- USE THE 'SET' API CALL MODE
    if paramgram["mode"] == "set":
        response = fmg.set(url, datagram)
        return response
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    if paramgram["mode"] == "add":
        response = fmg.add(url, datagram)
        return response
    # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    if paramgram["mode"] == "delete":
        response = fmg.delete(url, datagram)
        return response


def fmgr_fwobj_ipv6(fmg, paramgram):
    """
    This method sets a ipv6 address object
    """
    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if paramgram["mode"] in ['set', 'add']:
        # CREATE THE DATAGRAM DICTIONARY
        # ENSURE THE DATAGRAM KEYS MATCH THE JSON API GUIDE ATTRIBUTES, NOT WHAT IS IN ANSIBLE
        # SOME PARAMETERS SHOWN IN THIS DICTIONARY WE DON'T EVEN ASK THE USER FOR IN PLAYBOOKS BUT ARE REQUIRED
        datagram = {
            "comment": paramgram["comment"],
            "name": paramgram["name"],
            "color": paramgram["color"],
            "dynamic_mapping": [],
            "visibility": paramgram["visibility"],
            "type": paramgram["ipv6"]
        }

        # PROCESS TAGS
        # if paramgram["tags"] is not None:
        #     tag_list = []
        #     for tag in paramgram["tags"].split(","):
        #         tag = tag.strip()
        #         tag_list.append(tag)
        #     datagram["tags"] = tag_list

        # SET THE CORRECT URL BASED ON THE TYPE (WE'RE DOING GROUPS IN THIS METHOD, TOO)
        if datagram["type"] == "group":
            url = '/pm/config/adom/{adom}/obj/firewall/addrgrp6'.format(adom=paramgram["adom"])
        else:
            url = '/pm/config/adom/{adom}/obj/firewall/address6'.format(adom=paramgram["adom"])

        #########################
        # IF type = 'ip'
        #########################
        if datagram["type"] == "ip":
            datagram["type"] = "ipprefix"
            datagram["ip6"] = paramgram["ipv6addr"]

        #########################
        # IF type = 'iprange'
        #########################
        if datagram["type"] == "iprange":
            datagram["start-ip"] = paramgram["start-ip"]
            datagram["end-ip"] = paramgram["end-ip"]

        #########################
        # IF type = 'group'
        #########################
        if datagram["type"] == "group":
            datagram = None
            datagram = {
                "comment": paramgram["comment"],
                "name": paramgram["group_name"],
                "color": paramgram["color"],
                "visibility": paramgram["visibility"]
            }

            # PROCESS TAGS
            # if paramgram["tags"] is not None:
            #     tag_list = []
            #     for tag in paramgram["tags"].split(","):
            #         tag = tag.strip()
            #         tag_list.append(tag)
            #     datagram["tags"] = tag_list

            members = []
            group_members = paramgram["group_members"].replace(" ", "")
            try:
                for member in group_members.split(","):
                    members.append(member)
            except Exception:
                pass

            datagram["member"] = members

    # EVAL THE MODE PARAMETER FOR DELETE
    if paramgram["mode"] == "delete":
        # IF A GROUP, SET THE CORRECT NAME AND URL FOR THE GROUP ENDPOINT
        if paramgram["ipv6"] == "group":
            datagram = {}
            url = '/pm/config/adom/{adom}/obj/firewall/addrgrp6/{name}'.format(adom=paramgram["adom"],
                                                                               name=paramgram["group_name"])
        # OTHERWISE WE'RE JUST GOING TO USE THE ADDRESS ENDPOINT
        else:
            datagram = {}
            url = '/pm/config/adom/{adom}/obj/firewall/address6/{name}'.format(adom=paramgram["adom"],
                                                                               name=paramgram["name"])

    # IF MODE = SET -- USE THE 'SET' API CALL MODE
    if paramgram["mode"] == "set":
        response = fmg.set(url, datagram)
        return response
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    if paramgram["mode"] == "add":
        response = fmg.add(url, datagram)
        return response
    # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    if paramgram["mode"] == "delete":
        response = fmg.delete(url, datagram)
        return response


def fmgr_fwobj_multicast(fmg, paramgram):
    """
    This method sets a multicast address object (ipv4 only as of this version).
    """
    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if paramgram["mode"] in ['set', 'add']:
        # CREATE THE DATAGRAM DICTIONARY
        # ENSURE THE DATAGRAM KEYS MATCH THE JSON API GUIDE ATTRIBUTES, NOT WHAT IS IN ANSIBLE
        # SOME PARAMETERS SHOWN IN THIS DICTIONARY WE DON'T EVEN ASK THE USER FOR IN PLAYBOOKS BUT ARE REQUIRED
        datagram = {
            "associated-interface": paramgram["associated-interface"],
            "comment": paramgram["comment"],
            "name": paramgram["name"],
            "color": paramgram["color"],
            "type": paramgram["multicast"],
            "visibility": paramgram["visibility"],
        }

        # # PROCESS TAGS
        # if paramgram["tags"] is not None:
        #     tag_list = []
        #     for tag in paramgram["tags"].split(","):
        #         tag = tag.strip()
        #         tag_list.append(tag)
        #     datagram["tags"] = tag_list

        # SET THE CORRECT URL
        url = '/pm/config/adom/{adom}/obj/firewall/multicast-address'.format(adom=paramgram["adom"])

        #########################
        # IF type = 'multicastrange'
        #########################
        if paramgram["multicast"] == "multicastrange":
            datagram["start-ip"] = paramgram["start-ip"]
            datagram["end-ip"] = paramgram["end-ip"]
            datagram["subnet"] = ["0.0.0.0", "0.0.0.0"]

        #########################
        # IF type = 'broadcastmask'
        #########################
        if paramgram["multicast"] == "broadcastmask":
            # EVAL THE IPV4ADDR INPUT AND SPLIT THE IP ADDRESS FROM THE MASK AND APPEND THEM TO THE SUBNET LIST
            subnet = []
            for subnets in paramgram["ipv4addr"].split("/"):
                subnet.append(subnets)
            # CHECK THAT THE SECOND ENTRY IN THE SUBNET LIST (WHAT WAS TO THE RIGHT OF THE / CHARACTER)
            # IS IN SUBNET MASK FORMAT AND NOT CIDR FORMAT.
            # IF IT IS IN CIDR FORMAT, WE NEED TO CONVERT IT TO SUBNET BIT MASK FORMAT FOR THE JSON API
            if not re.match(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', subnet[1]):
                # IF THE SUBNET PARAMETER INPUT DIDN'T LOOK LIKE 255.255.255.255 TO REGEX...
                # ... RUN IT THROUGH THE fmgr_cidr_to_netmask() FUNCTION
                mask = fmgr_cidr_to_netmask(subnet[1])
                # AND THEN UPDATE THE SUBNET LIST OBJECT
                subnet[1] = mask

            # INCLUDE THE SUBNET LIST OBJECT IN THE DATAGRAM DICTIONARY TO BE SUBMITTED
            datagram["subnet"] = subnet

    # EVAL THE MODE PARAMETER FOR DELETE
    if paramgram["mode"] == "delete":
        datagram = {
            "name": paramgram["name"]
        }
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/firewall/multicast-address/{name}'.format(adom=paramgram["adom"],
                                                                                    name=paramgram["name"])

    # IF MODE = SET -- USE THE 'SET' API CALL MODE
    if paramgram["mode"] == "set":
        response = fmg.set(url, datagram)
        return response
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    if paramgram["mode"] == "add":
        response = fmg.add(url, datagram)
        return response
    # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    if paramgram["mode"] == "delete":
        response = fmg.delete(url, datagram)
        return response


# ADDITIONAL COMMON FUNCTIONS
# FUNCTION/METHOD FOR LOGGING OUT AND ANALYZING ERROR CODES
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """

    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except Exception:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except Exception:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

            if results[0] not in good_codes:
                if logout_on_fail:
                    fmg.logout()
                    module.fail_json(msg=msg, **results[1])
                else:
                    return_msg = msg + " -- LOGOUT ON FAIL IS OFF, MOVING ON"
                    return return_msg
            else:
                if logout_on_success:
                    fmg.logout()
                    module.exit_json(msg=msg, **results[1])
                else:
                    return_msg = msg + " -- LOGOUT ON SUCCESS IS OFF, MOVING ON TO REST OF CODE"
                    return return_msg


# FUNCTION/METHOD FOR CONVERTING CIDR TO A NETMASK
# DID NOT USE IP ADDRESS MODULE TO KEEP INCLUDES TO A MINIMUM
def fmgr_cidr_to_netmask(cidr):
    cidr = int(cidr)
    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    return(str((0xff000000 & mask) >> 24) + '.' +
           str((0x00ff0000 & mask) >> 16) + '.' +
           str((0x0000ff00 & mask) >> 8) + '.' +
           str((0x000000ff & mask)))


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True),
        mode=dict(choices=["add", "set", "delete"], type="str", default="add"),

        allow_routing=dict(required=False, type="str", choices=['enable', 'disable']),
        associated_interface=dict(required=False, type="str"),
        cache_ttl=dict(required=False, type="str"),
        color=dict(required=False, type="str"),
        comment=dict(required=False, type="str"),
        country=dict(required=False, type="str"),
        fqdn=dict(required=False, type="str"),
        name=dict(required=False, type="str"),
        start_ip=dict(required=False, type="str"),
        end_ip=dict(required=False, type="str"),
        ipv4=dict(required=False, type="str", choices=['ipmask', 'iprange', 'fqdn', 'wildcard',
                                                       'geography', 'wildcard-fqdn', 'group']),
        visibility=dict(required=False, type="str", choices=['enable', 'disable']),
        wildcard=dict(required=False, type="str"),
        wildcard_fqdn=dict(required=False, type="str"),
        ipv6=dict(required=False, type="str", choices=['ip', 'iprange', 'group']),
        group_members=dict(required=False, type="str"),
        group_name=dict(required=False, type="str"),
        ipv4addr=dict(required=False, type="str"),
        ipv6addr=dict(required=False, type="str"),
        multicast=dict(required=False, type="str", choices=['multicastrange', 'broadcastmask', 'ip6']),
        obj_id=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False, )

    # CHECK IF THE HOST/USERNAME/PW EXISTS, AND IF IT DOES, LOGIN.
    host = module.params["host"]
    password = module.params["password"]
    username = module.params["username"]
    if host is None or username is None:
        module.fail_json(msg="Host and username are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])

    try:
        response = fmg.login()
        if response[1]['status']['code'] != 0:
            module.fail_json(msg="Connection to FortiManager Failed")
    except Exception:
        module.fail_json(msg="Connection to FortiManager Failed")
    else:
        # START SESSION LOGIC
        # MODULE PARAMGRAM
        paramgram = {
            "adom": module.params["adom"],
            "allow-routing": module.params["allow_routing"],
            "associated-interface": module.params["associated_interface"],
            "cache-ttl": module.params["cache_ttl"],
            "color": module.params["color"],
            "comment": module.params["comment"],
            "country": module.params["country"],
            "end-ip": module.params["end_ip"],
            "fqdn": module.params["fqdn"],
            "name": module.params["name"],
            "start-ip": module.params["start_ip"],
            "visibility": module.params["visibility"],
            "wildcard": module.params["wildcard"],
            "wildcard-fqdn": module.params["wildcard_fqdn"],
            "ipv6": module.params["ipv6"],
            "ipv4": module.params["ipv4"],
            "group_members": module.params["group_members"],
            "group_name": module.params["group_name"],
            "ipv4addr": module.params["ipv4addr"],
            "ipv6addr": module.params["ipv6addr"],
            "multicast": module.params["multicast"],
            "mode": module.params["mode"],
            "obj-id": module.params["obj_id"],
        }

        if paramgram["adom"] is None:
            paramgram["adom"] = "root"
        if paramgram["mode"] is None:
            paramgram["mode"] = "add"
        if paramgram["color"] is None:
            paramgram["color"] = 22
        if paramgram["comment"] is None:
            paramgram["comment"] = "Created by Ansible"
        if paramgram["allow-routing"] is None:
            paramgram["allow-routing"] = "disable"
        if paramgram["visibility"] is None:
            paramgram["visibility"] = "enable"

        if paramgram["ipv4"] is not None and paramgram["ipv6"] is None and paramgram["multicast"] is None:
            # PROCESS IPv4
            results = fmgr_fwobj_ipv4(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -2, -3])

        if paramgram["ipv4"] is None and paramgram["ipv6"] is not None and paramgram["multicast"] is None:
            # PROCESS IPv6
            results = fmgr_fwobj_ipv6(fmg, paramgram)
            if results[0] not in [0, -2, -3]:
                module.fail_json(msg="Failed to process IPv6 Object", **results[1])

        if paramgram["ipv4"] is None and paramgram["ipv6"] is None and paramgram["multicast"] is not None:
            # PROCESS MULTICAST
            results = fmgr_fwobj_multicast(fmg, paramgram)
            if results[0] not in [0, -2, -3]:
                module.fail_json(msg="Failed to process Multicast Object", **results[1])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="Couldn't find a proper ipv4 or ipv6 or multicast parameter "
                                    "to run in the logic tree. Exiting...")


if __name__ == "__main__":
    main()
