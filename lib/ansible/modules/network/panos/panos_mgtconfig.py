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
module: panos_mgtconfig
short_description: configure management settings of device
description:
    - Configure management settings of device
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python
options:
    dns_server_primary:
        description:
            - address of primary DNS server
    dns_server_secondary:
        description:
            - address of secondary DNS server
    panorama_primary:
        description:
            - address of primary Panorama server
    panorama_secondary:
        description:
            - address of secondary Panorama server
    commit:
        description:
            - commit if changed
        type: bool
        default: 'yes'
extends_documentation_fragment: panos
'''

EXAMPLES = '''
- name: set dns and panorama
  panos_mgtconfig:
    ip_address: "192.168.1.1"
    password: "admin"
    dns_server_primary: "1.1.1.1"
    dns_server_secondary: "1.1.1.2"
    panorama_primary: "1.1.1.3"
    panorama_secondary: "1.1.1.4"
'''

RETURN = '''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

try:
    import pan.xapi
    from pan.xapi import PanXapiError
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

_XPATH_DNS_SERVERS = "/config/devices/entry[@name='localhost.localdomain']" +\
                     "/deviceconfig/system/dns-setting/servers"
_XPATH_PANORAMA_SERVERS = "/config" +\
                          "/devices/entry[@name='localhost.localdomain']" +\
                          "/deviceconfig/system"


def set_dns_server(xapi, new_dns_server, primary=True):
    if primary:
        tag = "primary"
    else:
        tag = "secondary"
    xpath = _XPATH_DNS_SERVERS + "/" + tag

    # check the current element value
    xapi.get(xpath)
    val = xapi.element_root.find(".//" + tag)
    if val is not None:
        # element exists
        val = val.text
    if val == new_dns_server:
        return False

    element = "<%(tag)s>%(value)s</%(tag)s>" %\
              dict(tag=tag, value=new_dns_server)
    xapi.edit(xpath, element)

    return True


def set_panorama_server(xapi, new_panorama_server, primary=True):
    if primary:
        tag = "panorama-server"
    else:
        tag = "panorama-server-2"
    xpath = _XPATH_PANORAMA_SERVERS + "/" + tag

    # check the current element value
    xapi.get(xpath)
    val = xapi.element_root.find(".//" + tag)
    if val is not None:
        # element exists
        val = val.text
    if val == new_panorama_server:
        return False

    element = "<%(tag)s>%(value)s</%(tag)s>" %\
              dict(tag=tag, value=new_panorama_server)
    xapi.edit(xpath, element)

    return True


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        dns_server_primary=dict(),
        dns_server_secondary=dict(),
        panorama_primary=dict(),
        panorama_secondary=dict(),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    dns_server_primary = module.params['dns_server_primary']
    dns_server_secondary = module.params['dns_server_secondary']
    panorama_primary = module.params['panorama_primary']
    panorama_secondary = module.params['panorama_secondary']
    commit = module.params['commit']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    changed = False
    try:
        if dns_server_primary is not None:
            changed |= set_dns_server(xapi, dns_server_primary, primary=True)
        if dns_server_secondary is not None:
            changed |= set_dns_server(xapi, dns_server_secondary, primary=False)
        if panorama_primary is not None:
            changed |= set_panorama_server(xapi, panorama_primary, primary=True)
        if panorama_secondary is not None:
            changed |= set_panorama_server(xapi, panorama_secondary, primary=False)

        if changed and commit:
            xapi.commit(cmd="<commit></commit>", sync=True, interval=1)
    except PanXapiError as exc:
        module.fail_json(msg=to_native(exc))

    module.exit_json(changed=changed, msg="okey dokey")


if __name__ == '__main__':
    main()
