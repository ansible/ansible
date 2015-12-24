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
module: bigip_pool
short_description: "Manages F5 BIG-IP LTM pools"
description:
    - "Manages F5 BIG-IP LTM pools via iControl SOAP API"
version_added: "1.2"
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
            - Pool/pool member state
        required: false
        default: present
        choices: ['present', 'absent']
        aliases: []
    name:
        description:
            - Pool name
        required: true
        default: null
        choices: []
        aliases: ['pool']
    partition:
        description:
            - Partition of pool/pool member
        required: false
        default: 'Common'
        choices: []
        aliases: []
    lb_method:
        description:
            - Load balancing method
        version_added: "1.3"
        required: False
        default: 'round_robin'
        choices: ['round_robin', 'ratio_member', 'least_connection_member',
                  'observed_member', 'predictive_member', 'ratio_node_address',
                  'least_connection_node_address', 'fastest_node_address',
                  'observed_node_address', 'predictive_node_address',
                  'dynamic_ratio', 'fastest_app_response', 'least_sessions',
                  'dynamic_ratio_member', 'l3_addr', 'unknown',
                  'weighted_least_connection_member',
                  'weighted_least_connection_node_address',
                  'ratio_session', 'ratio_least_connection_member',
                  'ratio_least_connection_node_address']
        aliases: []
    monitor_type:
        description:
            - Monitor rule type when monitors > 1
        version_added: "1.3"
        required: False
        default: null
        choices: ['and_list', 'm_of_n']
        aliases: []
    quorum:
        description:
            - Monitor quorum value when monitor_type is m_of_n
        version_added: "1.3"
        required: False
        default: null
        choices: []
        aliases: []
    monitors:
        description:
            - Monitor template name list. Always use the full path to the monitor.
        version_added: "1.3"
        required: False
        default: null
        choices: []
        aliases: []
    slow_ramp_time:
        description:
            - Sets the ramp-up time (in seconds) to gradually ramp up the load on newly added or freshly detected up pool members
        version_added: "1.3"
        required: False
        default: null
        choices: []
        aliases: []
    service_down_action:
        description:
            - Sets the action to take when node goes down in pool
        version_added: "1.3"
        required: False
        default: null
        choices: ['none', 'reset', 'drop', 'reselect']
        aliases: []
    host:
        description:
            - "Pool member IP"
        required: False
        default: null
        choices: []
        aliases: ['address']
    port:
        description:
            - "Pool member port"
        required: False
        default: null
        choices: []
        aliases: []
'''

EXAMPLES = '''

## playbook task examples:

---
# file bigip-test.yml
# ...
- hosts: localhost
  tasks:
  - name: Create pool
    local_action: >
      bigip_pool
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      name=matthite-pool
      partition=matthite
      lb_method=least_connection_member
      slow_ramp_time=120

  - name: Modify load balancer method
    local_action: >
      bigip_pool
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      name=matthite-pool
      partition=matthite
      lb_method=round_robin

- hosts: bigip-test
  tasks:
  - name: Add pool member
    local_action: >
      bigip_pool
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=present
      name=matthite-pool
      partition=matthite
      host="{{ ansible_default_ipv4["address"] }}"
      port=80

  - name: Remove pool member from pool
    local_action: >
      bigip_pool
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=absent
      name=matthite-pool
      partition=matthite
      host="{{ ansible_default_ipv4["address"] }}"
      port=80

- hosts: localhost
  tasks:
  - name: Delete pool
    local_action: >
      bigip_pool
      server=lb.mydomain.com
      user=admin
      password=mysecret
      state=absent
      name=matthite-pool
      partition=matthite

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

def create_pool(api, pool, lb_method):
    # create requires lb_method but we don't want to default
    # to a value on subsequent runs
    if not lb_method:
        lb_method = 'round_robin'
    lb_method = "LB_METHOD_%s" % lb_method.strip().upper()
    api.LocalLB.Pool.create_v2(pool_names=[pool], lb_methods=[lb_method],
                               members=[[]])

def remove_pool(api, pool):
    api.LocalLB.Pool.delete_pool(pool_names=[pool])

