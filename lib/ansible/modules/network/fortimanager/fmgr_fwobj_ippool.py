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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_fwobj_ippool
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Allows the editing of IP Pool Objects within FortiManager.
description:
  -  Allows users to add/edit/delete IP Pool Objects.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  type:
    description:
      - IP pool type (overload, one-to-one, fixed port range, or port block allocation).
      - choice | overload | IP addresses in the IP pool can be shared by clients.
      - choice | one-to-one | One to one mapping.
      - choice | fixed-port-range | Fixed port range.
      - choice | port-block-allocation | Port block allocation.
    required: false
    choices: ["overload", "one-to-one", "fixed-port-range", "port-block-allocation"]

  startip:
    description:
      - First IPv4 address (inclusive) in the range for the address pool (format xxx.xxx.xxx.xxx, Default| 0.0.0.0).
    required: false

  source_startip:
    description:
      -  First IPv4 address (inclusive) in the range of the source addresses to be translated (format xxx.xxx.xxx.xxx,
         Default| 0.0.0.0).
    required: false

  source_endip:
    description:
      - Final IPv4 address (inclusive) in the range of the source addresses to be translated (format xxx.xxx.xxx.xxx,
        Default| 0.0.0.0).
    required: false

  permit_any_host:
    description:
      - Enable/disable full cone NAT.
      - choice | disable | Disable full cone NAT.
      - choice | enable | Enable full cone NAT.
    required: false
    choices: ["disable", "enable"]

  pba_timeout:
    description:
      - Port block allocation timeout (seconds).
    required: false

  num_blocks_per_user:
    description:
      - Number of addresses blocks that can be used by a user (1 to 128, default = 8).
    required: false

  name:
    description:
      - IP pool name.
    required: false

  endip:
    description:
      - Final IPv4 address (inclusive) in the range for the address pool (format xxx.xxx.xxx.xxx, Default| 0.0.0.0).
    required: false

  comments:
    description:
      - Comment.
    required: false

  block_size:
    description:
      -  Number of addresses in a block (64 to 4096, default = 128).
    required: false

  associated_interface:
    description:
      - Associated interface name.
    required: false

  arp_reply:
    description:
      - Enable/disable replying to ARP requests when an IP Pool is added to a policy (default = enable).
      - choice | disable | Disable ARP reply.
      - choice | enable | Enable ARP reply.
    required: false
    choices: ["disable", "enable"]

  arp_intf:
    description:
      - Select an interface from available options that will reply to ARP requests. (If blank, any is selected).
    required: false

  dynamic_mapping:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameter.ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  dynamic_mapping_arp_intf:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_arp_reply:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_associated_interface:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_block_size:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_comments:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_endip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_num_blocks_per_user:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_pba_timeout:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_permit_any_host:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_source_endip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_source_startip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_startip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_type:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false
    choices: ["overload", "one-to-one", "fixed-port-range", "port-block-allocation"]


'''

EXAMPLES = '''
- name: ADD FMGR_FIREWALL_IPPOOL Overload
  fmgr_fwobj_ippool:
    mode: "add"
    adom: "ansible"
    name: "Ansible_pool4_overload"
    comments: "Created by ansible"
    type: "overload"

    # OPTIONS FOR ALL MODES
    startip: "10.10.10.10"
    endip: "10.10.10.100"
    arp_reply: "enable"

- name: ADD FMGR_FIREWALL_IPPOOL one-to-one
  fmgr_fwobj_ippool:
    mode: "add"
    adom: "ansible"
    name: "Ansible_pool4_121"
    comments: "Created by ansible"
    type: "one-to-one"

    # OPTIONS FOR ALL MODES
    startip: "10.10.20.10"
    endip: "10.10.20.100"
    arp_reply: "enable"

- name: ADD FMGR_FIREWALL_IPPOOL FIXED PORT RANGE
  fmgr_fwobj_ippool:
    mode: "add"
    adom: "ansible"
    name: "Ansible_pool4_fixed_port"
    comments: "Created by ansible"
    type: "fixed-port-range"

    # OPTIONS FOR ALL MODES
    startip: "10.10.40.10"
    endip: "10.10.40.100"
    arp_reply: "enable"
    # FIXED PORT RANGE OPTIONS
    source_startip: "192.168.20.1"
    source_endip: "192.168.20.20"

