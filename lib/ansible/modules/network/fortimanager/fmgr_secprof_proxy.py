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
module: fmgr_secprof_proxy
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manage proxy security profiles in FortiManager
description:
  -  Manage proxy security profiles for FortiGates via FortiManager using the FMG API with playbooks

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

  strip_encoding:
    description:
      - Enable/disable stripping unsupported encoding from the request header.
      - choice | disable | Disable stripping of unsupported encoding from the request header.
      - choice | enable | Enable stripping of unsupported encoding from the request header.
    required: false
    choices: ["disable", "enable"]

  name:
    description:
      - Profile name.
    required: false

  log_header_change:
    description:
      - Enable/disable logging HTTP header changes.
      - choice | disable | Disable Enable/disable logging HTTP header changes.
      - choice | enable | Enable Enable/disable logging HTTP header changes.
    required: false
    choices: ["disable", "enable"]

  header_x_forwarded_for:
    description:
      - Action to take on the HTTP x-forwarded-for header in forwarded requests| forwards (pass), adds, or removes the
      -  HTTP header.
      - choice | pass | Forward the same HTTP header.
      - choice | add | Add the HTTP header.
      - choice | remove | Remove the HTTP header.
    required: false
    choices: ["pass", "add", "remove"]

  header_x_authenticated_user:
    description:
      - Action to take on the HTTP x-authenticated-user header in forwarded requests| forwards (pass), adds, or remove
      - s the HTTP header.
      - choice | pass | Forward the same HTTP header.
      - choice | add | Add the HTTP header.
      - choice | remove | Remove the HTTP header.
    required: false
    choices: ["pass", "add", "remove"]

  header_x_authenticated_groups:
    description:
      - Action to take on the HTTP x-authenticated-groups header in forwarded requests| forwards (pass), adds, or remo
      - ves the HTTP header.
      - choice | pass | Forward the same HTTP header.
      - choice | add | Add the HTTP header.
      - choice | remove | Remove the HTTP header.
    required: false
    choices: ["pass", "add", "remove"]

  header_via_response:
    description:
      - Action to take on the HTTP via header in forwarded responses| forwards (pass), adds, or removes the HTTP heade
      - r.
      - choice | pass | Forward the same HTTP header.
      - choice | add | Add the HTTP header.
      - choice | remove | Remove the HTTP header.
    required: false
    choices: ["pass", "add", "remove"]

  header_via_request:
    description:
      - Action to take on the HTTP via header in forwarded requests| forwards (pass), adds, or removes the HTTP header
      - .
      - choice | pass | Forward the same HTTP header.
      - choice | add | Add the HTTP header.
      - choice | remove | Remove the HTTP header.
    required: false
    choices: ["pass", "add", "remove"]

  header_front_end_https:
    description:
      - Action to take on the HTTP front-end-HTTPS header in forwarded requests| forwards (pass), adds, or removes the
      -  HTTP header.
      - choice | pass | Forward the same HTTP header.
      - choice | add | Add the HTTP header.
      - choice | remove | Remove the HTTP header.
    required: false
    choices: ["pass", "add", "remove"]

  header_client_ip:
    description:
      - Actions to take on the HTTP client-IP header in forwarded requests| forwards (pass), adds, or removes the HTTP
      -  header.
      - choice | pass | Forward the same HTTP header.
      - choice | add | Add the HTTP header.
      - choice | remove | Remove the HTTP header.
    required: false
    choices: ["pass", "add", "remove"]

  headers:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  headers_action:
    description:
      - Action when HTTP the header forwarded.
      - choice | add-to-request | Add the HTTP header to request.
      - choice | add-to-response | Add the HTTP header to response.
      - choice | remove-from-request | Remove the HTTP header from request.
      - choice | remove-from-response | Remove the HTTP header from response.
    required: false
    choices: ["add-to-request", "add-to-response", "remove-from-request", "remove-from-response"]

  headers_content:
    description:
      - HTTP header's content.
    required: false

  headers_name:
    description:
      - HTTP forwarded header name.
    required: false


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_proxy:
      name: "Ansible_Web_Proxy_Profile"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_proxy:
      name: "Ansible_Web_Proxy_Profile"
      mode: "set"
      header_client_ip: "pass"
      header_front_end_https: "add"
      header_via_request: "remove"
      header_via_response: "pass"
      header_x_authenticated_groups: "add"
      header_x_authenticated_user: "remove"
      strip_encoding: "enable"
      log_header_change: "enable"
      header_x_forwarded_for: "pass"
      headers_action: "add-to-request"
      headers_content: "test"
      headers_name: "test_header"
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


def fmgr_web_proxy_profile_modify(fmgr, paramgram):
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

    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/web-proxy/profile'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/web-proxy/profile/{name}'.format(adom=adom, name=paramgram["name"])
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

        strip_encoding=dict(required=False, type="str", choices=["disable", "enable"]),
        name=dict(required=False, type="str"),
        log_header_change=dict(required=False, type="str", choices=["disable", "enable"]),
        header_x_forwarded_for=dict(required=False, type="str", choices=["pass", "add", "remove"]),
        header_x_authenticated_user=dict(required=False, type="str", choices=["pass", "add", "remove"]),
        header_x_authenticated_groups=dict(required=False, type="str", choices=["pass", "add", "remove"]),
        header_via_response=dict(required=False, type="str", choices=["pass", "add", "remove"]),
        header_via_request=dict(required=False, type="str", choices=["pass", "add", "remove"]),
        header_front_end_https=dict(required=False, type="str", choices=["pass", "add", "remove"]),
        header_client_ip=dict(required=False, type="str", choices=["pass", "add", "remove"]),
        headers=dict(required=False, type="list"),
        headers_action=dict(required=False, type="str", choices=["add-to-request", "add-to-response",
                                                                 "remove-from-request", "remove-from-response"]),
        headers_content=dict(required=False, type="str"),
        headers_name=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "strip-encoding": module.params["strip_encoding"],
        "name": module.params["name"],
        "log-header-change": module.params["log_header_change"],
        "header-x-forwarded-for": module.params["header_x_forwarded_for"],
        "header-x-authenticated-user": module.params["header_x_authenticated_user"],
        "header-x-authenticated-groups": module.params["header_x_authenticated_groups"],
        "header-via-response": module.params["header_via_response"],
        "header-via-request": module.params["header_via_request"],
        "header-front-end-https": module.params["header_front_end_https"],
        "header-client-ip": module.params["header_client_ip"],
        "headers": {
            "action": module.params["headers_action"],
            "content": module.params["headers_content"],
            "name": module.params["headers_name"],
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

    list_overrides = ['headers']
    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)
    module.paramgram = paramgram

    results = DEFAULT_RESULT_OBJ
    try:
        results = fmgr_web_proxy_profile_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
