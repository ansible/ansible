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
module: ecs_slb_lb
short_description: Create, Delete, Enable or Disable Server Load Balancer in ECS
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
  alicloud_region:
    description:
      - The Aliyun Cloud region to use. If not specified then the value of the `ALICLOUD_REGION`, `ACS_REGION`, 
        `ACS_DEFAULT_REGION` or `ECS_REGION` environment variable, if any, is used.
    required: false
    default: null
    aliases: ['acs_region', 'ecs_region', 'region']
  status:
    description: The state of the instance after operating.
    required: false
    default: 'present'
    aliases: [ 'state' ]
    choices: [ 'present', 'absent', 'active', 'inactive' ]
            map operation ['create', 'delete', 'enable', 'disable']

function create Server Load Balancer
    description: create a Server Load Balancer
    state: present
    options:
      load_balancer_name:
        description:
          - The name of the server load balancer
        default: null
        required: false
        aliases: [ 'name' ]
      load_balancer_id:
        description:
          - This parameter is required when user wants to perform edit operation in Load Balancer
        default: null
        required: false
        aliases: [ 'ecs_slb' ]
      address_type:
        description:
          - The address type of the SLB.
        default: internet
        required: false
        aliases: [ 'scheme' ]
        choices: ['internet', 'intranet']
      vswitch_id:
        description:
          - The vswitch id of the VPC instance.
        default: null
        required: false
        aliases: ['subnet_id', 'subnet']
      internet_charge_type:
        description:
          - The charge type of internet.
        default: 'paybytraffic'
        required: false
        choices: ['paybybandwidth', 'paybytraffic']
      master_zone_id:
        description:
          - The main usable area ID of the created Load Balancer can be found by the DescribeZone interface
        default: null
        required: false
        choices: []
      slave_zone_id:
        description:
          - The ID of the standby zone of the created Load Balancer can be found on the DescribeZone interface
        default: null
        required: false
        choices: []
      bandwidth:
        description:
          - Bandwidth peak of the public network instance charged per fixed bandwidth
        required: false
        default: 1
        choices: [ 1-1000 Mbps ]
      listeners:
        description:
          - List of ports/protocols for this SLB to listen on (see example)
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - protocol (required:true; default: null) - options are http, https, udp, tcp
            - listener_port (required:true; default: null; aliases:['load_balancer_port']) - Port used by the Server
              Load Balancer instance frontend
            - backend_server_port (required:false; default: null; aliases: ['instance_port']) - Server Load Balancer
              instance's backend port.
            - bandwidth (required:true; default: null) - Peak bandwidth of the monitor. Value: -1 / 1-1000 Mbps
            - scheduler (required:false; default: 'wrr'; choices:['wrr', 'wlc']) - Scheduling algorithm.
            - stickiness
                description: Configure sticky or non-stick session
                  - dictionary for the SLB Listener Stickiness
                  - '[{"key":"value", "key":"value"}]', keys allowed:
                    - enabled (required:true; default: null; choices:['on', 'off']) - Whether to enable session hold
                    - type (required:depends; default: null; choices:['insert', 'server']; aliases:['session_type'])
                      - How cookies are handled
                    - expiration (required:depends; aliases:['cookie_timeout']) - The cookie timeout period
                    - cookie (required:depends; aliases:['cookie_timeout']) - The cookie that is configured on the
                      server
            - health_check
                description: Configure the health check
                  - dictionary for the SLB Listener Health check
                  - '[{"key":"value", "key":"value"}]', keys allowed:
                    - domain (required:false; default: null) - The domain name used for the health check
                    - uri (required:true; default: null; aliases:['ping_path']) - URI used for health check
                    - connect_port (required:true; default: null; aliases:['ping_port']) - Port used for health checks
                    - healthy_threshold (required:true; default: null) - Threshold determining result of the health
                      check is success
                    - unhealthy_threshold (required:true; default: null;) - Threshold determining the result of the
                      health check is fail
                    - timeout (required:true; default: null; aliases['response_timeout']) - Maximum timeout of each
                      health check response
                    - interval (required:true; default: null) - Time interval of health checks
                    - http_code (required:false; default: null;) - Normal health check HTTP status codes
            - ssl_certificate_id (required:false; default: null) - Security certificate ID.
              This Parameter is required when protocol is https
            - gzip (required:false; default: 'on'; choices:['on', 'off']) - Gzip compression is turned on, will open a
              specific file type compression; will not close any file type compression
        default: null
        required: false
        aliases: []
      purge_listeners:
        description:
          - Purge existing listeners on SLB that are not found in listeners
        default: true
        required: false
      instance_ids:
        description:
          - List of instance ids to attach to this SLB
        default: null
        required: false
      purge_instance_ids:
        description:
          - Purge existing instance ids on SLB that are not found in instance_ids
        required: false
        default: true
      validate_certs:
        description:
          - When set to "no", SSL certificates will not be validated.
        required: false
        default: "yes"
        choices: ["yes", "no"]
        aliases: []
      tags:
        description:
          - An associative array of stickness policy settings. Policy will be applied to all listeners ( see example )
        required: false
      wait:
        description:
          - Wait for the SLB instance to be 'running' before returning
        required: false
        default: "no"
        choices: [ "yes", "no" ]
      wait_timeout:
        description:
          - how long before wait gives up, in seconds
        required: false
        default: 300

