#!/usr/bin/python
#
# Copyright 2017 Alibaba Group Holding Limited.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see http://www.gnu.org/licenses/.


ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'core',
                    'version': '1.0'}


DOCUMENTATION = """
---
module: ecs_slb
description:
  - Returns information about the backend servers.
  - Will be marked changed when called only if state is changed.
short_description: Creates, sets and remove backend servers and describe backend servers health status of SLB
common options:
  alicloud_access_key:
    description:
      - Aliyun Cloud access key. If not set then the value of the `ALICLOUD_ACCESS_KEY`, `ACS_ACCESS_KEY_ID`, 
        `ACS_ACCESS_KEY` or `ECS_ACCESS_KEY` environment variable is used.
    required: false
    default: null
    aliases: ['acs_access_key', 'ecs_access_key','access_key']
  alicloud_secret_key:
    description:
      - Aliyun Cloud secret key. If not set then the value of the `ALICLOUD_SECRET_KEY`, `ACS_SECRET_ACCESS_KEY`,
        `ACS_SECRET_KEY`, or `ECS_SECRET_KEY` environment variable is used.
    required: false
    default: null
    aliases: ['acs_secret_access_key', 'ecs_secret_key','secret_key']
  status:
    description: Create, set, remove or describe backend server health status of an slb
    required: false
    default: 'present'
    choices: ['present', 'absent', 'check']
    aliases: [ 'state' ]

function add set backend servers to SLB
    description: add and set backend servers to SLB.
    status: present
    options:
      load_balancer_id:
        description:
          - The unique ID of a Server Load Balancer instance
        required: true
        aliases: [ 'ecs_slb']
      backend_servers:
        description:
          - List of hash/dictionary of backend servers to add or set in
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - server_id (required:true)
            - weight (required:false; default: 100 )
        required: true

function remove backend servers from SLB
    description: remove backend servers from SLB.
    status: absent
    options:
      load_balancer_id:
        description:
          - The unique ID of a Server Load Balancer instance
        required: true
        aliases: [ 'ecs_slb']
      backend_servers:
        description:
          - List of of backend server ids to remove from SLB
        required: true


function describe health status of backend servers in SLB
    description: Describe health status of backend servers in SLB.
    status: check
    options:
      load_balancer_id:
        description:
          - The unique ID of a Server Load Balancer instance
        required: true
        aliases: [ 'ecs_slb']
      ports:
        description:
          - list ports used by the Server Load Balancer instance frontend to describe health status for
        required: false
"""

EXAMPLES = '''
#
# Provisioning new add or remove Backend Server from SLB
#

Basic example to add backend server to load balancer instance
- name: add backend server
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
  tasks:
    - name: add backend server
      ecs_slb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        load_balancer_id: 'xxxxxxxxxx'
        backend_servers:
          - server_id: xxxxxxxxxx
            weight: 70
          - server_id: xxxxxxxxxx


Basic example to set backend server of load balancer instance
- name: set backend server
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
  tasks:
    - name: set backend server
      ecs_slb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        load_balancer_id: 'xxxxxxxxxx'
        backend_servers:
          - server_id: xxxxxxxxxx
            weight: 50
          - server_id: xxxxxxxxxx
            weight: 80

Basic example to remove backend servers from load balancer instance
- name: remove backend servers
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
  tasks:
    - name: remove backend servers
      ecs_slb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        load_balancer_id: 'xxxxxxxxxx'
        status: absent
        backend_servers:
          - xxxxxxxxxx
          - xxxxxxxxxx

Basic example to describe backend server health status of load balancer instance
- name: describe backend server health status
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
  tasks:
    - name: describe backend server health status
      ecs_slb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        status: check
        load_balancer_id: 'xxxxxxxxxx'
        ports:
          - '80'
          - '120'
'''

from __builtin__ import isinstance

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.alicloud_ecs import *

import sys

