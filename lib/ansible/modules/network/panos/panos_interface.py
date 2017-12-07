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
module: panos_interface
short_description: configure data-port network interface for DHCP
description:
    - Configure data-port (DP) network interface for DHCP. By default DP interfaces are static.
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.python.org/pypi/pan-python)
notes:
    - Checkmode is not supported.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device being configured.
        required: true
    username:
        description:
            - Username credentials to use for auth.
        default: "admin"
    password:
        description:
            - Password credentials to use for auth.
        required: true
    if_name:
        description:
            - Name of the interface to configure.
        required: true
    zone_name:
        description: >
            Name of the zone for the interface. If the zone does not exist it is created but if the zone exists and
            it is not of the layer3 type the operation will fail.
        required: true
    create_default_route:
        description:
            - Whether or not to add default route with router learned via DHCP.
        default: "false"
    commit:
        description:
            - Commit if changed
        default: true
'''

EXAMPLES = '''
- name: enable DHCP client on ethernet1/1 in zone public
  interface:
    password: "admin"
    ip_address: "192.168.1.1"
    if_name: "ethernet1/1"
    zone_name: "public"
    create_default_route: "yes"
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

_IF_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
            "/network/interface/ethernet/entry[@name='%s']"

_ZONE_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
              "/vsys/entry/zone/entry"
_ZONE_XPATH_QUERY = _ZONE_XPATH + "[network/layer3/member/text()='%s']"
_ZONE_XPATH_IF = _ZONE_XPATH + "[@name='%s']/network/layer3/member[text()='%s']"
_VR_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
            "/network/virtual-router/entry"


def add_dhcp_if(xapi, if_name, zone_name, create_default_route):
    if_xml = [
        '<entry name="%s">',
        '<layer3>',
        '<dhcp-client>',
        '<create-default-route>%s</create-default-route>',
        '</dhcp-client>'
        '</layer3>'
        '</entry>'
    ]
    cdr = 'yes'
    if not create_default_route:
        cdr = 'no'
    if_xml = (''.join(if_xml)) % (if_name, cdr)
    xapi.edit(xpath=_IF_XPATH % if_name, element=if_xml)

    xapi.set(xpath=_ZONE_XPATH + "[@name='%s']/network/layer3" % zone_name,
             element='<member>%s</member>' % if_name)
    xapi.set(xpath=_VR_XPATH + "[@name='default']/interface",
             element='<member>%s</member>' % if_name)

    return True


def if_exists(xapi, if_name):
    xpath = _IF_XPATH % if_name
    xapi.get(xpath=xpath)
    network = xapi.element_root.find('.//layer3')
    return (network is not None)


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        if_name=dict(required=True),
        zone_name=dict(required=True),
        create_default_route=dict(type='bool', default=False),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    if_name = module.params['if_name']
    zone_name = module.params['zone_name']
    create_default_route = module.params['create_default_route']
    commit = module.params['commit']

    ifexists = if_exists(xapi, if_name)

    if ifexists:
        module.exit_json(changed=False, msg="interface exists, not changed")

    try:
        changed = add_dhcp_if(xapi, if_name, zone_name, create_default_route)
    except PanXapiError:
        exc = get_exception()
        module.fail_json(msg=exc.message)

    if changed and commit:
        xapi.commit(cmd="<commit></commit>", sync=True, interval=1)

    module.exit_json(changed=changed, msg="okey dokey")

if __name__ == '__main__':
    main()
