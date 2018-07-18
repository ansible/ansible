# -*- coding: utf-8 -*-
#
# (C) 2018 Red Hat Inc.
# Copyright (C) 2018 Western Telematic Inc.
#
# GNU General Public License v3.0+
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Module to execute CPM Status Commands on WTI OOB and PDU devices.
# CPM Networking
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: cpm_status
version_added: "2.7"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get status and parameters from WTI OOB and PDU devices
description:
    - "Get various status and parameters from WTI OOB and PDU devices"
options:
  cpm_action:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "temperature", "firmware", "status", "alarms" ]
  cpm_url:
    description:
      - This is the URL of the WTI device to send the module.
    required: true
  cpm_username:
    description:
      - This is the Username of the WTI device to send the module.
  cpm_password:
    description:
      - This is the Password of the WTI device to send the module.
  use_https:
    description:
      - Designates to use an https connection or http connection.
    required: false
    type: bool
    default: True
"""

EXAMPLES = """
# Get temperature
- name: Get the temperature of a given WTI device
  cpm_status:
    cpm_action: "temperature"
    cpm_url: "{{ansible_host}}"
    cpm_username: "{{ansible_user}}"
    cpm_password: "{{ansible_pw}}"

# Get firmware version
- name: Get the firmware version of a given WTI device
  cpm_status:
    cpm_action: "firmware"
    cpm_url: "{{ansible_host}}"
    cpm_username: "{{ansible_user}}"
    cpm_password: "{{ansible_pw}}"

# Get status output
- name: Get the status output from a given WTI device
  cpm_status:
    cpm_action: "status"
    cpm_url: "{{ansible_host}}"
    cpm_username: "{{ansible_user}}"
    cpm_password: "{{ansible_pw}}"

# Get Alarm output
- name: Get the alarms status of a given WTI device
  cpm_status:
    cpm_action: "alarms"
    cpm_url: "{{ansible_host}}"
    cpm_username: "{{ansible_user}}"
    cpm_password: "{{ansible_pw}}"
"""

RETURN = """
data:
    description: The output JSON returned from the commands sent
    returned: always
    type: str
"""

from ansible.module_utils.network.cpm.cpm_common import request
from ansible.module_utils.basic import AnsibleModule


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        cpm_action=dict(choices=['temperature', 'firmware', 'status', 'alarms'],
                   required=True),
        cpm_url=dict(type='str', required=True),
        cpm_username=dict(type='str', required=True),
        cpm_password=dict(type='str', required=True, no_log=True),
        use_https=dict(type='bool', default=True)
    )

    result = dict(
        changed=False,
        data=''
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        return result

    if module.params['use_https'] is True:
        protocol = "https://"
    else:
        protocol = "http://"

    if (module.params['cpm_action'] == 'temperature'):
        result['data'] = request(module,
        protocol + module.params['cpm_url'] + "/api/v2/status/temperature",
        module.params['cpm_username'], module.params['cpm_password'], 8)
    elif (module.params['cpm_action'] == 'firmware'):
        result['data'] = request(module,
        protocol + module.params['cpm_url'] + "/api/v2/status/firmware",
        module.params['cpm_username'], module.params['cpm_password'], 8)
    elif (module.params['cpm_action'] == 'status'):
        result['data'] = request(module,
        protocol + module.params['cpm_url'] + "/api/v2/status/status",
        module.params['cpm_username'], module.params['cpm_password'], 8)
    elif (module.params['cpm_action'] == 'alarms'):
        result['data'] = request(module,
        protocol + module.params['cpm_url'] + "/api/v2/status/alarms",
        module.params['cpm_username'], module.params['cpm_password'], 8)
    else:
        module.fail_json(msg='Status command not recognized.', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
