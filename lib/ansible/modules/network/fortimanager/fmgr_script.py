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
module: fmgr_script
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Add/Edit/Delete and execute scripts
description: Create/edit/delete scripts and execute the scripts on the FortiManager using jsonrpc API

options:
  adom:
    description:
      - The administrative domain (admon) the configuration belongs to
    required: true

  vdom:
    description:
      - The virtual domain (vdom) the configuration belongs to

  mode:
    description:
      - The desired mode of the specified object. Execute will run the script.
    required: false
    default: "add"
    choices: ["add", "delete", "execute", "set"]

  script_name:
    description:
      - The name of the script.
    required: True

  script_type:
    description:
      - The type of script (CLI or TCL).
    required: false

  script_target:
    description:
      - The target of the script to be run.
    required: false

  script_description:
    description:
      - The description of the script.
    required: false

  script_content:
    description:
      - The script content that will be executed.
    required: false

  script_scope:
    description:
      - (datasource) The devices that the script will run on, can have both device member and device group member.
    required: false

  script_package:
    description:
      - (datasource) Policy package object to run the script against
    required: false

'''

EXAMPLES = '''
- name: CREATE SCRIPT
  fmgr_script:
    adom: "root"
    script_name: "TestScript"
    script_type: "cli"
    script_target: "remote_device"
    script_description: "Create by Ansible"
    script_content: "get system status"

- name: EXECUTE SCRIPT
  fmgr_script:
    adom: "root"
    script_name: "TestScript"
    mode: "execute"
    script_scope: "FGT1,FGT2"

- name: DELETE SCRIPT
  fmgr_script:
    adom: "root"
    script_name: "TestScript"
    mode: "delete"
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
from ansible.module_utils.network.fortimanager.common import FMGRMethods
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def set_script(fmgr, script_name, script_type, script_content, script_desc, script_target, adom):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    datagram = {
        'content': script_content,
        'desc': script_desc,
        'name': script_name,
        'target': script_target,
        'type': script_type,
    }

    paramgram = {
        "script_name": script_name,
        "script_type": script_type,
        "script_content": script_content,
        "script_desc": script_desc,
        "script_target": script_target,
        "adom": adom
    }

    url = '/dvmdb/adom/{adom}/script/'.format(adom=adom)
    response = fmgr.process_request(url, datagram, paramgram, FMGRMethods.SET)
    return response


def delete_script(fmgr, script_name, adom):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    datagram = {
        'name': script_name,
    }

    paramgram = {
        "script_name": script_name,
        "adom": adom
    }

    url = '/dvmdb/adom/{adom}/script/{script_name}'.format(adom=adom, script_name=script_name)
    response = fmgr.process_request(url, datagram, paramgram, FMGRMethods.DELETE)
    return response


def execute_script(fmgr, script_name, scope, package, adom, vdom):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    scope_list = list()
    scope = scope.replace(' ', '')
    scope = scope.split(',')
    for dev_name in scope:
        scope_list.append({'name': dev_name, 'vdom': vdom})

    datagram = {
        'adom': adom,
        'script': script_name,
        'package': package,
        'scope': scope_list,
    }

    paramgram = {
        "script_name": script_name,
        "adom": adom,
        "scope": scope,
        "package": package,
        "vdom": vdom
    }

    url = '/dvmdb/adom/{adom}/script/execute'.format(adom=adom)
    response = fmgr.process_request(url, datagram, paramgram, FMGRMethods.EXEC)
    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        vdom=dict(required=False, type="str", default="root"),
        mode=dict(choices=["add", "execute", "set", "delete"], type="str", default="add"),
        script_name=dict(required=True, type="str"),
        script_type=dict(required=False, type="str"),
        script_target=dict(required=False, type="str"),
        script_description=dict(required=False, type="str"),
        script_content=dict(required=False, type="str"),
        script_scope=dict(required=False, type="str"),
        script_package=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module.check_mode)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    results = DEFAULT_RESULT_OBJ
    script_name = module.params["script_name"]
    script_type = module.params["script_type"]
    script_target = module.params["script_target"]
    script_description = module.params["script_description"]
    script_content = module.params["script_content"]
    script_scope = module.params["script_scope"]
    script_package = module.params["script_package"]
    adom = module.params["adom"]
    vdom = module.params["vdom"]
    mode = module.params["mode"]

    try:
        if mode in ['add', 'set']:
            results = set_script(fmgr, script_name, script_type, script_content,
                                 script_description, script_target, adom)
            fmgr.govern_response(module=module, results=results, msg="Operation Finished",
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, module.params))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        if mode == "execute":
            results = execute_script(fmgr, script_name, script_scope, script_package, adom, vdom)
            fmgr.govern_response(module=module, results=results, msg="Operation Finished",
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, module.params))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        if mode == "delete":
            results = delete_script(fmgr, script_name, adom)
            fmgr.govern_response(module=module, results=results, msg="Operation Finished",
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, module.params))
    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
