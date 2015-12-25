#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Matt Hite <mhite@hotmail.com>
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
module: bigip_node
short_description: "Manages F5 BIG-IP LTM nodes"
description:
    - "Manages F5 BIG-IP LTM nodes via iControl SOAP API"
version_added: "1.4"
author: "Matt Hite (@mhite)"
notes:
    - "Requires BIG-IP software version >= 11"
    - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
    - "Best run as a local_action in your playbook"
requirements:
    - bigsuds
options:
    server:
        description:
            - BIG-IP host
        required: true
        default: null
        choices: []
        aliases: []
    user:
        description:
            - BIG-IP username
        required: true
        default: null
        choices: []
        aliases: []
    password:
        description:
            - BIG-IP password
        required: true
        default: null
        choices: []
        aliases: []
    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be used
              on personally controlled sites.  Prior to 2.0, this module would always
              validate on python >= 2.7.9 and never validate on python <= 2.7.8
        required: false
        default: 'yes'
        choices: ['yes', 'no']
        version_added: 2.0
    state:
        description:
            - Pool member state
        required: true
        default: present
        choices: ['present', 'absent']
        aliases: []
    session_state:
        description:
            - Set new session availability status for node
        version_added: "1.9"
        required: false
        default: null
        choices: ['enabled', 'disabled']
        aliases: []
    monitor_state:
        description:
            - Set monitor availability status for node
        version_added: "1.9"
        required: false
        default: null
        choices: ['enabled', 'disabled']
        aliases: []
    partition:
        description:
            - Partition
        required: false
        default: 'Common'
        choices: []
        aliases: []
    name:
        description:
            - "Node name"
        required: false
        default: null
        choices: []
    host:
        description:
            - "Node IP. Required when state=present and node does not exist. Error when state=absent."
        required: true
        default: null
        choices: []
        aliases: ['address', 'ip']
    description:
        description:
            - "Node description."
        required: false
        default: null
        choices: []
'''

EXAMPLES = '''

## playbook task examples:

---
# file bigip-test.yml
# ...
- hosts: bigip-test
  tasks:
  - name: Add node
    local_action: >
      bigip_node
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      partition=matthite
      host="{{ ansible_default_ipv4["address"] }}"
      name="{{ ansible_default_ipv4["address"] }}"

# Note that the BIG-IP automatically names the node using the
# IP address specified in previous play's host parameter.
# Future plays referencing this node no longer use the host
# parameter but instead use the name parameter.
# Alternatively, you could have specified a name with the
# name parameter when state=present.

  - name: Modify node description
    local_action: >
      bigip_node
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      partition=matthite
      name="{{ ansible_default_ipv4["address"] }}"
      description="Our best server yet"

  - name: Delete node
    local_action: >
      bigip_node
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=absent
      partition=matthite
      name="{{ ansible_default_ipv4["address"] }}"

# The BIG-IP GUI doesn't map directly to the API calls for "Node ->
# General Properties -> State". The following states map to API monitor
# and session states.
#
# Enabled (all traffic allowed):
# monitor_state=enabled, session_state=enabled
# Disabled (only persistent or active connections allowed):
# monitor_state=enabled, session_state=disabled
# Forced offline (only active connections allowed):
# monitor_state=disabled, session_state=disabled
#
# See https://devcentral.f5.com/questions/icontrol-equivalent-call-for-b-node-down

  - name: Force node offline
    local_action: >
      bigip_node
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      session_state=disabled
      monitor_state=disabled
      partition=matthite
      name="{{ ansible_default_ipv4["address"] }}"

