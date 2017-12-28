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
module: panos_pg
short_description: create a security profiles group
description:
    - Create a security profile group
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
    password:
        description:
            - password for authentication
        required: true
    username:
        description:
            - username for authentication
        required: false
        default: "admin"
    pg_name:
        description:
            - name of the security profile group
        required: true
    data_filtering:
        description:
            - name of the data filtering profile
        required: false
        default: None
    file_blocking:
        description:
            - name of the file blocking profile
        required: false
        default: None
    spyware:
        description:
            - name of the spyware profile
        required: false
        default: None
    url_filtering:
        description:
            - name of the url filtering profile
        required: false
        default: None
    virus:
        description:
            - name of the anti-virus profile
        required: false
        default: None
    vulnerability:
        description:
            - name of the vulnerability profile
        required: false
        default: None
    wildfire:
        description:
            - name of the wildfire analysis profile
        required: false
        default: None
    commit:
        description:
            - commit if changed
        required: false
        default: true
'''

EXAMPLES = '''
- name: setup security profile group
  panos_pg:
    ip_address: "192.168.1.1"
    password: "admin"
    username: "admin"
    pg_name: "pg-default"
    virus: "default"
    spyware: "default"
    vulnerability: "default"
'''

RETURN = '''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception


try:
    import pan.xapi
    from pan.xapi import PanXapiError
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

_PG_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
            "/vsys/entry[@name='vsys1']" +\
            "/profile-group/entry[@name='%s']"


def pg_exists(xapi, pg_name):
    xapi.get(_PG_XPATH % pg_name)
    e = xapi.element_root.find('.//entry')
    if e is None:
        return False
    return True


def add_pg(xapi, pg_name, data_filtering, file_blocking, spyware,
           url_filtering, virus, vulnerability, wildfire):
    if pg_exists(xapi, pg_name):
        return False

    exml = []

    if data_filtering is not None:
        exml.append('<data-filtering><member>%s</member></data-filtering>' %
                    data_filtering)
    if file_blocking is not None:
        exml.append('<file-blocking><member>%s</member></file-blocking>' %
                    file_blocking)
    if spyware is not None:
        exml.append('<spyware><member>%s</member></spyware>' %
                    spyware)
    if url_filtering is not None:
        exml.append('<url-filtering><member>%s</member></url-filtering>' %
                    url_filtering)
    if virus is not None:
        exml.append('<virus><member>%s</member></virus>' %
                    virus)
    if vulnerability is not None:
        exml.append('<vulnerability><member>%s</member></vulnerability>' %
                    vulnerability)
    if wildfire is not None:
        exml.append('<wildfire-analysis><member>%s</member></wildfire-analysis>' %
                    wildfire)

    exml = ''.join(exml)
    xapi.set(xpath=_PG_XPATH % pg_name, element=exml)

    return True


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        pg_name=dict(required=True),
        data_filtering=dict(),
        file_blocking=dict(),
        spyware=dict(),
        url_filtering=dict(),
        virus=dict(),
        vulnerability=dict(),
        wildfire=dict(),
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

    pg_name = module.params['pg_name']
    data_filtering = module.params['data_filtering']
    file_blocking = module.params['file_blocking']
    spyware = module.params['spyware']
    url_filtering = module.params['url_filtering']
    virus = module.params['virus']
    vulnerability = module.params['vulnerability']
    wildfire = module.params['wildfire']
    commit = module.params['commit']

    try:
        changed = add_pg(xapi, pg_name, data_filtering, file_blocking,
                         spyware, url_filtering, virus, vulnerability, wildfire)

        if changed and commit:
            xapi.commit(cmd="<commit></commit>", sync=True, interval=1)
    except PanXapiError:
        exc = get_exception()
        module.fail_json(msg=exc.message)

    module.exit_json(changed=changed, msg="okey dokey")


if __name__ == '__main__':
    main()
