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
module: oneandone_firewall_policy
short_description: Configure 1&1 firewall policy.
description:
     - Create, remove, reconfigure, update firewall policies.
       This module has a dependency on 1and1 >= 1.0
version_added: "2.5"
options:
  state:
    description:
      - Define a firewall policy state to create, remove, or update.
    required: false
    default: 'present'
    choices: [ "present", "absent", "update" ]
  auth_token:
    description:
      - Authenticating API token provided by 1&1.
    required: true
  api_url:
    description:
      - Custom API URL. Overrides the
        ONEANDONE_API_URL environment variable.
    required: false
  name:
    description:
      - Firewall policy name used with present state. Used as identifier (id or name) when used with absent state.
        maxLength=128
    required: true
  firewall_policy:
    description:
      - The identifier (id or name) of the firewall policy used with update state.
    required: true
  rules:
    description:
      - A list of rules that will be set for the firewall policy.
        Each rule must contain protocol parameter, in addition to three optional parameters
        (port_from, port_to, and source)
  add_server_ips:
    description:
      - A list of server identifiers (id or name) to be assigned to a firewall policy.
        Used in combination with update state.
    required: false
  remove_server_ips:
    description:
      - A list of server IP ids to be unassigned from a firewall policy. Used in combination with update state.
    required: false
  add_rules:
    description:
      - A list of rules that will be added to an existing firewall policy.
        It is syntax is the same as the one used for rules parameter. Used in combination with update state.
    required: false
  remove_rules:
    description:
      - A list of rule ids that will be removed from an existing firewall policy. Used in combination with update state.
    required: false
  description:
    description:
      - Firewall policy description. maxLength=256
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
  -  "Amel Ajdinovic (@aajdinov)"
  -  "Ethan Devenport (@edevenport)"
'''

EXAMPLES = '''

# Provisioning example. Create and destroy a firewall policy.

- oneandone_firewall_policy:
    auth_token: oneandone_private_api_key
    name: ansible-firewall-policy
    description: Testing creation of firewall policies with ansible
    rules:
     -
       protocol: TCP
       port_from: 80
       port_to: 80
       source: 0.0.0.0
    wait: true
    wait_timeout: 500

- oneandone_firewall_policy:
    auth_token: oneandone_private_api_key
    state: absent
    name: ansible-firewall-policy

# Update a firewall policy.

- oneandone_firewall_policy:
    auth_token: oneandone_private_api_key
    state: update
    firewall_policy: ansible-firewall-policy
    name: ansible-firewall-policy-updated
    description: Testing creation of firewall policies with ansible - updated

# Add server to a firewall policy.

- oneandone_firewall_policy:
    auth_token: oneandone_private_api_key
    firewall_policy: ansible-firewall-policy-updated
    add_server_ips:
     - server_identifier (id or name)
     - server_identifier #2 (id or name)
    wait: true
    wait_timeout: 500
    state: update

# Remove server from a firewall policy.