try:
    from footmark.exception import SLBResponseError

    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def add_set_backend_servers(module, slb, load_balancer_id=None, backend_servers=None):
    """
    Add and/or Set backend servers to an slb

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param load_balancer_id: load balancer id to add/set backend servers to
    :param backend_servers: backend severs information to add/set
    :return: returns changed state, current added backend servers and custom message.
    """

    changed = False
    server_id_param = 'server_id'
    backend_servers_to_set = []
    backend_servers_to_add = []
    result = []
    current_backend_servers = []
    changed_after_add = False
    changed_after_set = False

    try:

        load_balancer_info = slb.describe_load_balancer_attribute(load_balancer_id)

        # Verifying if server load balancer Object is present
        if load_balancer_info:
            existing_backend_servers = str(load_balancer_info['BackendServers']['BackendServer'])

            # Segregating existing backend servers from new backend servers from the provided backend servers
            for backend_server in backend_servers:

                backend_server_string = backend_server[server_id_param] + '\''
                if backend_server_string in existing_backend_servers:
                    backend_servers_to_set.append(backend_server)
                else:
                    backend_servers_to_add.append(backend_server)

                    # Adding new backend servers if provided
            if len(backend_servers_to_add) > 0:
                changed_after_add, current_backend_servers_after_add, result_after_add \
                    = slb.add_backend_servers(load_balancer_id=load_balancer_id, backend_servers=backend_servers_to_add)

                result.extend(result_after_add)
                current_backend_servers.extend(current_backend_servers_after_add)

                # Setting exisiting backend servers if provided
            if len(backend_servers_to_set) > 0:
                changed_after_set, current_backend_servers_after_set, result_after_set \
                    = slb.set_backend_servers(load_balancer_id=load_balancer_id, backend_servers=backend_servers_to_set)
                result.extend(result_after_set)

                # If backend server result after set action is available then clearing actual list
                # and adding new result to it
                if len(current_backend_servers_after_set) > 0:
                    # Below operation clears list using slice operation
                    current_backend_servers[:] = []
                    current_backend_servers.extend(current_backend_servers_after_set)

            if changed_after_add or changed_after_set:
                changed = True

        else:
            module.fail_json(msg="Could not find provided load balancer instance")

        if 'error' in str(result).lower():
            module.fail_json(changed=changed, instance_backend_servers = current_backend_servers, msg=result)

    except SLBResponseError as ex:
        module.fail_json(msg='Unable to add backend servers, error: {0}'.format(ex))

    return changed, current_backend_servers, result


def remove_backend_servers(module, slb, load_balancer_id=None, backend_servers=None):
    """
    Remove backend servers from an slb

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param load_balancer_id: load balancer id to remove backend servers from
    :param backend_servers: list of backend server ids to remove from slb
    :return: returns changed state, current added backend servers and custom message.
    """

    changed = False
    current_backend_servers = []
    results = []

    try:

        changed = False

        changed, current_backend_servers, results = slb.remove_backend_servers(load_balancer_id = load_balancer_id,
                                                                               backend_server_ids = backend_servers)

        if 'error' in str(results).lower():
            module.fail_json(changed = False, msg=results)

    except SLBResponseError as ex:
        module.fail_json(msg='Unable to remove backend servers, error: {0}'.format(ex))

    return changed, current_backend_servers, results


def describe_backend_servers_health_status(module, slb, load_balancer_id=None, listener_ports=None):
    """
    Describe health status of added backend servers of an slb

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param load_balancer_id: load balancer id to remove backend servers from
    :param listener_ports: list of ports to for which backend server health status is required
    :return: returns backend servers health status and custom message
    """

    backend_servers_health_status = []
    results = []
    try:
        if listener_ports:
            for port in listener_ports:

                health_status, result = slb.describe_backend_servers_health_status(load_balancer_id=load_balancer_id,
                                                                                   port=port)
                backend_servers_health_status.extend(health_status)
                results.extend(result)
        else:
            backend_servers_health_status, results \
                = slb.describe_backend_servers_health_status(load_balancer_id=load_balancer_id)

        if 'error' in str(results).lower():
            module.fail_json(backend_servers_health_status=backend_servers_health_status, msg=results)

    except SLBResponseError as ex:
        module.fail_json(msg='Unable to describe backend servers health status, error: {0}'.format(ex))

    return backend_servers_health_status, results