def get_lb_method(api, pool):
    lb_method = api.LocalLB.Pool.get_lb_method(pool_names=[pool])[0]
    lb_method = lb_method.strip().replace('LB_METHOD_', '').lower()
    return lb_method

def set_lb_method(api, pool, lb_method):
    lb_method = "LB_METHOD_%s" % lb_method.strip().upper()
    api.LocalLB.Pool.set_lb_method(pool_names=[pool], lb_methods=[lb_method])

def get_monitors(api, pool):
    result = api.LocalLB.Pool.get_monitor_association(pool_names=[pool])[0]['monitor_rule']
    monitor_type = result['type'].split("MONITOR_RULE_TYPE_")[-1].lower()
    quorum = result['quorum']
    monitor_templates = result['monitor_templates']
    return (monitor_type, quorum, monitor_templates)

def set_monitors(api, pool, monitor_type, quorum, monitor_templates):
    monitor_type = "MONITOR_RULE_TYPE_%s" % monitor_type.strip().upper()
    monitor_rule = {'type': monitor_type, 'quorum': quorum, 'monitor_templates': monitor_templates}
    monitor_association = {'pool_name': pool, 'monitor_rule': monitor_rule}
    api.LocalLB.Pool.set_monitor_association(monitor_associations=[monitor_association])

def get_slow_ramp_time(api, pool):
    result = api.LocalLB.Pool.get_slow_ramp_time(pool_names=[pool])[0]
    return result

def set_slow_ramp_time(api, pool, seconds):
    api.LocalLB.Pool.set_slow_ramp_time(pool_names=[pool], values=[seconds])

def get_action_on_service_down(api, pool):
    result = api.LocalLB.Pool.get_action_on_service_down(pool_names=[pool])[0]
    result = result.split("SERVICE_DOWN_ACTION_")[-1].lower()
    return result

def set_action_on_service_down(api, pool, action):
    action = "SERVICE_DOWN_ACTION_%s" % action.strip().upper()
    api.LocalLB.Pool.set_action_on_service_down(pool_names=[pool], actions=[action])

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