function modify Server Load Balancer Internet Specification
    description: modify SLB Internet Specification such as charging mode, bandwidth
    status: present
    options:
      load_balancer_id:
        description:
          - The List of unique ID of a Server Load Balancer instance
        required: true
        aliases: [ 'ecs_slb' ]
      internet_charge_type:
        description:
          - Charging mode for the public network instance
        required: false
        choices: ['paybybandwidth', 'paybytraffic']
        default: 'paybytraffic'
      bandwidth:
        description:
          - Bandwidth peak of the public network instance charged per fixed bandwidth
        required: false
        default: 1
        choices: [ 1-1000 Mbps ]

function delete Server Load Balancer
    description: delete a Server Load Balancer
    status: absent
    options:
      load_balancer_id:
        description:
          - The List of unique ID of a Server Load Balancer instance
        required: true
        aliases: [ 'ecs_slb' ]

function set Server Load Balancer Status (Enable/Disable)
    description: change status of Server Load Balancer
    state: active/inactive
    options:
      load_balancer_id:
        description:
          - The List of unique ID of a Server Load Balancer instance
        required: true
      status:
        description:
          - Status of an Server Load Balancer instance.
        required: true
        choices: ['inactive', 'active']

function set Server Load Balancer Name (Alias)
    description: change name/alias of Server Load Balancer
    state: present
    options:
      load_balancer_id:
        description:
          - Id of Server Load Balancer
        default: null
        required: true
        aliases: [ 'ecs_slb' ]
      load_balancer_name:
        description:
          - The name of the server load balancer
        default: null
        required: true
        aliases: [ 'name' ]
"""

EXAMPLES = """
# Basic provisioning example to create Load Balancer
- name: create server load balancer add listeners and add backend server
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-beijing
    load_balancer_name: demo_slb
    address_type: internet
    internet_charge_type: paybytraffic
    state: present
  tasks:
    - name: create server load balancer add listeners and add backend server
      ecs_slb_lb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        load_balancer_name: '{{ load_balancer_name }}'
        address_type: '{{ address_type }}'
        internet_charge_type: '{{ internet_charge_type }}'
        state: '{{ state }}'
      register: result
    - debug: var=result

