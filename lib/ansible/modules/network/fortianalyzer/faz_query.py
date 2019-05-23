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
module: faz_query
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author: Luke Weighall (@lweighall)
short_description: Query FortiAnalyzer data objects for use in Ansible workflows.
description:
  - Provides information on data objects within FortiAnalyzer so that playbooks can perform conditionals.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  object:
    description:
      - The data object we wish to query (device, package, rule, etc). Will expand choices as improves.
    required: true
    choices:
    - device
    - cluster_nodes
    - task
    - custom

  custom_endpoint:
    description:
        - ADVANCED USERS ONLY! REQUIRES KNOWLEDGE OF FAZ JSON API!
        - The HTTP Endpoint on FortiAnalyzer you wish to GET from.
    required: false

  custom_dict:
    description:
        - ADVANCED USERS ONLY! REQUIRES KNOWLEDGE OF FAZ JSON API!
        - DICTIONARY JSON FORMAT ONLY -- Custom dictionary/datagram to send to the endpoint.
    required: false

  device_ip:
    description:
      - The IP of the device you want to query.
    required: false

  device_unique_name:
    description:
      - The desired "friendly" name of the device you want to query.
    required: false

  device_serial:
    description:
      - The serial number of the device you want to query.
    required: false

  task_id:
    description:
      - The ID of the task you wish to query status on. If left blank and object = 'task' a list of tasks are returned.
    required: false

  nodes:
    description:
      - A LIST of firewalls in the cluster you want to verify i.e. ["firewall_A","firewall_B"].
    required: false
'''


EXAMPLES = '''
- name: GET STATUS OF TASK ID
  faz_query:
    adom: "ansible"
    object: "task"
    task_id: "3"

- name: USE CUSTOM TYPE TO QUERY AVAILABLE SCRIPTS
  faz_query:
    adom: "ansible"
    object: "custom"
    custom_endpoint: "/dvmdb/adom/ansible/script"
    custom_dict: { "type": "cli" }
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortianalyzer.fortianalyzer import FortiAnalyzerHandler
from ansible.module_utils.network.fortianalyzer.common import FAZBaseException
from ansible.module_utils.network.fortianalyzer.common import FAZCommon
from ansible.module_utils.network.fortianalyzer.common import FAZMethods
from ansible.module_utils.network.fortianalyzer.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortianalyzer.common import FAIL_SOCKET_MSG


def faz_get_custom(faz, paramgram):
    """
    :param faz: The faz object instance from fortianalyzer.py
    :type faz: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiAnalyzer
    :rtype: dict
    """
    # IF THE CUSTOM DICTIONARY (OFTEN CONTAINING FILTERS) IS DEFINED CREATED THAT
    if paramgram["custom_dict"] is not None:
        datagram = paramgram["custom_dict"]
    else:
        datagram = dict()

    # SET THE CUSTOM ENDPOINT PROVIDED
    url = paramgram["custom_endpoint"]
    # MAKE THE CALL AND RETURN RESULTS
    response = faz.process_request(url, datagram, FAZMethods.GET)
    return response


def faz_get_task_status(faz, paramgram):
    """
    :param faz: The faz object instance from fortianalyzer.py
    :type faz: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiAnalyzer
    :rtype: dict
    """
    # IF THE TASK_ID IS DEFINED, THEN GET THAT SPECIFIC TASK
    # OTHERWISE, GET ALL RECENT TASKS IN A LIST
    if paramgram["task_id"] is not None:

        datagram = {
            "adom": paramgram["adom"]
        }
        url = '/task/task/{task_id}'.format(task_id=paramgram["task_id"])
        response = faz.process_request(url, datagram, FAZMethods.GET)
    else:
        datagram = {
            "adom": paramgram["adom"]
        }
        url = '/task/task'
        response = faz.process_request(url, datagram, FAZMethods.GET)
    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        object=dict(required=True, type="str", choices=["task", "custom"]),
        custom_endpoint=dict(required=False, type="str"),
        custom_dict=dict(required=False, type="dict"),
        task_id=dict(required=False, type="str")
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    paramgram = {
        "adom": module.params["adom"],
        "object": module.params["object"],
        "task_id": module.params["task_id"],
        "custom_endpoint": module.params["custom_endpoint"],
        "custom_dict": module.params["custom_dict"]
    }
    module.paramgram = paramgram
    faz = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        faz = FortiAnalyzerHandler(connection, module)
        faz.tools = FAZCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    results = DEFAULT_RESULT_OBJ

    try:
        # IF OBJECT IS TASK
        if paramgram["object"] == "task":
            results = faz_get_task_status(faz, paramgram)
            if results[0] != 0:
                module.fail_json(**results[1])
            if results[0] == 0:
                module.exit_json(**results[1])
    except Exception as err:
        raise FAZBaseException(err)

    try:
        # IF OBJECT IS CUSTOM
        if paramgram["object"] == "custom":
            results = faz_get_custom(faz, paramgram)
            if results[0] != 0:
                module.fail_json(msg="QUERY FAILED -- Please check syntax check JSON guide if needed.")
            if results[0] == 0:
                results_len = len(results[1])
                if results_len > 0:
                    results_combine = dict()
                    if isinstance(results[1], dict):
                        results_combine["results"] = results[1]
                    if isinstance(results[1], list):
                        results_combine["results"] = results[1][0:results_len]
                    module.exit_json(msg="Custom Query Success", **results_combine)
                else:
                    module.exit_json(msg="NO RESULTS")
    except Exception as err:
        raise FAZBaseException(err)

    # PROCESS RESULTS
    try:
        faz.govern_response(module=module, results=results,
                            ansible_facts=faz.construct_ansible_facts(results, module.params, paramgram))
    except BaseException as err:
        raise FAZBaseException(msg="An error occurred with govern_response(). Error: " + str(err))

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
