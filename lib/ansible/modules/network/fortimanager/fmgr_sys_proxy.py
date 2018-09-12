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
module: fmgr_sys_proxy
version_added: "2.8"
author: Andrew Welsh
short_description: Make FortiGate API calls via the FortiMananger
description:
  - The FMG proxies FOS API calls via the FMG.  Review FortiGate API documentation to ensure you are passing correct
    parameters for both the FortiManager and FortiGate

options:
  adom:
    description:
      - The administrative domain (admon) the configuration belongs to
    required: true
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

  action:
    description:
      - Specify HTTP action for the request. Either 'get' or 'post'
    required: True
  payload:
    description:
      - JSON payload of the request. The payload will be URL-encoded and becomes the "json" field in the query string for both GET and POST request.
    required: False
  resource:
    description:
      - URL on the remote device to be accessed, string
    required: True
  target:
    description:
      - FOS datasource, either device or group object
    required: True

'''

EXAMPLES = '''
- name: Proxy FOS requests via FMG
  hosts: FortiManager
  connection: local
  gather_facts: False

  tasks:

    - name: Get upgrade path for FGT1
      fmgr_provision:
        host: "{{ inventory_hostname }}"
        username: "{{ username }}"
        password: "{{ password }}"
        adom: "root"
        action: "get"
        resource: "/api/v2/monitor/system/firmware/upgrade-paths?vdom=root"
        target: ["/adom/root/device/FGT1"]
    - name: Upgrade firmware of FGT1
      fmgr_provision:
        host: "{{ inventory_hostname }}"
        username: "{{ username }}"
        password: "{{ password }}"
        adom: "root"
        action: "post"
        payload: {source: upload, file_content: b64_encoded_string, file_name: file_name}
        resource: "/api/v2/monitor/system/firmware/upgrade?vdom=vdom"
        target: ["/adom/root/device/FGT1"]

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


def fos_request(fmg, action, resource, target, payload, adom='root'):

    datagram = {
        "data": {
            # get or post
            "action": action,
            # dictionary of data
            "payload": payload,
            # FOS API URL including vdom params
            "resource": resource,
            # FMG device to make API calls to
            "target": target
        },

    }
    url = "/sys/proxy/json"

    status, response = fmg.execute(url, datagram)
    return status, response


def main():

    argument_spec = dict(
        adom=dict(required=False, type="str"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True),

        action=dict(required=False, type="str"),
        resource=dict(required=False, type="str"),
        target=dict(required=False, type="str"),
        payload=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True, )

    action = module.params["action"]
    resource = module.params["resource"]
    target = module.params["target"]
    payload = module.params["payload"]

    # check if params are set
    if module.params["host"] is None or module.params["username"] is None:
        module.fail_json(msg="Host and username are required for connection")

    # check if login failed
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()

    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")
    else:
        if module.params["adom"] is None:
            module.params["adom"] = 'root'

        status, result = fos_request(fmg, action, resource, target, payload, module.params["adom"])

        if not status == 0:
            module.fail_json(msg="Failure showing upgrade path", **result)

        fmg.logout()

        # results is returned as a tuple
        return module.exit_json(changed=True, **result)


if __name__ == "__main__":
    main()