# Advanced provisioning example to create Load Balancer with Listeners and Backend Servers
- name: create server load balancer, add listeners and add backend server
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-beijing
    master_zone_id: cn-beijing-a
    slave_zone_id: cn-beijing-b
    load_balancer_name: demo_slb
    scheme: internet
    internet_charge_type: paybytraffic
    bandwidth: 1
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
        bandwidth: 1
        scheduler: wrr
        gzip: "on"
        health_check:
          ping_port: 80
          ping_path: /index.html
          response_timeout: 5
          interval: 30
          unhealthy_threshold: 2
          healthy_threshold: 10
          http_code: http_2xx
        stickiness:
          enabled: "on"
          session_type: insert
          cookie: 300
          cookie_timeout: 1
    vswitch_id: xxxxxxxxxx
    instance_ids:
      - xxxxxxxxxx
      - xxxxxxxxxx
    state: present
  tasks:
    - name: create server load balancer add listeners and add backend server
      ecs_slb_lb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        master_zone_id: '{{ master_zone_id }}'
        slave_zone_id: '{{ slave_zone_id }}'
        load_balancer_name: '{{ load_balancer_name }}'
        scheme: '{{ scheme }}'
        internet_charge_type: '{{ internet_charge_type }}'
        bandwidth: '{{ bandwidth }}'
        listeners: '{{ listeners }}'
        instance_ids: '{{ instance_ids }}'
        vswitch_id: '{{ vswitch_id }}'
        state: '{{ state }}'
      register: result
    - debug: var=result

# Basic provisioning example to Modify  SLB Internet Specification
- name: modify server load balancer internet specification
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-beijing
    load_balancer_id: xxxxxxxxxx
    internet_charge_type: paybytraffic
    bandwidth: 5
  tasks:
    - name: modify server load balancer internet specification
      ecs_slb_lb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        load_balancer_id: '{{ load_balancer_id }}'
        internet_charge_type: '{{ internet_charge_type }}'
        bandwidth: '{{ bandwidth }}'
      register: result
    - debug: var=result

# Basic provisioning example to Delete Server Load Balancer
- name: delete server load balancer
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-beijing
    load_balancer_id: xxxxxxxxxx
    status : absent
  tasks:
    - name: delete server load balancer
      ecs_slb_lb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        load_balancer_id: '{{ load_balancer_id }}'
        status: '{{ status }}'
      register: result
    - debug: var=result

# Basic provisioning example to set  SLB Status
- name: set server load balancer status
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-beijing
    load_balancer_id: xxxxxxxxxx
    status: active
  tasks:
    - name: set server load balancer
      ecs_slb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        load_balancer_id: '{{ load_balancer_id }}'
        status: '{{ status }}'
      register: result
    - debug: var=result

# Basic provisioning example to set Server Load Balancer Name
- name: set server load balancer name
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-beijing
    load_balancer_id: xxxxxxxxxx
    load_balancer_name: slb_new_name
    status : present
  tasks:
    - name: set server load balancer name
      ecs_slb_lb:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        load_balancer_id: '{{ load_balancer_id }}'
        load_balancer_name: '{{ load_balancer_name }}'
        status: '{{ status }}'
      register: result
    - debug: var=result
