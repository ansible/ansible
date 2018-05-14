#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: panos_op
short_description: execute arbitrary OP commands on PANW devices (e.g. show interface all)
description: This module will allow user to pass and execute any supported OP command on the PANW device.
author: "Ivan Bojer (@ivanbojer)"
version_added: "2.5"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.org/project/pan-python/)
    - pandevice can be obtained from PyPi U(https://pypi.org/project/pandevice/)
notes:
    - Checkmode is NOT supported.
    - Panorama is NOT supported.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device or Panorama management console being configured.
        required: true
    username:
        description:
            - Username credentials to use for authentication.
        required: false
        default: "admin"
    password:
        description:
            - Password credentials to use for authentication.
        required: true
    api_key:
        description:
            - API key that can be used instead of I(username)/I(password) credentials.
    cmd:
        description:
            - The OP command to be performed.
        required: true
'''

EXAMPLES = '''
- name: show list of all interfaces
  panos_op:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    cmd: 'show interfaces all'

- name: show system info
  panos_op:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    cmd: 'show system info'
'''

RETURN = '''
stdout:
    description: output of the given OP command as JSON formatted string
    returned: success
    type: string
    sample: "{system: {app-release-date: 2017/05/01  15:09:12}}"

stdout_xml:
    description: output of the given OP command as JSON formatted string
    returned: success
    type: string
    sample: "<response status=success><result><system><hostname>fw2</hostname>"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception

try:
    import pan.xapi
    from pan.xapi import PanXapiError
    import pandevice
    from pandevice import base
    from pandevice import firewall
    from pandevice import panorama
    import xmltodict
    import json

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(no_log=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        cmd=dict(required=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['api_key', 'password']])
    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries.')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    api_key = module.params['api_key']
    cmd = module.params['cmd']

    # Create the device with the appropriate pandevice type
    device = base.PanDevice.create_from_device(ip_address, username, password, api_key=api_key)

    changed = False
    try:
        xml_output = device.op(cmd, xml=True)
        changed = True
    except PanXapiError:
        exc = get_exception()

        if 'non NULL value' in exc.message:
            # rewrap and call again
            cmd_array = cmd.split()
            cmd_array_len = len(cmd_array)
            cmd_array[cmd_array_len - 1] = '\"' + cmd_array[cmd_array_len - 1] + '\"'
            cmd2 = ' '.join(cmd_array)
            try:
                xml_output = device.op(cmd2, xml=True)
                changed = True
            except PanXapiError:
                exc = get_exception()
                module.fail_json(msg=exc.message)

    obj_dict = xmltodict.parse(xml_output)
    json_output = json.dumps(obj_dict)

    module.exit_json(changed=changed, msg="Done", stdout=json_output, stdout_xml=xml_output)


if __name__ == '__main__':
    main()