def main():
    lb_method_choices = ['round_robin', 'ratio_member',
                         'least_connection_member', 'observed_member',
                         'predictive_member', 'ratio_node_address',
                         'least_connection_node_address',
                         'fastest_node_address', 'observed_node_address',
                         'predictive_node_address', 'dynamic_ratio',
                         'fastest_app_response', 'least_sessions',
                         'dynamic_ratio_member', 'l3_addr', 'unknown',
                         'weighted_least_connection_member',
                         'weighted_least_connection_node_address',
                         'ratio_session', 'ratio_least_connection_member',
                         'ratio_least_connection_node_address']

    monitor_type_choices = ['and_list', 'm_of_n']

    service_down_choices = ['none', 'reset', 'drop', 'reselect']

    argument_spec=f5_argument_spec();
    argument_spec.update(dict(
            name = dict(type='str', required=True, aliases=['pool']),
            lb_method = dict(type='str', choices=lb_method_choices),
            monitor_type = dict(type='str', choices=monitor_type_choices),
            quorum = dict(type='int'),
            monitors = dict(type='list'),
            slow_ramp_time = dict(type='int'),
            service_down_action = dict(type='str', choices=service_down_choices),
            host = dict(type='str', aliases=['address']),
            port = dict(type='int')
        )
    )

    module = AnsibleModule(
        argument_spec = argument_spec,
        supports_check_mode=True
    )

    (server,user,password,state,partition,validate_certs) = f5_parse_arguments(module)

    name = module.params['name']
    pool = fq_name(partition,name)
    lb_method = module.params['lb_method']
    if lb_method:
        lb_method = lb_method.lower()
    monitor_type = module.params['monitor_type']
    if monitor_type:
        monitor_type = monitor_type.lower()
    quorum = module.params['quorum']
    monitors = module.params['monitors']
    if monitors:
        monitors = []
        for monitor in module.params['monitors']:
                monitors.append(fq_name(partition, monitor))
    slow_ramp_time = module.params['slow_ramp_time']
    service_down_action = module.params['service_down_action']
    if service_down_action:
        service_down_action = service_down_action.lower()
    host = module.params['host']
    address = fq_name(partition,host)
    port = module.params['port']

    # sanity check user supplied values

    if (host and not port) or (port and not host):
        module.fail_json(msg="both host and port must be supplied")

    if 1 > port > 65535:
        module.fail_json(msg="valid ports must be in range 1 - 65535")

    if monitors:
        if len(monitors) == 1:
            # set default required values for single monitor
            quorum = 0
            monitor_type = 'single'
        elif len(monitors) > 1:
            if not monitor_type:
                module.fail_json(msg="monitor_type required for monitors > 1")
            if monitor_type == 'm_of_n' and not quorum:
                module.fail_json(msg="quorum value required for monitor_type m_of_n")
            if monitor_type != 'm_of_n':
                quorum = 0
    elif monitor_type:
        # no monitors specified but monitor_type exists
        module.fail_json(msg="monitor_type require monitors parameter")
    elif quorum is not None:
        # no monitors specified but quorum exists
        module.fail_json(msg="quorum requires monitors parameter")

    try:
        api = bigip_api(server, user, password, validate_certs)
        result = {'changed': False}  # default

        if state == 'absent':
            if host and port and pool:
                # member removal takes precedent
                if pool_exists(api, pool) and member_exists(api, pool, address, port):
                    if not module.check_mode:
                        remove_pool_member(api, pool, address, port)
                        deleted = delete_node_address(api, address)
                        result = {'changed': True, 'deleted': deleted}
                    else:
                        result = {'changed': True}
            elif pool_exists(api, pool):
                # no host/port supplied, must be pool removal
                if not module.check_mode:
                    # hack to handle concurrent runs of module
                    # pool might be gone before we actually remove it
                    try:
                        remove_pool(api, pool)
                        result = {'changed': True}
                    except bigsuds.OperationFailed, e:
                        if "was not found" in str(e):
                            result = {'changed': False}
                        else:
                            # genuine exception
                            raise
                else:
                    # check-mode return value
                    result = {'changed': True}

        elif state == 'present':
            update = False
            if not pool_exists(api, pool):
                # pool does not exist -- need to create it
                if not module.check_mode:
                    # a bit of a hack to handle concurrent runs of this module.
                    # even though we've checked the pool doesn't exist,
                    # it may exist by the time we run create_pool().
                    # this catches the exception and does something smart
                    # about it!
                    try:
                        create_pool(api, pool, lb_method)
                        result = {'changed': True}
                    except bigsuds.OperationFailed, e:
                        if "already exists" in str(e):
                            update = True
                        else:
                            # genuine exception
                            raise
                    else:
                        if monitors:
                            set_monitors(api, pool, monitor_type, quorum, monitors)
                        if slow_ramp_time:
                            set_slow_ramp_time(api, pool, slow_ramp_time)
                        if service_down_action:
                            set_action_on_service_down(api, pool, service_down_action)
                        if host and port:
                            add_pool_member(api, pool, address, port)
                else:
                    # check-mode return value
                    result = {'changed': True}
            else:
                # pool exists -- potentially modify attributes
                update = True

            if update:
                if lb_method and lb_method != get_lb_method(api, pool):
                    if not module.check_mode:
                        set_lb_method(api, pool, lb_method)
                    result = {'changed': True}
                if monitors:
                    t_monitor_type, t_quorum, t_monitor_templates = get_monitors(api, pool)
                    if (t_monitor_type != monitor_type) or (t_quorum != quorum) or (set(t_monitor_templates) != set(monitors)):
                        if not module.check_mode:
                            set_monitors(api, pool, monitor_type, quorum, monitors)
                        result = {'changed': True}
                if slow_ramp_time and slow_ramp_time != get_slow_ramp_time(api, pool):
                    if not module.check_mode:
                        set_slow_ramp_time(api, pool, slow_ramp_time)
                    result = {'changed': True}
                if service_down_action and service_down_action != get_action_on_service_down(api, pool):
                    if not module.check_mode:
                        set_action_on_service_down(api, pool, service_down_action)
                    result = {'changed': True}
                if (host and port) and not member_exists(api, pool, address, port):
                    if not module.check_mode:
                        add_pool_member(api, pool, address, port)
                    result = {'changed': True}

    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *
main()