"""


HAS_FOOTMARK = False

try:
    from footmark.exception import SLBResponseError
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def create_load_balancer(module, slb, load_balancer_name=None, address_type=None, vswitch_id=None,
                         internet_charge_type=None, master_zone_id=None, slave_zone_id=None, bandwidth=None,
                         listeners=None, instance_ids=None, validate_cert=None, tags=None, wait=None,
                         wait_timeout=None):
    """
    Create LoadBalancer; generate Server Load Balancer instances, and allocate service addresses and LoadBalancerIds
     according to parameters
    :param module: Ansible module object
    :param slb: Authenticated slb connection object
    :param load_balancer_name: The name of the LoadBalancer
    :param address_type: The AddressType of the LoadBalancer, It allows 'internet' or 'intranet'
        Default: internet
    :param vswitch_id: The vswitch id of VPC instance
    :param internet_charge_type: Charging mode for the public network instance, It allows 'paybybandwidth'
        or 'paybytraffic'. Default: paybytraffic
    :param master_zone_id: Name of master availability zones to enable on this LoadBalancer
    :param  slave_zone_id: Name of slave availability zones to enable on this load balancer
    :param bandwidth: Bandwidth peak of the public network instance charged per fixed bandwidth
        value ranges from 1 to 1000 and default is 1
    :param listeners: list of Listeners to the LoadBalancer
    :param instance_ids: List of Instance ids attached to the LoadBalancer
    :param validate_cert:
    :param tags:
    :param wait: After execution of method whether it has to wait for some time interval
    :param wait_timeout: Time interval of waiting
    :return: Retrun created LoadBalancer details
    """
    changed = False

    if (master_zone_id is None) and (slave_zone_id is not None):
        module.fail_json(msg="provide master_zone_id first")

    try:
        changed, result = slb.create_load_balancer(load_balancer_name=load_balancer_name, address_type=address_type,
                                                   vswitch_id=vswitch_id, internet_charge_type=internet_charge_type,
                                                   master_zone_id=master_zone_id, slave_zone_id=slave_zone_id,
                                                   bandwidth=bandwidth, listeners=listeners, instance_ids=instance_ids,
                                                   validate_cert=validate_cert, tags=tags, wait=wait,
                                                   wait_timeout=wait_timeout)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except SLBResponseError as e:
        module.fail_json(msg='Unable to create server load balancer, error: {0}'.format(e))

    return changed, result


def add_listeners(module, slb, load_balancer_id=None, purge_listeners=None, listeners=None):
    """
    Add listener to an existing LoadBalancer
    :param module: Ansible module object
    :param slb: Authenticated slb connection object
    :param load_balancer_id: Id of LoadBalancer
    :param purge_listeners: Whether to remove existing listener or not
    :param listeners: List of listeners to the LoadBalancer
    :return: Return a RequestId of request
    """
    changed = False
    try:
        changed, result = slb.add_listeners(load_balancer_id=load_balancer_id, purge_listener=purge_listeners,
                                            listeners=listeners)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except SLBResponseError as e:
        module.fail_json(msg='Unable to add listener, error: {0}'.format(e))

    return changed, result


def modify_slb_internet_spec(module, slb, load_balancer_id, internet_charge_type=None, bandwidth=None):
    """
    Modify the LoadBalancer specification; modify the specification of the Server Load Balancer instance according
     to parameters
    :param module: Ansible module object
    :param slb: Authenticated slb connection object
    :param load_balancer_id: Id of LoadBalancer
    :param internet_charge_type: Charging mode for the public network instance, It allows 'paybybandwidth'
        or 'paybytraffic'. Default: paybytraffic
    :param bandwidth: Bandwidth peak of the public network instance charged per fixed bandwidth
    :return: Return a RequestId of request
    """
    changed = False
    result = []
    try:
        changed, result = slb.modify_slb_internet_spec(load_balancer_id=load_balancer_id,
                                                       internet_charge_type=internet_charge_type,
                                                       bandwidth=bandwidth)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except SLBResponseError as e:
        module.fail_json(msg='Unable to create server load balancer, error: {0}'.format(e))

    return changed, result


def delete_load_balancer(module, slb, load_balancer_id):
    """
     Method Added to Delete Load Balancer
    :param module: Ansible module object
    :param slb: Authenticated slb connection object
    :param load_balancer_id: The Id of the Load Balancer
    :return: delete load balancer instance
    """
    changed = False
    try:
        changed, result = slb.delete_load_balancer(slb_id=load_balancer_id)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)
        changed = True

    except SLBResponseError as e:
        module.fail_json(msg='Unable to delete server load balancer, error: {0}'.format(e))

    return changed, result


def set_load_balancer_status(module, slb, load_balancer_id, load_balancer_status):
    """
     Method Added to Set Load Balancer Status
    :param module: Ansible module object
    :param slb: Authenticated slb connection object
    :param load_balancer_id: The Id of the Load Balancer
    :param load_balancer_status: Default status is active otherwise inactive
    :return: set load balancer instance  status
    """
    changed = False
    try:
        changed, result = slb.set_load_balancer_status(load_balancer_id=load_balancer_id,
                                                       load_balancer_status=load_balancer_status)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)
        changed = True

    except SLBResponseError as e:
        module.fail_json(msg='Unable to set server load balancer status, error: {0}'.format(e))

    return changed, result


def set_load_balancer_name(module, slb, load_balancer_id, load_balancer_name):
    """
    Configure the alias of LoadBalancer
    :param module: Ansible module object
    :param slb: Authenticated slb connection object
    :param load_balancer_id: The unique ID of an Server Load Balancer instance
    :param load_balancer_name: Displayed name of an Server Load Balancer instance
    :return: Return a RequestId of request
    """
    changed = False
    try:
        changed, result = slb.set_load_balancer_name(load_balancer_id=load_balancer_id,
                                                     load_balancer_name=load_balancer_name)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)
        changed = True

    except SLBResponseError as e:
        module.fail_json(msg='Unable to set server load balancer name, error: {0}'.format(e))
    return changed, result


def purge_add_backend_server(module, slb, load_balancer_id, instance_ids=None, purge_instance_ids=None):
    """
    Remove existing Backend Server and add new Backend Server
    :param module: Ansible module object
    :param slb: Authenticated slb connection object
    :param load_balancer_id: Id of LoadBalancer
    :param instance_ids: List of Backend Server/ Instance Ids
    :param purge_instance_ids: Whether to remove existing backend server or not
    :return: Details of newly added Backend Servers
    """
    changed = False
    try:
        changed, results = slb.purge_add_backend_server(load_balancer_id=load_balancer_id, instance_ids=instance_ids,
                                                        purge_instance_ids=purge_instance_ids)

        if 'error' in (''.join(str(results))).lower():
            module.fail_json(changed=changed, msg=results)

    except SLBResponseError as e:
        module.fail_json(msg='Unable to add backend server, error: {0}'.format(e))

    return changed, results


def add_listener_and_backend_server(module, slb, load_balancer_id, purge_listeners=None, listeners=None,
                                    instance_ids=None, purge_instance_ids=None):
    """
    Add Listeners and Backend Servers to Load Balancer
    :param module: Ansible module object
    :param slb: Authenticated slb connection object
    :param load_balancer_id: Id of LoadBalancer    
    :param purge_listeners: Whether to remove existing listener or not
    :param listeners: List of listeners to the LoadBalancer
    :param instance_ids: List of Backend Server/ Instance Ids
    :param purge_instance_ids: Whether to remove existing backend server or not
    :return: Details of newly added Listeners and Backend Servers
    """
    changed = False
    results = []

    try:
        # Call to add_listeners method
        listener_changed, listener_result = slb.add_listeners(
            load_balancer_id=load_balancer_id, purge_listener=purge_listeners, listeners=listeners)
        results.append(listener_result)

        # Call to purge_add_backend_server method
        instance_ids_changed, instance_ids_result = slb.purge_add_backend_server(
            load_balancer_id=load_balancer_id, instance_ids=instance_ids, purge_instance_ids=purge_instance_ids)
        results.append(instance_ids_result)
        
        if (listener_changed is True) or (instance_ids_changed is True):
            changed = True

        if 'error' in (''.join(str(results))).lower():
            module.fail_json(changed=changed, msg=results)

    except SLBResponseError as e:
        module.fail_json(msg='Unable to add Listener and Backend Server, error: {0}'.format(e))

    return changed, results


def manage_present_state(module, slb):
    """
    Manage all operations done in present state
    :param module: Ansible module object
    :param slb: Authenticated slb connection object
    :return: Returns a response of executed method
    """
    load_balancer_id = module.params['load_balancer_id']
    load_balancer_name = module.params['load_balancer_name']
    address_type = module.params['address_type']
    vswitch_id = module.params['vswitch_id']
    master_zone_id = module.params['master_zone_id']
    slave_zone_id = module.params['slave_zone_id']
    internet_charge_type = module.params['internet_charge_type']
    bandwidth = module.params['bandwidth']
    listeners = module.params['listeners']
    purge_listeners = module.params['purge_listeners']
    instance_ids = module.params['instance_ids']
    purge_instance_ids = module.params['purge_instance_ids']
    validate_certs = module.params['validate_certs']
    tags = module.params['tags']
    wait = module.params['wait']
    wait_timeout = module.params['wait_timeout']

    if not load_balancer_id:
        # Call to create server load balancer method
        (changed, result) = create_load_balancer(module=module, slb=slb, load_balancer_name=load_balancer_name,
                                                 address_type=address_type, vswitch_id=vswitch_id,
                                                 internet_charge_type=internet_charge_type,
                                                 master_zone_id=master_zone_id, slave_zone_id=slave_zone_id,
                                                 bandwidth=bandwidth, listeners=listeners,
                                                 instance_ids=instance_ids,
                                                 validate_cert=validate_certs, tags=tags, wait=wait,
                                                 wait_timeout=wait_timeout)
        module.exit_json(changed=changed, result=result)
    else:
        if (listeners is not None) and (instance_ids is not None):
            # Call to add_listener_and_backend_server method
            (changed, result) = add_listener_and_backend_server(
                module=module, slb=slb, load_balancer_id=load_balancer_id, purge_listeners=purge_listeners,
                listeners=listeners, instance_ids=instance_ids, purge_instance_ids=purge_instance_ids)
            module.exit_json(changed=changed, result=result)
            
        elif load_balancer_name is not None:
            # Call to set_load_balancer_name method
            (changed, result) = set_load_balancer_name(module=module, slb=slb,
                                                       load_balancer_id=load_balancer_id,
                                                       load_balancer_name=load_balancer_name)
            module.exit_json(changed=changed, result=result)

        elif instance_ids is not None:
            # Call to purge_add_backend_server method
            (changed, result) = purge_add_backend_server(module=module, slb=slb,
                                                         load_balancer_id=load_balancer_id,
                                                         instance_ids=instance_ids,
                                                         purge_instance_ids=purge_instance_ids)
            module.exit_json(changed=changed, result=result)

        elif listeners is not None:
            # Call to add_listeners method
            (changed, result) = add_listeners(module=module, slb=slb, load_balancer_id=load_balancer_id,
                                              purge_listeners=purge_listeners, listeners=listeners)
            module.exit_json(changed=changed, result=result)

        else:
            # Call to modify_slb_internet_spec method
            (changed, result) = modify_slb_internet_spec(module, slb, load_balancer_id=load_balancer_id,
                                                         internet_charge_type=internet_charge_type,
                                                         bandwidth=bandwidth)
            module.exit_json(changed=changed, result=result)


def main():
    if HAS_FOOTMARK is False:
        print("Footmark required for this module")
        sys.exit(1)
    else:
        argument_spec = ecs_argument_spec()
        argument_spec.update(dict(
            internet_charge_type=dict(choices=['paybybandwidth', 'paybytraffic'], default='paybytraffic'),
            group_id=dict(),
            zone_id=dict(aliases=['acs_zone', 'ecs_zone']),
            status=dict(default='present', aliases=['state'], choices=[
                'present', 'modify_spec', 'absent', 'modify_status', 'modify_name', 'active', 'inactive']),
            load_balancer_name=dict(aliases=['name']),
            load_balancer_id=dict(aliases=['ecs_slb']),
            address_type=dict(default='internet', aliases=['scheme']),
            bandwidth=dict(default=1, type='int'),
            listeners=dict(type='list'),
            purge_listeners=dict(type='bool', default=True),
            vswitch_id=dict(aliases=['subnet_id', 'subnet']),
            zones=dict(type='list'),
            instance_ids=dict(type='list'),
            purge_instance_ids=dict(type='bool', default=False),
            attributes=dict(type='list'),
            load_balancer_status=dict(default='active'),
            validate_certs=dict(type='bool', default=True),
            master_zone_id=dict(),
            slave_zone_id=dict(),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default='300'),
            name=dict(),
            tags=dict(type='list')
        ))

        module = AnsibleModule(argument_spec=argument_spec)
        slb = slb_connect(module)
        status = module.params['status']

        if status == "present":
            manage_present_state(module=module, slb=slb)

        elif status == "absent":
            load_balancer_id = module.params['load_balancer_id']

            if not load_balancer_id:
                module.fail_json(msg='Load Balancer ID is required to delete load balancer')

            changed, result = delete_load_balancer(module=module, slb=slb, load_balancer_id=load_balancer_id)
            module.exit_json(changed=changed, result=result)

        elif status in ['active', 'inactive']:
            load_balancer_id = module.params['load_balancer_id']

            changed, result = set_load_balancer_status(module=module, slb=slb, load_balancer_id=load_balancer_id,
                                                       load_balancer_status=status)
            module.exit_json(changed=changed, result=result)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.alicloud_ecs import *

# import ECSConnection
main()