'''

def node_exists(api, address):
    # hack to determine if node exists
    result = False
    try:
        api.LocalLB.NodeAddressV2.get_object_status(nodes=[address])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def create_node_address(api, address, name):
    try:
        api.LocalLB.NodeAddressV2.create(nodes=[name], addresses=[address], limits=[0])
        result = True
        desc = ""
    except bigsuds.OperationFailed, e:
        if "already exists" in str(e):
            result = False
            desc = "referenced name or IP already in use"
        else:
            # genuine exception
            raise
    return (result, desc)

def get_node_address(api, name):
    return api.LocalLB.NodeAddressV2.get_address(nodes=[name])[0]

def delete_node_address(api, address):
    try:
        api.LocalLB.NodeAddressV2.delete_node_address(nodes=[address])
        result = True
        desc = ""
    except bigsuds.OperationFailed, e:
        if "is referenced by a member of pool" in str(e):
            result = False
            desc = "node referenced by pool"
        else:
            # genuine exception
            raise
    return (result, desc)

def set_node_description(api, name, description):
    api.LocalLB.NodeAddressV2.set_description(nodes=[name],
                                              descriptions=[description])

def get_node_description(api, name):
    return api.LocalLB.NodeAddressV2.get_description(nodes=[name])[0]

def set_node_session_enabled_state(api, name, session_state):
    session_state = "STATE_%s" % session_state.strip().upper()
    api.LocalLB.NodeAddressV2.set_session_enabled_state(nodes=[name],
                                                        states=[session_state])

def get_node_session_status(api, name):
    result = api.LocalLB.NodeAddressV2.get_session_status(nodes=[name])[0]
    result = result.split("SESSION_STATUS_")[-1].lower()
    return result

def set_node_monitor_state(api, name, monitor_state):
    monitor_state = "STATE_%s" % monitor_state.strip().upper()
    api.LocalLB.NodeAddressV2.set_monitor_state(nodes=[name],
                                                states=[monitor_state])

def get_node_monitor_status(api, name):
    result = api.LocalLB.NodeAddressV2.get_monitor_status(nodes=[name])[0]
    result = result.split("MONITOR_STATUS_")[-1].lower()
    return result


def main():
    argument_spec=f5_argument_spec();
    argument_spec.update(dict(
            session_state = dict(type='str', choices=['enabled', 'disabled']),
            monitor_state = dict(type='str', choices=['enabled', 'disabled']),
            name = dict(type='str', required=True),
            host = dict(type='str', aliases=['address', 'ip']),
            description = dict(type='str')
        )
    )

    module = AnsibleModule(
        argument_spec = argument_spec,
        supports_check_mode=True
    )

    (server,user,password,state,partition,validate_certs) = f5_parse_arguments(module)

    session_state = module.params['session_state']
    monitor_state = module.params['monitor_state']
    host = module.params['host']
    name = module.params['name']
    address = fq_name(partition, name)
    description = module.params['description']

    if state == 'absent' and host is not None:
        module.fail_json(msg="host parameter invalid when state=absent")

    try:
        api = bigip_api(server, user, password, validate_certs)
        result = {'changed': False}  # default

        if state == 'absent':
            if node_exists(api, address):
                if not module.check_mode:
                    deleted, desc = delete_node_address(api, address)
                    if not deleted:
                        module.fail_json(msg="unable to delete: %s" % desc)
                    else:
                        result = {'changed': True}
                else:
                    # check-mode return value
                    result = {'changed': True}

        elif state == 'present':
            if not node_exists(api, address):
                if host is None:
                    module.fail_json(msg="host parameter required when " \
                                         "state=present and node does not exist")
                if not module.check_mode:
                    created, desc = create_node_address(api, address=host, name=address)
                    if not created:
                        module.fail_json(msg="unable to create: %s" % desc)
                    else:
                        result = {'changed': True}
                    if session_state is not None:
                        set_node_session_enabled_state(api, address,
                                                       session_state)
                        result = {'changed': True}
                    if monitor_state is not None:
                        set_node_monitor_state(api, address, monitor_state)
                        result = {'changed': True}
                    if description is not None:
                        set_node_description(api, address, description)
                        result = {'changed': True}
                else:
                    # check-mode return value
                    result = {'changed': True}
            else:
                # node exists -- potentially modify attributes
                if host is not None:
                    if get_node_address(api, address) != host:
                        module.fail_json(msg="Changing the node address is " \
                                             "not supported by the API; " \
                                             "delete and recreate the node.")
                if session_state is not None:
                    session_status = get_node_session_status(api, address)
                    if session_state == 'enabled' and \
                       session_status == 'forced_disabled':
                        if not module.check_mode:
                            set_node_session_enabled_state(api, address,
                                                           session_state)
                        result = {'changed': True}
                    elif session_state == 'disabled' and \
                         session_status != 'force_disabled':
                        if not module.check_mode:
                            set_node_session_enabled_state(api, address,
                                                           session_state)
                        result = {'changed': True}
                if monitor_state is not None:
                    monitor_status = get_node_monitor_status(api, address)
                    if monitor_state == 'enabled' and \
                       monitor_status == 'forced_down':
                        if not module.check_mode:
                            set_node_monitor_state(api, address,
                                                   monitor_state)
                        result = {'changed': True}
                    elif monitor_state == 'disabled' and \
                         monitor_status != 'forced_down':
                        if not module.check_mode:
                            set_node_monitor_state(api, address,
                                                   monitor_state)
                        result = {'changed': True}
                if description is not None:
                    if get_node_description(api, address) != description:
                        if not module.check_mode:
                            set_node_description(api, address, description)
                        result = {'changed': True}

    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *
main()

