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

DOCUMENTATION = '''
---
module: panos_lic
short_description: apply authcode to a device/instance
description:
    - Apply an authcode to a device.
    - The authcode should have been previously registered on the Palo Alto Networks support portal.
    - The device should have Internet access.
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python
options:
    auth_code:
        description:
            - authcode to be applied
        required: true
    force:
        description:
            - whether to apply authcode even if device is already licensed
        required: false
        default: "false"
extends_documentation_fragment: panos
'''

EXAMPLES = '''
    - hosts: localhost
      connection: local
      tasks:
        - name: fetch license
          panos_lic:
            ip_address: "192.168.1.1"
            password: "paloalto"
            auth_code: "IBADCODE"
          register: result
    - name: Display serialnumber (if already registered)
      debug:
        var: "{{result.serialnumber}}"
'''

RETURN = '''
serialnumber:
    description: serialnumber of the device in case that it has been already registered
    returned: success
    type: string
    sample: 007200004214
'''


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule

try:
    import pan.xapi
    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def get_serial(xapi, module):
    xapi.op(cmd="show system info", cmd_xml=True)
    r = xapi.element_root
    serial = r.find('.//serial')
    if serial is None:
        module.fail_json(msg="No <serial> tag in show system info")

    serial = serial.text

    return serial


def apply_authcode(xapi, module, auth_code):
    try:
        xapi.op(cmd='request license fetch auth-code "%s"' % auth_code,
                cmd_xml=True)
    except pan.xapi.PanXapiError:
        if hasattr(xapi, 'xml_document'):
            if 'Successfully' in xapi.xml_document:
                return

        if 'Invalid Auth Code' in xapi.xml_document:
            module.fail_json(msg="Invalid Auth Code")

        raise

    return


def fetch_authcode(xapi, module):
    try:
        xapi.op(cmd='request license fetch', cmd_xml=True)
    except pan.xapi.PanXapiError:
        if hasattr(xapi, 'xml_document'):
            if 'Successfully' in xapi.xml_document:
                return

        if 'Invalid Auth Code' in xapi.xml_document:
            module.fail_json(msg="Invalid Auth Code")

        raise

    return


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        auth_code=dict(),
        username=dict(default='admin'),
        force=dict(type='bool', default=False)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    auth_code = module.params["auth_code"]
    force = module.params['force']
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    if not force:
        serialnumber = get_serial(xapi, module)
        if serialnumber != 'unknown':
            return module.exit_json(changed=False, serialnumber=serialnumber)
    if auth_code:
        apply_authcode(xapi, module, auth_code)
    else:
        fetch_authcode(xapi, module)

    module.exit_json(changed=True, msg="okey dokey")

if __name__ == '__main__':
    main()
