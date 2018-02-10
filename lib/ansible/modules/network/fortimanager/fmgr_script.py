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
version_added: "2.5"
author: Andrew Welsh
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
  host:
    description:
      - The FortiManager's Address.
    required: true
  username:
    description:
      - The username to log into the FortiManager
    required: true
  password:
    description:
      - The password associated with the username account.
    required: false
  state:
    description:
      - The desired state of the specified object.
      - present - will create a script.
      - execute - execute the scipt.
      - delete - delete the script.
    required: false
    default: present
    choices: ["present", "execute", "delete"]
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
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    script_name: "TestScript"
    script_type: "cli"
    script_target: "remote_device"
    script_description: "Create by Ansible"
    script_content: "get system status"

- name: EXECUTE SCRIPT
  fmgr_script:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    script_name: "TestScript"
    state: "execute"
    script_scope: "FGT1,FGT2"

- name: DELETE SCRIPT
  fmgr_script:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    script_name: "TestScript"
    state: "delete"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: string
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


def set_script(fmg, script_name, script_type, script_content, script_desc, script_target, adom):
    """
    This method sets a script.
    """

    datagram = {
        'content': script_content,
        'desc': script_desc,
        'name': script_name,
        'target': script_target,
        'type': script_type,
    }

    url = '/dvmdb/adom/{adom}/script/'.format(adom=adom)
    response = fmg.set(url, datagram)
    return response


def delete_script(fmg, script_name, adom):
    """
    This method deletes a script.
    """

    datagram = {
        'name': script_name,
    }

    url = '/dvmdb/adom/{adom}/script/{script_name}'.format(adom=adom, script_name=script_name)
    response = fmg.delete(url, datagram)
    return response


def execute_script(fmg, script_name, scope, package, adom, vdom):
    """
    This method will execute a specific script.
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

    url = '/dvmdb/adom/{adom}/script/execute'.format(adom=adom)
    response = fmg.execute(url, datagram)
    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str"),
        vdom=dict(required=False, type="str"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
        state=dict(choices=["execute", "delete", "present"], type="str"),

        script_name=dict(required=True, type="str"),
        script_type=dict(required=False, type="str"),
        script_target=dict(required=False, type="str"),
        script_description=dict(required=False, type="str"),
        script_content=dict(required=False, type="str"),
        script_scope=dict(required=False, type="str"),
        script_package=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True,)

    # check if params are set
    if module.params["host"] is None or module.params["username"] is None:
        module.fail_json(msg="Host and username are required for connection")

    # check if login failed
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()

    if "FortiManager instance connnected" not in str(response):
        module.fail_json(msg="Connection to FortiManager Failed")
    else:
        adom = module.params["adom"]
        if adom is None:
            adom = "root"
        vdom = module.params["vdom"]
        if vdom is None:
            vdom = "root"
        state = module.params["state"]
        if state is None:
            state = "present"

        script_name = module.params["script_name"]
        script_type = module.params["script_type"]
        script_target = module.params["script_target"]
        script_description = module.params["script_description"]
        script_content = module.params["script_content"]
        script_scope = module.params["script_scope"]
        script_package = module.params["script_package"]

        # if state is present (default), then add the script
        if state == "present":
            results = set_script(fmg, script_name, script_type, script_content, script_description, script_target, adom)
            if not results[0] == 0:
                if isinstance(results[1], list):
                    module.fail_json(msg="Adding Script Failed", **results)
                else:
                    module.fail_json(msg="Adding Script Failed")
        elif state == "execute":
            results = execute_script(fmg, script_name, script_scope, script_package, adom, vdom)
            if not results[0] == 0:
                module.fail_json(msg="Script Execution Failed", **results)
        elif state == "delete":
            results = delete_script(fmg, script_name, adom)
            if not results[0] == 0:
                module.fail_json(msg="Script Deletion Failed", **results)

        fmg.logout()

        # results is returned as a tuple
        return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
