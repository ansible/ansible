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
module: bigip_pool_member
short_description: "Manages F5 BIG-IP LTM pool members"
description:
    - "Manages F5 BIG-IP LTM pool members via iControl SOAP API"
version_added: "1.4"
author: "Matt Hite (@mhite)"
notes:
    - "Requires BIG-IP software version >= 11"
    - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
    - "Best run as a local_action in your playbook"
    - "Supersedes bigip_pool for managing pool members"

requirements:
    - bigsuds
options:
    server:
        description:
            - BIG-IP host
        required: true
    user:
        description:
            - BIG-IP username
        required: true
    password:
        description:
            - BIG-IP password
        required: true
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
    session_state:
        description:
            - Set new session availability status for pool member
        version_added: "2.0"
        required: false
        default: null
        choices: ['enabled', 'disabled']
    monitor_state:
        description:
            - Set monitor availability status for pool member
        version_added: "2.0"
        required: false
        default: null
        choices: ['enabled', 'disabled']
    pool:
        description:
            - Pool name. This pool must exist.
        required: true
    partition:
        description:
            - Partition
        required: false
        default: 'Common'
    host:
        description:
            - Pool member IP
        required: true
        aliases: ['address', 'name']
    port:
        description:
            - Pool member port
        required: true
    connection_limit:
        description:
            - Pool member connection limit. Setting this to 0 disables the limit.
        required: false
        default: null
    description:
        description:
            - Pool member description
        required: false
        default: null
    rate_limit:
        description:
            - Pool member rate limit (connections-per-second). Setting this to 0 disables the limit.
        required: false
        default: null
    ratio:
        description:
            - Pool member ratio weight. Valid values range from 1 through 100. New pool members -- unless overriden with this value -- default to 1.
        required: false
        default: null
    preserve_node:
        description:
            - When state is absent and the pool member is no longer referenced in other pools, the default behavior removes the unused node object. Setting this to 'yes' disables this behavior.
        required: false
        default: 'no'
        choices: ['yes', 'no']
        version_added: 2.1
'''

EXAMPLES = '''

## playbook task examples:

---
# file bigip-test.yml
# ...
- hosts: bigip-test
  tasks:
  - name: Add pool member
    local_action: >
      bigip_pool_member
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      pool=matthite-pool
      partition=matthite
      host="{{ ansible_default_ipv4["address"] }}"
      port=80
      description="web server"
      connection_limit=100
      rate_limit=50
      ratio=2

  - name: Modify pool member ratio and description
    local_action: >
      bigip_pool_member
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      pool=matthite-pool
      partition=matthite
      host="{{ ansible_default_ipv4["address"] }}"
      port=80
      ratio=1
      description="nginx server"

  - name: Remove pool member from pool
    local_action: >
      bigip_pool_member
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=absent
      pool=matthite-pool
      partition=matthite
      host="{{ ansible_default_ipv4["address"] }}"
      port=80


  # The BIG-IP GUI doesn't map directly to the API calls for "Pool ->
  # Members -> State". The following states map to API monitor
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

  - name: Force pool member offline
    local_action: >
      bigip_pool_member
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      session_state=disabled
      monitor_state=disabled
      pool=matthite-pool
      partition=matthite
      host="{{ ansible_default_ipv4["address"] }}"
      port=80

