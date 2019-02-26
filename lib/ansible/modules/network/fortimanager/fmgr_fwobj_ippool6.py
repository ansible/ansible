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
module: fmgr_fwobj_ippool6
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Allows the editing of IP Pool Objects within FortiManager.
description:
  -  Allows users to add/edit/delete IPv6 Pool Objects.

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

  startip:
    description:
      - First IPv6 address (inclusive) in the range for the address pool.
    required: false

  name:
    description:
      - IPv6 IP pool name.
    required: false

  endip:
    description:
      - Final IPv6 address (inclusive) in the range for the address pool.
    required: false

  comments:
    description:
      - Comment.
    required: false

  dynamic_mapping:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  dynamic_mapping_comments:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_endip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_startip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false


'''

EXAMPLES = '''
- name: ADD FMGR_FIREWALL_IPPOOL6
  fmgr_firewall_ippool6:
    mode: "add"
    adom: "ansible"
    startip:
    name: "IPv6 IPPool"
    endip:
    comments: "Created by Ansible"

- name: DELETE FMGR_FIREWALL_IPPOOL6
  fmgr_firewall_ippool6:
    mode: "delete"
    adom: "ansible"
    name: "IPv6 IPPool"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict


def fmgr_fwobj_ippool6_modify(fmgr, paramgram):
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
        url = '/pm/config/adom/{adom}/obj/firewall/ippool6'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/firewall/ippool6/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),
        startip=dict(required=False, type="str"),
        name=dict(required=False, type="str"),
        endip=dict(required=False, type="str"),
        comments=dict(required=False, type="str"),
        dynamic_mapping=dict(required=False, type="list"),
        dynamic_mapping_comments=dict(required=False, type="str"),
        dynamic_mapping_endip=dict(required=False, type="str"),
        dynamic_mapping_startip=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "startip": module.params["startip"],
        "name": module.params["name"],
        "endip": module.params["endip"],
        "comments": module.params["comments"],
        "dynamic_mapping": {
            "comments": module.params["dynamic_mapping_comments"],
            "endip": module.params["dynamic_mapping_endip"],
            "startip": module.params["dynamic_mapping_startip"],
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

    results = DEFAULT_RESULT_OBJ

    try:
        results = fmgr_fwobj_ippool6_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