def validate_backend_server_info(module, backend_servers, check_weight, default_weight=None):
    """
    Validate backend server information provided by user for add, set and remove action

    :param module: Ansible module object
    :param backend_servers: backend severs information to validate (list of dictionaries or string)
    :param check_weight: specifies whether to check for weight key in dictionary
    :param default_weight: assigns default weight, if provided, for a backend server to set/add
    """

    server_id_param = 'server_id'
    weight_param = 'weight'
    VALID_PARAMS = (server_id_param, weight_param)

    for backend_server in backend_servers:

        if check_weight:
            if isinstance(backend_server, dict) is False:
                module.fail_json(msg='Invalid backend_server parameter type [%s].' % type(backend_server))

            for k in backend_server:
                if k not in VALID_PARAMS:
                    module.fail_json(msg='Invalid backend_server parameter \'{}\''.format(k))

            server_id = get_alias_value(backend_server,[server_id_param])
            if server_id is None:
                module.fail_json(msg='server_id is mandatory')

            weight = get_alias_value(backend_server, [weight_param])

            if weight is None:
                if default_weight is not None:
                    backend_server[weight_param] = default_weight
                else:
                    module.fail_json(msg='Weight is mandatory')
            else:
                #verifying weight parameter for non numeral string and limit validation
                try:
                    w = int(weight)
                    if w < 1 or w > 100:
                        module.fail_json(msg='Invalid weight parameter.')
                except Exception as e:
                    module.fail_json(msg='Invalid weight parameter.')


        else:
            if isinstance(backend_server, str) is False:
                module.fail_json(msg='Invalid backend_server parameter type [%s].' % type(backend_server))


def get_alias_value(dictionary, aliases):
    """

    :param dictionary: a dictionary to check in for aliases
    :param aliases: list of keys to check in dictionary for value retrieval
    :return: returns value if alias found else none
    """

    if (dictionary and aliases) is not None:
        for alias in aliases:
            if alias in dictionary:
                return dictionary[alias]
        return None
    else:
        return None


def get_verify_listener_ports(module, listener_ports=None):
    """
    Validate and get listener ports

    :param module: Ansible module object
    :param listener_ports: list of ports to for which backend server health status is required
    :return: formatted listener ports
    """

    if listener_ports:
        if len(listener_ports) > 0:
            for port in listener_ports:

                try:
                    port = int(port)
                except Exception as ex:
                    module.fail_json(msg='Invalid port value')
        else:
            listener_ports = None

    return listener_ports


def main():

    if HAS_FOOTMARK is False:
        print("footmark required for this module")
        sys.exit(1)

    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        status=dict(choices=['present', 'absent', 'check'], aliases=['state'], default='present'),
        backend_servers=dict(type='list'),
        load_balancer_id=dict(required='True', aliases=['ecs_slb']),
        ports=dict(type='list', aliases=['port']),
    ))

    # handling region parameter which is not required by this module
    del argument_spec['alicloud_region']

    module = AnsibleModule(argument_spec=argument_spec)

    # handling region parameter which is required by common utils file to login but not required by this module
    module.params['alicloud_region'] = 'cn-hangzhou'

    slb = slb_connect(module)
    region, acs_connect_kwargs = get_acs_connection_info(module)

    state = module.params['status']
    backend_servers = module.params['backend_servers']
    load_balancer_id = module.params['load_balancer_id']
    listener_ports = module.params['ports']

    if state == 'present':

        if backend_servers and load_balancer_id:
            if len(backend_servers) > 0:

                validate_backend_server_info(module=module, backend_servers=backend_servers,
                                             check_weight=True, default_weight="100")

                changed, current_backend_servers, result \
                    = add_set_backend_servers(module, slb, load_balancer_id=load_balancer_id,
                                              backend_servers=backend_servers)

                module.exit_json(changed=changed, msg=result, instance_backend_servers=current_backend_servers)
            else:
                module.fail_json(msg='backend servers information is mandatory to perform action')
        else:
            module.fail_json(msg='load balancer id and backend servers information is mandatory to perform action')

    elif state == 'absent':

        if backend_servers and load_balancer_id:
            if len(backend_servers) > 0:

                validate_backend_server_info(module=module, backend_servers=backend_servers,
                                             check_weight=False)

                changed, current_backend_servers, result \
                    = remove_backend_servers(module, slb, load_balancer_id=load_balancer_id,
                                             backend_servers=backend_servers)

                module.exit_json(changed=changed, instance_backend_servers=current_backend_servers, msg=result)
            else:
                module.fail_json(msg='backend server ID(s) information is mandatory to perform action')
        else:
            module.fail_json(msg='load balancer id and backend server ID(s) information is mandatory to perform action')

    elif state == 'check':

        if load_balancer_id:

            listener_ports = get_verify_listener_ports(module, listener_ports)

            backend_servers_health_status, result = \
                describe_backend_servers_health_status(module, slb,
                                                       load_balancer_id=load_balancer_id, listener_ports=listener_ports)

            module.exit_json(backend_servers_health_status=backend_servers_health_status, msg=result)
        else:
            module.fail_json(msg='load balancer id is mandatory to perform action')


main()
