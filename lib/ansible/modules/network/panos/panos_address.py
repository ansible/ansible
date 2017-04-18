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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: panos_address
short_description: Create address service object on PanOS devices
description:
    - Create address service object of different types [IP Range, FQDN, or IP Netmask].
author: "Luigi Mori (@jtschichold), Ken Celenza (@itdependsnetworks), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.python.org/pypi/pan-python)
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device being configured.
        required: true
    username:
        description:
            - Username credentials to use for authentication.
        default: "admin"
    password:
        description:
            - Password credentials to use for authentication.
        required: true
    address:
        description:
            - IP address with or without mask, range, or FQDN.
        required: true
        default: None
    address_name:
        description:
            - Human readable name of the address.
        required: true
        default: None
    type:
        description:
            - This is the type of the object created.
        default: ip-nemask
        choices: [ 'ip-netmask', 'fqdn', 'ip-range' ]
    description:
        description:
            - Description of the address object.
        default: None
    tag:
        description:
            - Tag of the address object.
        default: None
    commit:
        description:
            - Commit configuration to the Firewall if it is changed.
        default: true
'''

EXAMPLES = '''
- name: create IP-Netmask Object
  panos_address:
    ip_address: "192.168.1.1"
    password: 'admin'
    address_name: 'google_dns'
    address: '8.8.8.8/32'
    description: 'Google DNS'
    tag: 'Outbound'
    commit: False

- name: create IP-Range Object
  panos_address:
    ip_address: "192.168.1.1"
    password: 'admin'
    type: 'ip-range'
    address_name: 'apple-range'
    address: '17.0.0.0-17.255.255.255'
    commit: False

- name: create FQDN Object
  panos_address:
    ip_address: "192.168.1.1"
    password: 'admin'
    type: 'fqdn'
    address_name: 'google.com'
    address: 'www.google.com'
'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception

try:
    import pan.xapi
    from pan.xapi import PanXapiError

    HAS_LIB = True
except ImportError:
    HAS_LIB = False

_ADDRESS_XPATH = "/config/devices/entry[@name='localhost.localdomain']" + \
                 "/vsys/entry[@name='vsys1']" + \
                 "/address/entry[@name='%s']"


def address_exists(xapi, address_name):
    xapi.get(_ADDRESS_XPATH % address_name)
    e = xapi.element_root.find('.//entry')
    if e is None:
        return False
    return True


def add_address(xapi, module, address, address_name, description, type, tag):
    if address_exists(xapi, address_name):
        return False

    exml = []
    exml.append('<%s>' % type)
    exml.append('%s' % address)
    exml.append('</%s>' % type)

    if description:
        exml.append('<description>')
        exml.append('%s' % description)
        exml.append('</description>')

    if tag:
        exml.append('<tag>')
        exml.append('<member>%s</member>' % tag)
        exml.append('</tag>')

    exml = ''.join(exml)

    xapi.set(xpath=_ADDRESS_XPATH % address_name, element=exml)

    return True


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        address_name=dict(required=True),
        address=dict(),
        description=dict(),
        tag=dict(),
        type=dict(default='ip-netmask', choices=['ip-netmask', 'ip-range', 'fqdn']),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_LIB:
        module.fail_json(msg='pan-python required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    address_name = module.params['address_name']
    address = module.params['address']
    commit = module.params['commit']

    description = module.params['description']
    tag = module.params['tag']
    type = module.params['type']

    changed = False
    try:
        changed = add_address(xapi, module,
                              address,
                              address_name,
                              description,
                              type,
                              tag)
    except PanXapiError:
        exc = get_exception()
        module.fail_json(msg=exc.message)

    if changed and commit:
        xapi.commit(cmd="<commit></commit>", sync=True, interval=1)

    module.exit_json(changed=changed, msg="okey dokey")


if __name__ == '__main__':
    main()