- oneandone_firewall_policy:
    auth_token: oneandone_private_api_key
    firewall_policy: ansible-firewall-policy-updated
    remove_server_ips:
     - B2504878540DBC5F7634EB00A07C1EBD (server's IP id)
    wait: true
    wait_timeout: 500
    state: update

# Add rules to a firewall policy.

- oneandone_firewall_policy:
    auth_token: oneandone_private_api_key
    firewall_policy: ansible-firewall-policy-updated
    description: Adding rules to an existing firewall policy
    add_rules:
     -
       protocol: TCP
       port_from: 70
       port_to: 70
       source: 0.0.0.0
     -
       protocol: TCP
       port_from: 60
       port_to: 60
       source: 0.0.0.0
    wait: true
    wait_timeout: 500
    state: update

# Remove rules from a firewall policy.

- oneandone_firewall_policy:
    auth_token: oneandone_private_api_key
    firewall_policy: ansible-firewall-policy-updated
    remove_rules:
     - rule_id #1
     - rule_id #2
     - ...
    wait: true
    wait_timeout: 500
    state: update

'''

RETURN = '''
firewall_policy:
    description: Information about the firewall policy that was processed
    type: dict
    sample: '{"id": "92B74394A397ECC3359825C1656D67A6", "name": "Default Policy"}'
    returned: always
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oneandone import (
    get_firewall_policy,
    get_server,
    OneAndOneResources,
    wait_for_resource_creation_completion
)

HAS_ONEANDONE_SDK = True

try:
    import oneandone.client
except ImportError:
    HAS_ONEANDONE_SDK = False


def _check_mode(module, result):
    if module.check_mode:
        module.exit_json(
            changed=result
        )


def _add_server_ips(module, oneandone_conn, firewall_id, server_ids):
    """
    Assigns servers to a firewall policy.
    """
    try:
        attach_servers = []

        for _server_id in server_ids:
            server = get_server(oneandone_conn, _server_id, True)
            attach_server = oneandone.client.AttachServer(
                server_id=server['id'],
                server_ip_id=next(iter(server['ips'] or []), None)['id']
            )
            attach_servers.append(attach_server)

        if module.check_mode:
            if attach_servers:
                return True
            return False

        firewall_policy = oneandone_conn.attach_server_firewall_policy(
            firewall_id=firewall_id,
            server_ips=attach_servers)
        return firewall_policy
    except Exception as e:
        module.fail_json(msg=str(e))


def _remove_firewall_server(module, oneandone_conn, firewall_id, server_ip_id):
    """
    Unassigns a server/IP from a firewall policy.
    """
    try:
        if module.check_mode:
            firewall_server = oneandone_conn.get_firewall_server(
                firewall_id=firewall_id,
                server_ip_id=server_ip_id)
            if firewall_server:
                return True
            return False

        firewall_policy = oneandone_conn.remove_firewall_server(
            firewall_id=firewall_id,
            server_ip_id=server_ip_id)
        return firewall_policy
    except Exception as e:
        module.fail_json(msg=str(e))


def _add_firewall_rules(module, oneandone_conn, firewall_id, rules):
    """
    Adds new rules to a firewall policy.
    """
    try:
        firewall_rules = []

        for rule in rules:
            firewall_rule = oneandone.client.FirewallPolicyRule(
                protocol=rule['protocol'],
                port_from=rule['port_from'],
                port_to=rule['port_to'],
                source=rule['source'])
            firewall_rules.append(firewall_rule)

        if module.check_mode:
            firewall_policy_id = get_firewall_policy(oneandone_conn, firewall_id)
            if (firewall_rules and firewall_policy_id):
                return True
            return False

        firewall_policy = oneandone_conn.add_firewall_policy_rule(
            firewall_id=firewall_id,
            firewall_policy_rules=firewall_rules
        )
        return firewall_policy
    except Exception as e:
        module.fail_json(msg=str(e))


def _remove_firewall_rule(module, oneandone_conn, firewall_id, rule_id):
    """
    Removes a rule from a firewall policy.
    """
    try:
        if module.check_mode:
            rule = oneandone_conn.get_firewall_policy_rule(
                firewall_id=firewall_id,
                rule_id=rule_id)
            if rule:
                return True
            return False

        firewall_policy = oneandone_conn.remove_firewall_rule(
            firewall_id=firewall_id,
            rule_id=rule_id
        )
        return firewall_policy
    except Exception as e:
        module.fail_json(msg=str(e))


def update_firewall_policy(module, oneandone_conn):
    """
    Updates a firewall policy based on input arguments.
    Firewall rules and server ips can be added/removed to/from
    firewall policy. Firewall policy name and description can be
    updated as well.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    try:
        firewall_policy_id = module.params.get('firewall_policy')
        name = module.params.get('name')
        description = module.params.get('description')
        add_server_ips = module.params.get('add_server_ips')
        remove_server_ips = module.params.get('remove_server_ips')
        add_rules = module.params.get('add_rules')
        remove_rules = module.params.get('remove_rules')

        changed = False

        firewall_policy = get_firewall_policy(oneandone_conn, firewall_policy_id, True)
        if firewall_policy is None:
            _check_mode(module, False)

        if name or description:
            _check_mode(module, True)
            firewall_policy = oneandone_conn.modify_firewall(
                firewall_id=firewall_policy['id'],
                name=name,
                description=description)
            changed = True

        if add_server_ips:
            if module.check_mode:
                _check_mode(module, _add_server_ips(module,
                                                    oneandone_conn,
                                                    firewall_policy['id'],
                                                    add_server_ips))

            firewall_policy = _add_server_ips(module, oneandone_conn, firewall_policy['id'], add_server_ips)
            changed = True

        if remove_server_ips:
            chk_changed = False
            for server_ip_id in remove_server_ips:
                if module.check_mode:
                    chk_changed |= _remove_firewall_server(module,
                                                           oneandone_conn,
                                                           firewall_policy['id'],
                                                           server_ip_id)

                _remove_firewall_server(module,
                                        oneandone_conn,
                                        firewall_policy['id'],
                                        server_ip_id)
            _check_mode(module, chk_changed)
            firewall_policy = get_firewall_policy(oneandone_conn, firewall_policy['id'], True)
            changed = True

        if add_rules:
            firewall_policy = _add_firewall_rules(module,
                                                  oneandone_conn,
                                                  firewall_policy['id'],
                                                  add_rules)
            _check_mode(module, firewall_policy)
            changed = True

        if remove_rules:
            chk_changed = False
            for rule_id in remove_rules:
                if module.check_mode:
                    chk_changed |= _remove_firewall_rule(module,
                                                         oneandone_conn,
                                                         firewall_policy['id'],
                                                         rule_id)

                _remove_firewall_rule(module,
                                      oneandone_conn,
                                      firewall_policy['id'],
                                      rule_id)
            _check_mode(module, chk_changed)
            firewall_policy = get_firewall_policy(oneandone_conn, firewall_policy['id'], True)
            changed = True

        return (changed, firewall_policy)
    except Exception as e:
        module.fail_json(msg=str(e))


def create_firewall_policy(module, oneandone_conn):
    """
    Create a new firewall policy.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    try:
        name = module.params.get('name')
        description = module.params.get('description')
        rules = module.params.get('rules')
        wait = module.params.get('wait')
        wait_timeout = module.params.get('wait_timeout')
        wait_interval = module.params.get('wait_interval')

        firewall_rules = []

        for rule in rules:
            firewall_rule = oneandone.client.FirewallPolicyRule(
                protocol=rule['protocol'],
                port_from=rule['port_from'],
                port_to=rule['port_to'],
                source=rule['source'])
            firewall_rules.append(firewall_rule)

        firewall_policy_obj = oneandone.client.FirewallPolicy(
            name=name,
            description=description
        )

        _check_mode(module, True)
        firewall_policy = oneandone_conn.create_firewall_policy(
            firewall_policy=firewall_policy_obj,
            firewall_policy_rules=firewall_rules
        )

        if wait:
            wait_for_resource_creation_completion(
                oneandone_conn,
                OneAndOneResources.firewall_policy,
                firewall_policy['id'],
                wait_timeout,
                wait_interval)

        firewall_policy = get_firewall_policy(oneandone_conn, firewall_policy['id'], True)  # refresh
        changed = True if firewall_policy else False

        _check_mode(module, False)

        return (changed, firewall_policy)
    except Exception as e:
        module.fail_json(msg=str(e))


def remove_firewall_policy(module, oneandone_conn):
    """
    Removes a firewall policy.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    try:
        fp_id = module.params.get('name')
        firewall_policy_id = get_firewall_policy(oneandone_conn, fp_id)
        if module.check_mode:
            if firewall_policy_id is None:
                _check_mode(module, False)
            _check_mode(module, True)
        firewall_policy = oneandone_conn.delete_firewall(firewall_policy_id)

        changed = True if firewall_policy else False

        return (changed, {
            'id': firewall_policy['id'],
            'name': firewall_policy['name']
        })
    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth_token=dict(
                type='str',
                default=os.environ.get('ONEANDONE_AUTH_TOKEN'),
                no_log=True),
            api_url=dict(
                type='str',
                default=os.environ.get('ONEANDONE_API_URL')),
            name=dict(type='str'),
            firewall_policy=dict(type='str'),
            description=dict(type='str'),
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
            msg='The "auth_token" parameter or ' +
            'ONEANDONE_AUTH_TOKEN environment variable is required.')

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
                msg="'name' parameter is required to delete a firewall policy.")
        try:
            (changed, firewall_policy) = remove_firewall_policy(module, oneandone_conn)
        except Exception as e:
            module.fail_json(msg=str(e))

    elif state == 'update':
        if not module.params.get('firewall_policy'):
            module.fail_json(
                msg="'firewall_policy' parameter is required to update a firewall policy.")
        try:
            (changed, firewall_policy) = update_firewall_policy(module, oneandone_conn)
        except Exception as e:
            module.fail_json(msg=str(e))

    elif state == 'present':
        for param in ('name', 'rules'):
            if not module.params.get(param):
                module.fail_json(
                    msg="%s parameter is required for new firewall policies." % param)
        try:
            (changed, firewall_policy) = create_firewall_policy(module, oneandone_conn)
        except Exception as e:
            module.fail_json(msg=str(e))

    module.exit_json(changed=changed, firewall_policy=firewall_policy)


if __name__ == '__main__':
    main()
