#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
author:
  - Matt Hite (@mhite)
  - Tim Rupp (@caphrim007)
notes:
  - "Requires BIG-IP software version >= 11"
  - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
  - "Best run as a local_action in your playbook"
requirements:
  - bigsuds
options:
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
  monitor_type:
    description:
      - Monitor rule type when monitors > 1
    version_added: "2.2"
    required: False
    default: null
    choices: ['and_list', 'm_of_n']
    aliases: []
  quorum:
    description:
      - Monitor quorum value when monitor_type is m_of_n
    version_added: "2.2"
    required: False
    default: null
    choices: []
    aliases: []
  monitors:
    description:
      - Monitor template name list. Always use the full path to the monitor.
    version_added: "2.2"
    required: False
    default: null
    choices: []
    aliases: []
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
extends_documentation_fragment: f5
'''

EXAMPLES = '''
- name: Add node
  bigip_node:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "present"
      partition: "Common"
      host: "10.20.30.40"
      name: "10.20.30.40"

# Note that the BIG-IP automatically names the node using the
# IP address specified in previous play's host parameter.
# Future plays referencing this node no longer use the host
# parameter but instead use the name parameter.
# Alternatively, you could have specified a name with the
# name parameter when state=present.

- name: Add node with a single 'ping' monitor
  bigip_node:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "present"
      partition: "Common"
      host: "10.20.30.40"
      name: "mytestserver"
      monitors:
        - /Common/icmp
  delegate_to: localhost

- name: Modify node description
  bigip_node:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "present"
      partition: "Common"
      name: "10.20.30.40"
      description: "Our best server yet"
  delegate_to: localhost

- name: Delete node
  bigip_node:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "absent"
      partition: "Common"
      name: "10.20.30.40"

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
  bigip_node:
      server: "lb.mydomain.com"
      user: "admin"
      password: "mysecret"
      state: "present"
      session_state: "disabled"
      monitor_state: "disabled"
      partition: "Common"
      name: "10.20.30.40"
'''


def node_exists(api, address):
    # hack to determine if node exists
    result = False
    try:
        api.LocalLB.NodeAddressV2.get_object_status(nodes=[address])
        result = True
    except bigsuds.OperationFailed as e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result


def create_node_address(api, address, name):
    try:
        api.LocalLB.NodeAddressV2.create(
            nodes=[name],
            addresses=[address],
            limits=[0]
        )
        result = True
        desc = ""
    except bigsuds.OperationFailed as e:
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
    except bigsuds.OperationFailed as e:
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


def get_monitors(api, name):
    result = api.LocalLB.NodeAddressV2.get_monitor_rule(nodes=[name])[0]
    monitor_type = result['type'].split("MONITOR_RULE_TYPE_")[-1].lower()
    quorum = result['quorum']
    monitor_templates = result['monitor_templates']
    return (monitor_type, quorum, monitor_templates)


def set_monitors(api, name, monitor_type, quorum, monitor_templates):
    monitor_type = "MONITOR_RULE_TYPE_%s" % monitor_type.strip().upper()
    monitor_rule = {'type': monitor_type, 'quorum': quorum, 'monitor_templates': monitor_templates}
    api.LocalLB.NodeAddressV2.set_monitor_rule(nodes=[name],
                                               monitor_rules=[monitor_rule])


def main():
    monitor_type_choices = ['and_list', 'm_of_n']

    argument_spec = f5_argument_spec()

    meta_args = dict(
        session_state=dict(type='str', choices=['enabled', 'disabled']),
        monitor_state=dict(type='str', choices=['enabled', 'disabled']),
        name=dict(type='str', required=True),
        host=dict(type='str', aliases=['address', 'ip']),
        description=dict(type='str'),
        monitor_type=dict(type='str', choices=monitor_type_choices),
        quorum=dict(type='int'),
        monitors=dict(type='list')
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if module.params['validate_certs']:
        import ssl
        if not hasattr(ssl, 'SSLContext'):
            module.fail_json(msg='bigsuds does not support verifying certificates with python < 2.7.9.  Either update python or set validate_certs=False on the task')

    server = module.params['server']
    server_port = module.params['server_port']
    user = module.params['user']
    password = module.params['password']
    state = module.params['state']
    partition = module.params['partition']
    validate_certs = module.params['validate_certs']

    session_state = module.params['session_state']
    monitor_state = module.params['monitor_state']
    host = module.params['host']
    name = module.params['name']
    address = fq_name(partition, name)
    description = module.params['description']
    monitor_type = module.params['monitor_type']
    if monitor_type:
        monitor_type = monitor_type.lower()
    quorum = module.params['quorum']
    monitors = module.params['monitors']
    if monitors:
        monitors = []
        for monitor in module.params['monitors']:
                monitors.append(fq_name(partition, monitor))

    # sanity check user supplied values
    if state == 'absent' and host is not None:
        module.fail_json(msg="host parameter invalid when state=absent")

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
        api = bigip_api(server, user, password, validate_certs, port=server_port)
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
                    module.fail_json(msg="host parameter required when "
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
                    if monitors:
                        set_monitors(api, address, monitor_type, quorum, monitors)
                else:
                    # check-mode return value
                    result = {'changed': True}
            else:
                # node exists -- potentially modify attributes
                if host is not None:
                    if get_node_address(api, address) != host:
                        module.fail_json(msg="Changing the node address is "
                                             "not supported by the API; "
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
                if monitors:
                    t_monitor_type, t_quorum, t_monitor_templates = get_monitors(api, address)
                    if (t_monitor_type != monitor_type) or (t_quorum != quorum) or (set(t_monitor_templates) != set(monitors)):
                        if not module.check_mode:
                            set_monitors(api, address, monitor_type, quorum, monitors)
                        result = {'changed': True}
    except Exception as e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
