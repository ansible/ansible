#!/usr/bin/python
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: oneandone_load_balancer
short_description: Configure 1&1 load balancer.
description:
     - Create, remove, update load balancers.
       This module has a dependency on 1and1 >= 1.0
version_added: "2.5"
options:
  state:
    description:
      - Define a load balancer state to create, remove, or update.
    required: false
    default: 'present'
    choices: [ "present", "absent", "update" ]
  auth_token:
    description:
      - Authenticating API token provided by 1&1.
    required: true
  load_balancer:
    description:
      - The identifier (id or name) of the load balancer used with update state.
    required: true
  api_url:
    description:
      - Custom API URL. Overrides the
        ONEANDONE_API_URL environement variable.
    required: false
  name:
    description:
      - Load balancer name used with present state. Used as identifier (id or name) when used with absent state.
        maxLength=128
    required: true
  health_check_test:
    description:
      - Type of the health check. At the moment, HTTP is not allowed.
    choices: [ "NONE", "TCP", "HTTP", "ICMP" ]
    required: true
  health_check_interval:
    description:
      - Health check period in seconds. minimum=5, maximum=300, multipleOf=1
    required: true
  health_check_path:
    description:
      - Url to call for cheking. Required for HTTP health check. maxLength=1000
    required: false
  health_check_parse:
    description:
      - Regular expression to check. Required for HTTP health check. maxLength=64
    required: false
  persistence:
    description:
      - Persistence.
    required: true
    type: bool
  persistence_time:
    description:
      - Persistence time in seconds. Required if persistence is enabled. minimum=30, maximum=1200, multipleOf=1
    required: true
  method:
    description:
      - Balancing procedure.
    choices: [ "ROUND_ROBIN", "LEAST_CONNECTIONS" ]
    required: true
  datacenter:
    description:
      - ID or country code of the datacenter where the load balancer will be created.
    default: US
    choices: [ "US", "ES", "DE", "GB" ]
    required: false
  rules:
    description:
      - A list of rule objects that will be set for the load balancer. Each rule must contain protocol,
        port_balancer, and port_server parameters, in addition to source parameter, which is optional.
    required: true
  description:
    description:
      - Description of the load balancer. maxLength=256
    required: false
  add_server_ips:
    description:
      - A list of server identifiers (id or name) to be assigned to a load balancer.
        Used in combination with update state.
    required: false
  remove_server_ips:
    description:
      - A list of server IP ids to be unassigned from a load balancer. Used in combination with update state.
    required: false
  add_rules:
    description:
      - A list of rules that will be added to an existing load balancer.
        It is syntax is the same as the one used for rules parameter. Used in combination with update state.
    required: false
  remove_rules:
    description:
      - A list of rule ids that will be removed from an existing load balancer. Used in combination with update state.
    required: false
  wait:
    description:
      - wait for the instance to be in state 'running' before returning
    required: false
    default: "yes"
    type: bool
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  wait_interval:
    description:
      - Defines the number of seconds to wait when using the _wait_for methods
    default: 5

requirements:
     - "1and1"
     - "python >= 2.6"

author:
  - Amel Ajdinovic (@aajdinov)
  - Ethan Devenport (@edevenport)
'''

EXAMPLES = '''

# Provisioning example. Create and destroy a load balancer.

- oneandone_load_balancer:
    auth_token: oneandone_private_api_key
    name: ansible load balancer
    description: Testing creation of load balancer with ansible
    health_check_test: TCP
    health_check_interval: 40
    persistence: true
    persistence_time: 1200
    method: ROUND_ROBIN
    datacenter: US
    rules:
     -
       protocol: TCP
       port_balancer: 80
       port_server: 80
       source: 0.0.0.0
    wait: true
    wait_timeout: 500

- oneandone_load_balancer:
    auth_token: oneandone_private_api_key
    name: ansible load balancer
    wait: true
    wait_timeout: 500
    state: absent

# Update a load balancer.

- oneandone_load_balancer:
    auth_token: oneandone_private_api_key
    load_balancer: ansible load balancer
    name: ansible load balancer updated
    description: Testing the update of a load balancer with ansible
    wait: true
    wait_timeout: 500
    state: update

# Add server to a load balancer.

- oneandone_load_balancer:
    auth_token: oneandone_private_api_key
    load_balancer: ansible load balancer updated
    description: Adding server to a load balancer with ansible
    add_server_ips:
     - server identifier (id or name)
    wait: true
    wait_timeout: 500
    state: update

# Remove server from a load balancer.

