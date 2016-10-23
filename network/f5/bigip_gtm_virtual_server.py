#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Michael Perzel
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
module: bigip_gtm_virtual_server
short_description: "Manages F5 BIG-IP GTM virtual servers"
description:
    - "Manages F5 BIG-IP GTM virtual servers"
version_added: "2.2"
author:
    - Michael Perzel (@perzizzle)
    - Tim Rupp (@caphrim007)
notes:
    - "Requires BIG-IP software version >= 11.4"
    - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
    - "Best run as a local_action in your playbook"
    - "Tested with manager and above account privilege level"

requirements:
    - bigsuds
options:
    state:
        description:
            - Virtual server state
        required: false
        default: present
        choices: ['present', 'absent','enabled','disabled']
    virtual_server_name:
        description:
            - Virtual server name
        required: True
    virtual_server_server:
        description:
            - Virtual server server
        required: true
    host:
        description:
            - Virtual server host
        required: false
        default: None
        aliases: ['address']
    port:
        description:
            - Virtual server port
        required: false
        default: None
extends_documentation_fragment: f5
'''

EXAMPLES = '''
  - name: Enable virtual server
    local_action: >
      bigip_gtm_virtual_server
      server=192.0.2.1
      user=admin
      password=mysecret
      virtual_server_name=myname
      virtual_server_server=myserver
      state=enabled
'''

RETURN = '''# '''

try:
    import bigsuds
except ImportError:
    bigsuds_found = False
else:
    bigsuds_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.f5 import bigip_api, f5_argument_spec


def server_exists(api, server):
    # hack to determine if virtual server exists
    result = False
    try:
        api.GlobalLB.Server.get_object_status([server])
        result = True
    except bigsuds.OperationFailed:
        e = get_exception()
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result


def virtual_server_exists(api, name, server):
    # hack to determine if virtual server exists
    result = False
    try:
        virtual_server_id = {'name': name, 'server': server}
        api.GlobalLB.VirtualServerV2.get_object_status([virtual_server_id])
        result = True
    except bigsuds.OperationFailed:
        e = get_exception()
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result


def add_virtual_server(api, virtual_server_name, virtual_server_server, address, port):
    addresses = {'address': address, 'port': port}
    virtual_server_id = {'name': virtual_server_name, 'server': virtual_server_server}
    api.GlobalLB.VirtualServerV2.create([virtual_server_id], [addresses])


def remove_virtual_server(api, virtual_server_name, virtual_server_server):
    virtual_server_id = {'name': virtual_server_name, 'server': virtual_server_server}
    api.GlobalLB.VirtualServerV2.delete_virtual_server([virtual_server_id])


def get_virtual_server_state(api, name, server):
    virtual_server_id = {'name': name, 'server': server}
    state = api.GlobalLB.VirtualServerV2.get_enabled_state([virtual_server_id])
    state = state[0].split('STATE_')[1].lower()
    return state


def set_virtual_server_state(api, name, server, state):
    virtual_server_id = {'name': name, 'server': server}
    state = "STATE_%s" % state.strip().upper()
    api.GlobalLB.VirtualServerV2.set_enabled_state([virtual_server_id], [state])


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        state=dict(type='str', default='present', choices=['present', 'absent', 'enabled', 'disabled']),
        host=dict(type='str', default=None, aliases=['address']),
        port=dict(type='int', default=None),
        virtual_server_name=dict(type='str', required=True),
        virtual_server_server=dict(type='str', required=True)
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    server = module.params['server']
    server_port = module.params['server_port']
    validate_certs = module.params['validate_certs']
    user = module.params['user']
    password = module.params['password']
    virtual_server_name = module.params['virtual_server_name']
    virtual_server_server = module.params['virtual_server_server']
    state = module.params['state']
    address = module.params['host']
    port = module.params['port']

    result = {'changed': False}  # default

    try:
        api = bigip_api(server, user, password, validate_certs, port=server_port)

        if state == 'absent':
            if virtual_server_exists(api, virtual_server_name, virtual_server_server):
                if not module.check_mode:
                    remove_virtual_server(api, virtual_server_name, virtual_server_server)
                    result = {'changed': True}
                else:
                    # check-mode return value
                    result = {'changed': True}
        elif state == 'present':
            if virtual_server_name and virtual_server_server and address and port:
                if not virtual_server_exists(api, virtual_server_name, virtual_server_server):
                    if not module.check_mode:
                        if server_exists(api, virtual_server_server):
                            add_virtual_server(api, virtual_server_name, virtual_server_server, address, port)
                            result = {'changed': True}
                        else:
                            module.fail_json(msg="server does not exist")
                    else:
                        # check-mode return value
                        result = {'changed': True}
                else:
                    # virtual server exists -- potentially modify attributes --future feature
                    result = {'changed': False}
            else:
                module.fail_json(msg="Address and port are required to create virtual server")
        elif state == 'enabled':
            if not virtual_server_exists(api, virtual_server_name, virtual_server_server):
                module.fail_json(msg="virtual server does not exist")
            if state != get_virtual_server_state(api, virtual_server_name, virtual_server_server):
                if not module.check_mode:
                    set_virtual_server_state(api, virtual_server_name, virtual_server_server, state)
                    result = {'changed': True}
                else:
                    result = {'changed': True}
        elif state == 'disabled':
            if not virtual_server_exists(api, virtual_server_name, virtual_server_server):
                module.fail_json(msg="virtual server does not exist")
            if state != get_virtual_server_state(api, virtual_server_name, virtual_server_server):
                if not module.check_mode:
                    set_virtual_server_state(api, virtual_server_name, virtual_server_server, state)
                    result = {'changed': True}
                else:
                    result = {'changed': True}

    except Exception:
        e = get_exception()
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