'''

def pool_exists(api, pool):
    # hack to determine if pool exists
    result = False
    try:
        api.LocalLB.Pool.get_object_status(pool_names=[pool])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def member_exists(api, pool, address, port):
    # hack to determine if member exists
    result = False
    try:
        members = [{'address': address, 'port': port}]
        api.LocalLB.Pool.get_member_object_status(pool_names=[pool],
                                                  members=[members])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def delete_node_address(api, address):
    result = False
    try:
        api.LocalLB.NodeAddressV2.delete_node_address(nodes=[address])
        result = True
    except bigsuds.OperationFailed, e:
        if "is referenced by a member of pool" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def remove_pool_member(api, pool, address, port):
    members = [{'address': address, 'port': port}]
    api.LocalLB.Pool.remove_member_v2(pool_names=[pool], members=[members])

def add_pool_member(api, pool, address, port):
    members = [{'address': address, 'port': port}]
    api.LocalLB.Pool.add_member_v2(pool_names=[pool], members=[members])

def get_connection_limit(api, pool, address, port):
    members = [{'address': address, 'port': port}]
    result = api.LocalLB.Pool.get_member_connection_limit(pool_names=[pool], members=[members])[0][0]
    return result

def set_connection_limit(api, pool, address, port, limit):
    members = [{'address': address, 'port': port}]
    api.LocalLB.Pool.set_member_connection_limit(pool_names=[pool], members=[members], limits=[[limit]])

def get_description(api, pool, address, port):
    members = [{'address': address, 'port': port}]
    result = api.LocalLB.Pool.get_member_description(pool_names=[pool], members=[members])[0][0]
    return result

def set_description(api, pool, address, port, description):
    members = [{'address': address, 'port': port}]
    api.LocalLB.Pool.set_member_description(pool_names=[pool], members=[members], descriptions=[[description]])

def get_rate_limit(api, pool, address, port):
    members = [{'address': address, 'port': port}]
    result = api.LocalLB.Pool.get_member_rate_limit(pool_names=[pool], members=[members])[0][0]
    return result

def set_rate_limit(api, pool, address, port, limit):
    members = [{'address': address, 'port': port}]
    api.LocalLB.Pool.set_member_rate_limit(pool_names=[pool], members=[members], limits=[[limit]])

def get_ratio(api, pool, address, port):
    members = [{'address': address, 'port': port}]
    result = api.LocalLB.Pool.get_member_ratio(pool_names=[pool], members=[members])[0][0]
    return result

def set_ratio(api, pool, address, port, ratio):
    members = [{'address': address, 'port': port}]
    api.LocalLB.Pool.set_member_ratio(pool_names=[pool], members=[members], ratios=[[ratio]])

def set_member_session_enabled_state(api, pool, address, port, session_state):
    members = [{'address': address, 'port': port}]
    session_state = ["STATE_%s" % session_state.strip().upper()]
    api.LocalLB.Pool.set_member_session_enabled_state(pool_names=[pool], members=[members], session_states=[session_state])

def get_member_session_status(api, pool, address, port):
    members = [{'address': address, 'port': port}]
    result = api.LocalLB.Pool.get_member_session_status(pool_names=[pool], members=[members])[0][0]
    result = result.split("SESSION_STATUS_")[-1].lower()
    return result

def set_member_monitor_state(api, pool, address, port, monitor_state):
    members = [{'address': address, 'port': port}]
    monitor_state = ["STATE_%s" % monitor_state.strip().upper()]
    api.LocalLB.Pool.set_member_monitor_state(pool_names=[pool], members=[members], monitor_states=[monitor_state])

def get_member_monitor_status(api, pool, address, port):
    members = [{'address': address, 'port': port}]
    result = api.LocalLB.Pool.get_member_monitor_status(pool_names=[pool], members=[members])[0][0]
    result = result.split("MONITOR_STATUS_")[-1].lower()
    return result

def main():
    argument_spec = f5_argument_spec();
    argument_spec.update(dict(
            session_state = dict(type='str', choices=['enabled', 'disabled']),
            monitor_state = dict(type='str', choices=['enabled', 'disabled']),
            pool = dict(type='str', required=True),
            host = dict(type='str', required=True, aliases=['address', 'name']),
            port = dict(type='int', required=True),
            connection_limit = dict(type='int'),
            description = dict(type='str'),
            rate_limit = dict(type='int'),
            ratio = dict(type='int'),
            preserve_node = dict(type='bool', default=False)
        )
    )

    module = AnsibleModule(
        argument_spec = argument_spec,
        supports_check_mode=True
    )

    (server,user,password,state,partition,validate_certs) = f5_parse_arguments(module)
    session_state = module.params['session_state']
    monitor_state = module.params['monitor_state']
    pool = fq_name(partition, module.params['pool'])
    connection_limit = module.params['connection_limit']
    description = module.params['description']
    rate_limit = module.params['rate_limit']
    ratio = module.params['ratio']
    host = module.params['host']
    address = fq_name(partition, host)
    port = module.params['port']
    preserve_node = module.params['preserve_node']


    # sanity check user supplied values

    if (host and port is None) or (port is not None and not host):
        module.fail_json(msg="both host and port must be supplied")

    if 0 > port or port > 65535:
        module.fail_json(msg="valid ports must be in range 0 - 65535")

    try:
        api = bigip_api(server, user, password, validate_certs)
        if not pool_exists(api, pool):
            module.fail_json(msg="pool %s does not exist" % pool)
        result = {'changed': False}  # default

        if state == 'absent':
            if member_exists(api, pool, address, port):
                if not module.check_mode:
                    remove_pool_member(api, pool, address, port)
                    if preserve_node:
                        result = {'changed': True}
                    else:
                        deleted = delete_node_address(api, address)
                        result = {'changed': True, 'deleted': deleted}
                else:
                    result = {'changed': True}

        elif state == 'present':
            if not member_exists(api, pool, address, port):
                if not module.check_mode:
                    add_pool_member(api, pool, address, port)
                    if connection_limit is not None:
                        set_connection_limit(api, pool, address, port, connection_limit)
                    if description is not None:
                        set_description(api, pool, address, port, description)
                    if rate_limit is not None:
                        set_rate_limit(api, pool, address, port, rate_limit)
                    if ratio is not None:
                        set_ratio(api, pool, address, port, ratio)
                    if session_state is not None:
                        set_member_session_enabled_state(api, pool, address, port, session_state)
                    if monitor_state is not None:
                        set_member_monitor_state(api, pool, address, port, monitor_state)
                result = {'changed': True}
            else:
                # pool member exists -- potentially modify attributes
                if connection_limit is not None and connection_limit != get_connection_limit(api, pool, address, port):
                    if not module.check_mode:
                        set_connection_limit(api, pool, address, port, connection_limit)
                    result = {'changed': True}
                if description is not None and description != get_description(api, pool, address, port):
                    if not module.check_mode:
                        set_description(api, pool, address, port, description)
                    result = {'changed': True}
                if rate_limit is not None and rate_limit != get_rate_limit(api, pool, address, port):
                    if not module.check_mode:
                        set_rate_limit(api, pool, address, port, rate_limit)
                    result = {'changed': True}
                if ratio is not None and ratio != get_ratio(api, pool, address, port):
                    if not module.check_mode:
                        set_ratio(api, pool, address, port, ratio)
                    result = {'changed': True}
                if session_state is not None:
                    session_status = get_member_session_status(api, pool, address, port)
                    if session_state == 'enabled' and session_status == 'forced_disabled':
                        if not module.check_mode:
                            set_member_session_enabled_state(api, pool, address, port, session_state)
                        result = {'changed': True}
                    elif session_state == 'disabled' and session_status != 'force_disabled':
                        if not module.check_mode:
                            set_member_session_enabled_state(api, pool, address, port, session_state)
                        result = {'changed': True}
                if monitor_state is not None:
                    monitor_status = get_member_monitor_status(api, pool, address, port)
                    if monitor_state == 'enabled' and monitor_status == 'forced_down':
                        if not module.check_mode:
                            set_member_monitor_state(api, pool, address, port, monitor_state)
                        result = {'changed': True}
                    elif monitor_state == 'disabled' and monitor_status != 'forced_down':
                        if not module.check_mode:
                            set_member_monitor_state(api, pool, address, port, monitor_state)
                        result = {'changed': True}

    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