- name: ADD FMGR_FIREWALL_IPPOOL PORT BLOCK ALLOCATION
  fmgr_fwobj_ippool:
    mode: "add"
    adom: "ansible"
    name: "Ansible_pool4_port_block_allocation"
    comments: "Created by ansible"
    type: "port-block-allocation"

    # OPTIONS FOR ALL MODES
    startip: "10.10.30.10"
    endip: "10.10.30.100"
    arp_reply: "enable"
    # PORT BLOCK ALLOCATION OPTIONS
    block_size: "128"
    num_blocks_per_user: "1"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict


###############
# START METHODS
###############


def fmgr_fwobj_ippool_modify(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/firewall/ippool'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/firewall/ippool/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    response = fmgr.process_request(url, datagram, paramgram["mode"])

    return response


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        type=dict(required=False, type="str", choices=["overload",
                                                       "one-to-one",
                                                       "fixed-port-range",
                                                       "port-block-allocation"]),
        startip=dict(required=False, type="str"),
        source_startip=dict(required=False, type="str"),
        source_endip=dict(required=False, type="str"),
        permit_any_host=dict(required=False, type="str", choices=["disable", "enable"]),
        pba_timeout=dict(required=False, type="int"),
        num_blocks_per_user=dict(required=False, type="int"),
        name=dict(required=False, type="str"),
        endip=dict(required=False, type="str"),
        comments=dict(required=False, type="str"),
        block_size=dict(required=False, type="int"),
        associated_interface=dict(required=False, type="str"),
        arp_reply=dict(required=False, type="str", choices=["disable", "enable"]),
        arp_intf=dict(required=False, type="str"),
        dynamic_mapping=dict(required=False, type="list"),
        dynamic_mapping_arp_intf=dict(required=False, type="str"),
        dynamic_mapping_arp_reply=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_associated_interface=dict(required=False, type="str"),
        dynamic_mapping_block_size=dict(required=False, type="int"),
        dynamic_mapping_comments=dict(required=False, type="str"),
        dynamic_mapping_endip=dict(required=False, type="str"),
        dynamic_mapping_num_blocks_per_user=dict(required=False, type="int"),
        dynamic_mapping_pba_timeout=dict(required=False, type="int"),
        dynamic_mapping_permit_any_host=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_source_endip=dict(required=False, type="str"),
        dynamic_mapping_source_startip=dict(required=False, type="str"),
        dynamic_mapping_startip=dict(required=False, type="str"),
        dynamic_mapping_type=dict(required=False, type="str", choices=["overload",
                                                                       "one-to-one",
                                                                       "fixed-port-range",
                                                                       "port-block-allocation"]),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "type": module.params["type"],
        "startip": module.params["startip"],
        "source-startip": module.params["source_startip"],
        "source-endip": module.params["source_endip"],
        "permit-any-host": module.params["permit_any_host"],
        "pba-timeout": module.params["pba_timeout"],
        "num-blocks-per-user": module.params["num_blocks_per_user"],
        "name": module.params["name"],
        "endip": module.params["endip"],
        "comments": module.params["comments"],
        "block-size": module.params["block_size"],
        "associated-interface": module.params["associated_interface"],
        "arp-reply": module.params["arp_reply"],
        "arp-intf": module.params["arp_intf"],
        "dynamic_mapping": {
            "arp-intf": module.params["dynamic_mapping_arp_intf"],
            "arp-reply": module.params["dynamic_mapping_arp_reply"],
            "associated-interface": module.params["dynamic_mapping_associated_interface"],
            "block-size": module.params["dynamic_mapping_block_size"],
            "comments": module.params["dynamic_mapping_comments"],
            "endip": module.params["dynamic_mapping_endip"],
            "num-blocks-per-user": module.params["dynamic_mapping_num_blocks_per_user"],
            "pba-timeout": module.params["dynamic_mapping_pba_timeout"],
            "permit-any-host": module.params["dynamic_mapping_permit_any_host"],
            "source-endip": module.params["dynamic_mapping_source_endip"],
            "source-startip": module.params["dynamic_mapping_source_startip"],
            "startip": module.params["dynamic_mapping_startip"],
            "type": module.params["dynamic_mapping_type"],
        }
    }

    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    list_overrides = ['dynamic_mapping']
    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)
    # UPDATE THE CHANGED PARAMGRAM
    module.paramgram = paramgram

    results = DEFAULT_RESULT_OBJ
    try:
        results = fmgr_fwobj_ippool_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