- oneandone_load_balancer:
    auth_token: oneandone_private_api_key
    load_balancer: ansible load balancer updated
    description: Removing server from a load balancer with ansible
    remove_server_ips:
     - B2504878540DBC5F7634EB00A07C1EBD (server's ip id)
    wait: true
    wait_timeout: 500
    state: update

# Add rules to a load balancer.

- oneandone_load_balancer:
    auth_token: oneandone_private_api_key
    load_balancer: ansible load balancer updated
    description: Adding rules to a load balancer with ansible
    add_rules:
     -
       protocol: TCP
       port_balancer: 70
       port_server: 70
       source: 0.0.0.0
     -
       protocol: TCP
       port_balancer: 60
       port_server: 60
       source: 0.0.0.0
    wait: true
    wait_timeout: 500
    state: update

# Remove rules from a load balancer.

- oneandone_load_balancer:
    auth_token: oneandone_private_api_key
    load_balancer: ansible load balancer updated
    description: Adding rules to a load balancer with ansible
    remove_rules:
     - rule_id #1
     - rule_id #2
     - ...
    wait: true
    wait_timeout: 500
    state: update
'''

RETURN = '''
load_balancer:
    description: Information about the load balancer that was processed
    type: dict
    sample: '{"id": "92B74394A397ECC3359825C1656D67A6", "name": "Default Balancer"}'
    returned: always
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oneandone import (
    get_load_balancer,
    get_server,
    get_datacenter,
    OneAndOneResources,
    wait_for_resource_creation_completion
)

HAS_ONEANDONE_SDK = True

try:
    import oneandone.client
except ImportError:
    HAS_ONEANDONE_SDK = False

DATACENTERS = ['US', 'ES', 'DE', 'GB']
HEALTH_CHECK_TESTS = ['NONE', 'TCP', 'HTTP', 'ICMP']
METHODS = ['ROUND_ROBIN', 'LEAST_CONNECTIONS']


def _check_mode(module, result):
    if module.check_mode:
        module.exit_json(
            changed=result
        )


def _add_server_ips(module, oneandone_conn, load_balancer_id, server_ids):
    """
    Assigns servers to a load balancer.
    """
    try:
        attach_servers = []

        for server_id in server_ids:
            server = get_server(oneandone_conn, server_id, True)
            attach_server = oneandone.client.AttachServer(
                server_id=server['id'],
                server_ip_id=next(iter(server['ips'] or []), None)['id']
            )
            attach_servers.append(attach_server)

        if module.check_mode:
            if attach_servers:
                return True
            return False

        load_balancer = oneandone_conn.attach_load_balancer_server(
            load_balancer_id=load_balancer_id,
            server_ips=attach_servers)
        return load_balancer
    except Exception as ex:
        module.fail_json(msg=str(ex))


def _remove_load_balancer_server(module, oneandone_conn, load_balancer_id, server_ip_id):
    """
    Unassigns a server/IP from a load balancer.
    """
    try:
        if module.check_mode:
            lb_server = oneandone_conn.get_load_balancer_server(
                load_balancer_id=load_balancer_id,
                server_ip_id=server_ip_id)
            if lb_server:
                return True
            return False

        load_balancer = oneandone_conn.remove_load_balancer_server(
            load_balancer_id=load_balancer_id,
            server_ip_id=server_ip_id)
        return load_balancer
    except Exception as ex:
        module.fail_json(msg=str(ex))


def _add_load_balancer_rules(module, oneandone_conn, load_balancer_id, rules):
    """
    Adds new rules to a load_balancer.
    """
    try:
        load_balancer_rules = []

        for rule in rules:
            load_balancer_rule = oneandone.client.LoadBalancerRule(
                protocol=rule['protocol'],
                port_balancer=rule['port_balancer'],
                port_server=rule['port_server'],
                source=rule['source'])
            load_balancer_rules.append(load_balancer_rule)

        if module.check_mode:
            lb_id = get_load_balancer(oneandone_conn, load_balancer_id)
            if (load_balancer_rules and lb_id):
                return True
            return False

        load_balancer = oneandone_conn.add_load_balancer_rule(
            load_balancer_id=load_balancer_id,
            load_balancer_rules=load_balancer_rules
        )

        return load_balancer
    except Exception as ex:
        module.fail_json(msg=str(ex))


def _remove_load_balancer_rule(module, oneandone_conn, load_balancer_id, rule_id):
    """
    Removes a rule from a load_balancer.
    """
    try:
        if module.check_mode:
            rule = oneandone_conn.get_load_balancer_rule(
                load_balancer_id=load_balancer_id,
                rule_id=rule_id)
            if rule:
                return True
            return False

        load_balancer = oneandone_conn.remove_load_balancer_rule(
            load_balancer_id=load_balancer_id,
            rule_id=rule_id
        )
        return load_balancer
    except Exception as ex:
        module.fail_json(msg=str(ex))


def update_load_balancer(module, oneandone_conn):
    """
    Updates a load_balancer based on input arguments.
    Load balancer rules and server ips can be added/removed to/from
    load balancer. Load balancer name, description, health_check_test,
    health_check_interval, persistence, persistence_time, and method
    can be updated as well.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    load_balancer_id = module.params.get('load_balancer')
    name = module.params.get('name')
    description = module.params.get('description')
    health_check_test = module.params.get('health_check_test')
    health_check_interval = module.params.get('health_check_interval')
    health_check_path = module.params.get('health_check_path')
    health_check_parse = module.params.get('health_check_parse')
    persistence = module.params.get('persistence')
    persistence_time = module.params.get('persistence_time')
    method = module.params.get('method')
    add_server_ips = module.params.get('add_server_ips')
    remove_server_ips = module.params.get('remove_server_ips')
    add_rules = module.params.get('add_rules')
    remove_rules = module.params.get('remove_rules')

    changed = False

    load_balancer = get_load_balancer(oneandone_conn, load_balancer_id, True)
    if load_balancer is None:
        _check_mode(module, False)

    if (name or description or health_check_test or health_check_interval or health_check_path or
            health_check_parse or persistence or persistence_time or method):
        _check_mode(module, True)
        load_balancer = oneandone_conn.modify_load_balancer(
            load_balancer_id=load_balancer['id'],
            name=name,
            description=description,
            health_check_test=health_check_test,
            health_check_interval=health_check_interval,
            health_check_path=health_check_path,
            health_check_parse=health_check_parse,
            persistence=persistence,
            persistence_time=persistence_time,
            method=method)
        changed = True

    if add_server_ips:
        if module.check_mode:
            _check_mode(module, _add_server_ips(module,
                                                oneandone_conn,
                                                load_balancer['id'],
                                                add_server_ips))

        load_balancer = _add_server_ips(module, oneandone_conn, load_balancer['id'], add_server_ips)
        changed = True

    if remove_server_ips:
        chk_changed = False
        for server_ip_id in remove_server_ips:
            if module.check_mode:
                chk_changed |= _remove_load_balancer_server(module,
                                                            oneandone_conn,
                                                            load_balancer['id'],
                                                            server_ip_id)

            _remove_load_balancer_server(module,
                                         oneandone_conn,
                                         load_balancer['id'],
                                         server_ip_id)
        _check_mode(module, chk_changed)
        load_balancer = get_load_balancer(oneandone_conn, load_balancer['id'], True)
        changed = True

    if add_rules:
        load_balancer = _add_load_balancer_rules(module,
                                                 oneandone_conn,
                                                 load_balancer['id'],
                                                 add_rules)
        _check_mode(module, load_balancer)
        changed = True

    if remove_rules:
        chk_changed = False
        for rule_id in remove_rules:
            if module.check_mode:
                chk_changed |= _remove_load_balancer_rule(module,
                                                          oneandone_conn,
                                                          load_balancer['id'],
                                                          rule_id)

            _remove_load_balancer_rule(module,
                                       oneandone_conn,
                                       load_balancer['id'],
                                       rule_id)
        _check_mode(module, chk_changed)
        load_balancer = get_load_balancer(oneandone_conn, load_balancer['id'], True)
        changed = True

    try:
        return (changed, load_balancer)
    except Exception as ex:
        module.fail_json(msg=str(ex))


def create_load_balancer(module, oneandone_conn):
    """
    Create a new load_balancer.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    try:
        name = module.params.get('name')
        description = module.params.get('description')
        health_check_test = module.params.get('health_check_test')
        health_check_interval = module.params.get('health_check_interval')
        health_check_path = module.params.get('health_check_path')
        health_check_parse = module.params.get('health_check_parse')
        persistence = module.params.get('persistence')
        persistence_time = module.params.get('persistence_time')
        method = module.params.get('method')
        datacenter = module.params.get('datacenter')
        rules = module.params.get('rules')
        wait = module.params.get('wait')
        wait_timeout = module.params.get('wait_timeout')
        wait_interval = module.params.get('wait_interval')

        load_balancer_rules = []

        datacenter_id = None
        if datacenter is not None:
            datacenter_id = get_datacenter(oneandone_conn, datacenter)
            if datacenter_id is None:
                module.fail_json(
                    msg='datacenter %s not found.' % datacenter)

        for rule in rules:
            load_balancer_rule = oneandone.client.LoadBalancerRule(
                protocol=rule['protocol'],
                port_balancer=rule['port_balancer'],
                port_server=rule['port_server'],
                source=rule['source'])
            load_balancer_rules.append(load_balancer_rule)

        _check_mode(module, True)
        load_balancer_obj = oneandone.client.LoadBalancer(
            health_check_path=health_check_path,
            health_check_parse=health_check_parse,
            name=name,
            description=description,
            health_check_test=health_check_test,
            health_check_interval=health_check_interval,
            persistence=persistence,
            persistence_time=persistence_time,
            method=method,
            datacenter_id=datacenter_id
        )

        load_balancer = oneandone_conn.create_load_balancer(
            load_balancer=load_balancer_obj,
            load_balancer_rules=load_balancer_rules
        )

        if wait:
            wait_for_resource_creation_completion(oneandone_conn,
                                                  OneAndOneResources.load_balancer,
                                                  load_balancer['id'],
                                                  wait_timeout,
                                                  wait_interval)

        load_balancer = get_load_balancer(oneandone_conn, load_balancer['id'], True)  # refresh
        changed = True if load_balancer else False

        _check_mode(module, False)

        return (changed, load_balancer)
    except Exception as ex:
        module.fail_json(msg=str(ex))


def remove_load_balancer(module, oneandone_conn):
    """
    Removes a load_balancer.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    try:
        lb_id = module.params.get('name')
        load_balancer_id = get_load_balancer(oneandone_conn, lb_id)
        if module.check_mode:
            if load_balancer_id is None:
                _check_mode(module, False)
            _check_mode(module, True)
        load_balancer = oneandone_conn.delete_load_balancer(load_balancer_id)

        changed = True if load_balancer else False

        return (changed, {
            'id': load_balancer['id'],
            'name': load_balancer['name']
        })
    except Exception as ex:
        module.fail_json(msg=str(ex))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth_token=dict(
                type='str',
                default=os.environ.get('ONEANDONE_AUTH_TOKEN')),
            api_url=dict(
                type='str',
                default=os.environ.get('ONEANDONE_API_URL')),
            load_balancer=dict(type='str'),
            name=dict(type='str'),
            description=dict(type='str'),
            health_check_test=dict(
                choices=HEALTH_CHECK_TESTS),
            health_check_interval=dict(type='str'),
            health_check_path=dict(type='str'),
            health_check_parse=dict(type='str'),
            persistence=dict(type='bool'),
            persistence_time=dict(type='str'),
            method=dict(
                choices=METHODS),
            datacenter=dict(
                choices=DATACENTERS),
            rules=dict(type='list', default=[]),
            add_server_ips=dict(type='list', default=[]),
            remove_server_ips=dict(type='list', default=[]),
            add_rules=dict(type='list', default=[]),
            remove_rules=dict(type='list', default=[]),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            wait_interval=dict(type='int', default=5),
            state=dict(type='str', default='present', choices=['present', 'absent', 'update']),
        ),
        supports_check_mode=True
    )

    if not HAS_ONEANDONE_SDK:
        module.fail_json(msg='1and1 required for this module')

    if not module.params.get('auth_token'):
        module.fail_json(
            msg='auth_token parameter is required.')

    if not module.params.get('api_url'):
        oneandone_conn = oneandone.client.OneAndOneService(
            api_token=module.params.get('auth_token'))
    else:
        oneandone_conn = oneandone.client.OneAndOneService(
            api_token=module.params.get('auth_token'), api_url=module.params.get('api_url'))

    state = module.params.get('state')

    if state == 'absent':
        if not module.params.get('name'):
            module.fail_json(
                msg="'name' parameter is required for deleting a load balancer.")
        try:
            (changed, load_balancer) = remove_load_balancer(module, oneandone_conn)
        except Exception as ex:
            module.fail_json(msg=str(ex))
    elif state == 'update':
        if not module.params.get('load_balancer'):
            module.fail_json(
                msg="'load_balancer' parameter is required for updating a load balancer.")
        try:
            (changed, load_balancer) = update_load_balancer(module, oneandone_conn)
        except Exception as ex:
            module.fail_json(msg=str(ex))

    elif state == 'present':
        for param in ('name', 'health_check_test', 'health_check_interval', 'persistence',
                      'persistence_time', 'method', 'rules'):
            if not module.params.get(param):
                module.fail_json(
                    msg="%s parameter is required for new load balancers." % param)
        try:
            (changed, load_balancer) = create_load_balancer(module, oneandone_conn)
        except Exception as ex:
            module.fail_json(msg=str(ex))

    module.exit_json(changed=changed, load_balancer=load_balancer)


if __name__ == '__main__':
    main()
