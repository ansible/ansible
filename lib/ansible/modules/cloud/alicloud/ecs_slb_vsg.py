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
module: ecs_slb_vsg
short_description: Creates,remove VServer Groups and add, remove and modify VServer Group backend server
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
    description:
      -  status to creates or remove VServer Groups to SLB.
    choices: ["present", "absent"]
    required: false
    default: present
    aliases: [ 'state' ]

function create vservers group in SLB
    description: Create vservers group in SLB.
    status: present
    options:
      load_balancer_id:
        description:
          - The unique ID of a Server Load Balancer instance
        required: true
        default: null
        aliases: [ 'ecs_slb' ]
      vserver_group_name:
        description:
          - Virtual server group name
        required: true
        default: null
        aliases: []
      backend_servers:
        description:
          - List of hash/dictionary of backend servers to add in
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - server_id (required:true, description: Unique id of Instance to add)
            - port (required:true, description: The back-end server using the port, range: 1-65535)
            - weight (required:true; default: 100, description: Weight of the backend server, in the range of 1-100 )
        required: true

function set vservers group attribute
    description: Set vservers group attribute
    status: present
    options:
      vserver_group_id:
        description:
          - The unique identifier for the virtual server group.
        required: true
        default: null
        aliases: []
      vserver_group_name:
        description:
          - Virtual server group name.
        required: true
        default: null
        aliases: []
      backend_servers:
        description:
          - List of hash/dictionary of backend servers to set vserver group attribute
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - server_id (required:true, description: Unique id of Instance to add)
            - port (required:true, description: The back-end server using the port, range: 1-65535)
            - weight (required:true; default: 100, description: Weight of the backend server, in the range of 1-100 )
        required: false

function add vserver group backend server
    description: Add vserver group backend server
    status: present
    options:
      vserver_group_id:
        description:
          - The unique identifier for the virtual server group.
        required: true
        default: null
        aliases: []
      backend_servers:
        description:
          - List of hash/dictionary of backend servers to add vserver group backend server
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - server_id (required:true, description: Unique id of Instance to add)
            - port (required:true, description: The back-end server using the port, range: 1-65535)
            - weight (required:true; default: 100, description: Weight of the backend server, in the range of 1-100 )
        required: false

function remove vserver groups backend servers from SLB
    description: Remove vserver groups backend servers from SLB.
    status: present
    options:
      vserver_group_id:
        description:
          - The unique identifier for the virtual server group
        required: true
      purge_backend_servers:
        description:
          - List of hash/dictionary of backend servers to remove
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - server_id (required:true, description: Unique id of Instance to remove)
            - port (required:true, description: The back-end server using the port, range: 1-65535)
        required: true

function modify vserver groups backend servers in SLB
    description: Modify vserver groups backend servers in SLB.
    status: present
    options:
      vserver_group_id:
        description:
          - The unique identifier for the virtual server group
        required: true
      purge_backend_servers:
        description:
          - List of hash/dictionary of backend servers to remove
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - server_id (required:true, description: Unique id of Instance to remove)
            - port (required:true, description: The back-end server using the port, range: 1-65535)
      required: false
      backend_servers:
        description:
          - List of hash/dictionary of backend servers to modify
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - server_id (required:true, description: Unique id of Instance to add)
            - port (required:true, description: The back-end server using the port, range: 1-65535)
            - weight (required:true; default: 100, description: Weight of the backend server, in the range of 1-100 )
      required: false

function remove vservers group from SLB
    description: Remove vservers group from SLB.
    status: absent
    options:
      vserver_group_id:
        description:
          - The unique identifier for the virtual server group
        required: true
      load_balancer_id:
        description:
          - The unique ID of a Server Load Balancer instance
        required: true
        default: null
        aliases: [ 'ecs_slb' ]

"""
EXAMPLES = '''
#
# provisioning to create VServer Group in SLB
#

# basic provisioning example to create VServer Group in SLB
- name: Create VServer Group in SLB
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: ap-southeast-1
    status: present
    load_balancer_id: xxxxxxxxxx
    vserver_group_name: test
    backend_servers:
       -  server_id: xxxxxxxxxx
          port: 8080
          weight: 100
  tasks:
    - name: Create VServer Group in SLB
      ecs_slb_vsg:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        load_balancer_id: '{{ load_balancer_id }}'
        vserver_group_name: '{{ vserver_group_name }}'
        backend_servers: '{{ backend_servers }}'
      register: result
    - debug: var=result

# basic provisioning example to set VServer Group Attribute
- name: Set VServer Group Attribute
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: ap-southeast-1
    status: present
    vserver_group_name: test123
    vserver_group_id: xxxxxxxxxx
    backend_servers:
       -  server_id: xxxxxxxxxx
          port: 8080
          weight: 50
  tasks:
    - name: Set VServer Group Attribute
      ecs_slb_vsg:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        status: '{{ status }}'
        vserver_group_id: '{{ vserver_group_id }}'
        vserver_group_name: '{{ vserver_group_name }}'
        backend_servers: '{{ backend_servers }}'
      register: result
    - debug: var=result

# basic provisioning example to add VServer Group backend server
- name: add VServer Group backend server
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: ap-southeast-1
    status: present
    vserver_group_id: xxxxxxxxxx
    backend_servers:
       -  server_id: xxxxxxxxxx
          port: 8070
          weight: 100
  tasks:
    - name: add VServer Group backend server
      ecs_slb_vsg:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        status: '{{ status }}'
        vserver_group_id: '{{ vserver_group_id}}'
        backend_servers: '{{ backend_servers }}'
      register: result
    - debug: var=result

# basic provisioning example to remove VServer Group backend server
- name: remove VServer Group backend server
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: ap-southeast-1
    status: present
    vserver_group_id: xxxxxxxxxx
    purge_backend_servers:
       -  server_id: xxxxxxxxxx
          port: 8070
  tasks:
    - name: remove VServer Group backend server
      ecs_slb_vsg:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        status: '{{ status }}'
        vserver_group_id: '{{ vserver_group_id }}'
        purge_backend_servers: '{{ purge_backend_servers }}'
      register: result
    - debug: var=result

# basic provisioning example to modify VServer Group backend server
- name: modify VServer Group backend server
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: ap-southeast-1
    status: present
    vserver_group_id: xxxxxxxxxx
    purge_backend_servers:
       -  server_id: xxxxxxxxxx
          port: 8070
    backend_servers:
       -  server_id: xxxxxxxxxx
          port: 8070
          weight: 90
       -  server_id: xxxxxxxxxx
          port: 8090
          weight: 70
  tasks:
    - name: modify VServer Group backend server
      ecs_slb_vsg:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        status: '{{ status }}'
        vserver_group_id: '{{ vserver_group_id }}'
        purge_backend_servers: '{{ purge_backend_servers }}'
        backend_servers: '{{ backend_servers }}'
      register: result
    - debug: var=result

# basic provisioning example to delete VServer Group
- name: delete VServer Group
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: ap-southeast-1
    status: absent
    vserver_group_id: xxxxxxxxxx
    load_balancer_id: xxxxxxxxxx
  tasks:
    - name: delete VServer Group
      ecs_slb_vsg:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        status: '{{ status }}'
        load_balancer_id: '{{ load_balancer_id }}'
        vserver_group_id: '{{ vserver_group_id }}'
      register: result
    - debug: var=result

'''
# region Import packages
from footmark.exception import SLBResponseError
# endregion


# region Methods
def create_vserver_group(module, slb, ecs, load_balancer_id, vserver_group_name, backend_servers):
    """
    Method Call to create VServer Group

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param ecs: authenticated ecs connection object
    :param load_balancer_id: The Id of the Load Balancer
    :param vserver_group_name: Virtual server group name
    :param backend_servers:
        - List of hash/dictionary of backend servers to add in
        - '[{"key":"value", "key":"value"}]', keys allowed:
        - server_id (required:true, description: Unique id of Instance to add)
        - port (required:true, description: The back-end server using the port, range: 1-65535)
        - weight (required:true, description: Weight of the backend server, in the range of 1-100 default: 100)
    :return:
        changed: Changed is true if VServer Group is created else false
        result: return dictionary which contains backend server, vserver group id and vserver group name
    """
    changed = False
    create_flag = True
    result = []

    if not load_balancer_id:
        module.fail_json(msg='Load Balancer Id is required to create vserver group')
    if vserver_group_name:        
        if len(vserver_group_name) > 256 or len(vserver_group_name) < 2:
            module.fail_json(msg='The VServerGroupName length is limited to 2-256 characters')
    else:
        module.fail_json(msg='VServerGroupName is required to create vserver group')    
             
    if not backend_servers:
        module.fail_json(msg='Backend Server is required to create vserver group')

    try:
        for backend_server in backend_servers:
            instance_info = ecs.describe_instances(instance_ids=[str(backend_server["server_id"])])
            if not instance_info:
                create_flag = False
                result.append({"Error Code": "obtainIpFail",
                               "Error Message": "obtainIpFail, please make sure that"
                               " "+str(backend_server["server_id"])+" ECS exists in the specified region"})

        if create_flag:
            changed, result = slb.create_vserver_group(load_balancer_id=load_balancer_id,
                                                       vserver_group_name=vserver_group_name,
                                                       backend_servers=backend_servers)
        
            if 'error' in (''.join(str(result))).lower():
                module.fail_json(changed=changed, msg=result)
        else:
            module.fail_json(changed=changed, msg=result)
        
    except SLBResponseError as e:
        module.fail_json(msg='Unable to Create VServer Group due to following error :{0}'.format(e))
    return changed, result


def set_vserver_group_attribute(module, slb, ecs, vserver_group_id, vserver_group_name=None, backend_servers=None):
    """
    Method Call to Set VServer Group Attributes

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param ecs: authenticated ecs connection object
    :param vserver_group_id: The unique identifier for the virtual server group
    :param vserver_group_name:Virtual server group name
    :param backend_servers:
        - List of hash/dictionary of backend servers to set vserver group attribute
        - '[{"key":"value", "key":"value"}]', keys allowed:
        - server_id (required:true, description: Unique id of Instance to add)
        - port (required:true, description: The back-end server using the port, range: 1-65535)
        - weight (required:true, description: Weight of the backend server, in the range of 1-100 default: 100)
    :return:
        changed: Changed is true if set VServer Group attribute else false
        result: return dictionary which contains backend server , vserver group id and vserver group name
    """
    changed = False
    set_flag = True
    result = []
    if vserver_group_name:        
        if len(vserver_group_name) > 256 or len(vserver_group_name) < 2:
            module.fail_json(msg='The VServerGroupName length is limited to 2-256 characters')
    else:
        module.fail_json(msg='VServerGroupName is required to create vserver group') 
    if not vserver_group_id:
        module.fail_json(msg='VServerGroupId is required to set vserver group attribute')
    try:
        for backend_server in backend_servers:
            instance_info = ecs.describe_instances(instance_ids=[str(backend_server["server_id"])])
            if not instance_info:
                set_flag = False
                result.append({"Error Code": "obtainIpFail",
                               "Error Message": "obtainIpFail, please make sure that "
                                                ""+str(backend_server["server_id"])+" ECS exists in "
                                                                                    "the specified region"})
        if set_flag:
            changed_vsgbs, result_vsgbs = slb.describe_vservergroup_backendserver(vserver_group_id, backend_servers)  
            if changed_vsgbs:                        
                changed, result = slb.set_vservergroup_attribute(vserver_group_id=vserver_group_id,
                                                                 vserver_group_name=vserver_group_name,
                                                                 backend_servers=backend_servers)
                if 'error' in (''.join(str(result))).lower():
                    module.fail_json(changed=changed, msg=result)
            else:
                module.fail_json(changed=changed_vsgbs, msg=result_vsgbs)
        else:
            module.fail_json(changed=changed, msg=result)
        
    except SLBResponseError as e:
        module.fail_json(msg='Unable to Set VServer Group Attribute due to following error :{0}'.format(e))
    return changed, result


def add_vservergroup_backend_server(module, slb, ecs, vserver_group_id, backend_servers):
    """
    Method Call to Add VServer Group Backend Server

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param ecs: authenticated ecs connection object
    :param vserver_group_id: The unique identifier for the virtual server group
    :param backend_servers:
        - List of hash/dictionary of backend servers to add in
        - '[{"key":"value", "key":"value"}]', keys allowed:
        - server_id (required:true, description: Unique id of Instance to add)
        - port (required:true, description: The back-end server using the port, range: 1-65535)
        - weight (required:true, description: Weight of the backend server, in the range of 1-100 default: 100)
    :return:
        changed: Changed is true if VServer Group Backend Server is Added else false
        result: return dictionary which contains backend server and vserver group id
    """
    changed = False
    add_flag = True
    result = []
    if not vserver_group_id:
        module.fail_json(msg='VServerGroupId is required to add backend server')

    if not backend_servers:
        module.fail_json(msg='Backend Servers is required to add backend server')
    try:
        for backend_server in backend_servers:
            instance_info = ecs.describe_instances(instance_ids=[str(backend_server["server_id"])])
            if not instance_info:
                add_flag = False
                result.append({"Error Code": "obtainIpFail",
                               "Error Message": "obtainIpFail, please make sure that "
                                                ""+str(backend_server["server_id"])+" ECS exists"
                                                                                    " in the specified region"})

        if add_flag:  
            changed_vsgbs, result_vsgbs = slb.describe_vservergroup_backendserver_to_add(vserver_group_id,
                                                                                         backend_servers)
            if changed_vsgbs:   
                changed, result = slb.add_vservergroup_backend_server(vserver_group_id=vserver_group_id,
                                                                      backend_servers=backend_servers)
                if 'error' in (''.join(str(result))).lower():
                    module.fail_json(changed=changed, msg=result)
            else:
                module.fail_json(changed=changed_vsgbs, msg=result_vsgbs)
        else:
            module.fail_json(changed=changed, msg=result)
    except SLBResponseError as e:
        module.fail_json(msg='Unable to Add VServer Group BackEndServer due to following error :{0}'.format(e))
    return changed, result
    
    
def remove_vserver_group_backend_server(module, slb, ecs, vserver_group_id, purge_backend_servers):
    """
    Method call to Remove VServer Group Backend Server

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param ecs: authenticated ecs connection object
    :param vserver_group_id:  Uniquely identifies the virtual server group
    :param purge_backend_servers:
      - List of hash/dictionary of backend servers to be removed
      - '[{"key":"value", "key":"value"}]', keys allowed:
        - server_id (required:true, description: Unique id of Instance to add)
        - port (required:true, description: The back-end server using the port, range: 1-65535)
    :return:
        changed: Changed is true if VServer Group Backend Server is Removed else false
        result: return dictionary which contains backend server , vserver group id
    """
    changed = False
    remove_flag = True
    result = []
    if not vserver_group_id:
        module.fail_json(msg='VServerGroupId is required to remove vserver group backend server')

    if not purge_backend_servers:
        module.fail_json(msg='Purge Backend Server is required to remove vserver group backend server')
    try:
        for purge_backend_server in purge_backend_servers:
            instance_info = ecs.describe_instances(instance_ids=[str(purge_backend_server["server_id"])])
            if not instance_info:
                remove_flag = False
                result.append({"Error Code": "obtainIpFail",
                               "Error Message": "obtainIpFail,"
                                                " please make sure that "
                                                ""+str(purge_backend_server["server_id"])+" ECS exists in "
                                                                                          "the specified region"})

        if remove_flag:
            changed_vsgbs, result_vsgbs = slb.describe_vservergroup_backendserver(vserver_group_id,
                                                                                  purge_backend_servers)
            if changed_vsgbs:
                changed, result = slb.remove_vserver_group_backend_server(vserver_group_id=vserver_group_id,
                                                                          purge_backend_servers=purge_backend_servers)   
    
                if 'error' in (''.join(str(result))).lower():
                    module.fail_json(msg=result)  
            else:
                module.fail_json(changed=changed_vsgbs, msg=result_vsgbs)
        else:
            module.fail_json(changed=changed, msg=result)                     
    
    except SLBResponseError as e:
        module.fail_json(msg='Unable to remove vserver group, error: {0}'.format(e))
    return changed, result


def modify_vserver_group_backend_server(module, slb, ecs, vserver_group_id, purge_backend_servers, backend_servers):
    """
    Method call to Modify VServer Group Backend Server

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param ecs: authenticated ecs connection object
    :param vserver_group_id: Virtual server group Id
    :param purge_backend_servers:
      - List of hash/dictionary of backend servers to remove
      - '[{"key":"value", "key":"value"}]', keys allowed:
        - server_id (required:true, description: Unique id of Instance to add)
        - port (required:true, description: The back-end server using the port, range: 1-65535)
    :param backend_servers:
    - List of hash/dictionary of backend servers to add in
    - '[{"key":"value", "key":"value"}]', keys allowed:
    - server_id (required:true, description: Unique id of Instance to add)
    - port (required:true, description: The back-end server using the port, range: 1-65535)
    - weight (required:true, description: Weight of the backend server, in the range of 1-100 default: 100)

    :return:
        changed: Changed is true if VServer Group Backend Server is Modified
        result: return dictionary which contains backend server , vserver group id
    """
    changed = False
    changed_vsg = False
    result_vsgs = []
    modify_flag = True
    setvsg_flag = True
    result = []
    if not vserver_group_id:
        module.fail_json(msg='VServerGroupId is required for modifying vserver group')
    if not purge_backend_servers:
        module.fail_json(msg='Purge Backend Server is required for modifying vserver group')
    if not backend_servers:
        module.fail_json(msg='Backend Server is required for modifying vserver group')

    try:
        for purge_backend_server in purge_backend_servers:
            instance_info = ecs.describe_instances(instance_ids=[str(purge_backend_server["server_id"])])
            if not instance_info:
                modify_flag = False
                result.append({"Error Code": "obtainIpFail",
                               "Error Message": "obtainIpFail, please make sure that"
                                                ""+str(purge_backend_server["server_id"])+" ECS exists "
                                                                                          "in the specified region"})
        for backend_server in backend_servers:
            instance_info = ecs.describe_instances(instance_ids=[str(backend_server["server_id"])])
            if not instance_info:
                modify_flag = False
                result.append({"Error Code": "obtainIpFail",
                               "Error Message": "obtainIpFail, please make sure that "
                                                ""+str(backend_server["server_id"])+" ECS exists in "
                                                                                    "the specified region"})

        if modify_flag:
            changed_vsgpbs, result_vsgpbs = slb.describe_vservergroup_backendserver(vserver_group_id,
                                                                                    purge_backend_servers)
            if changed_vsgpbs:
                changed, result = \
                    slb.modify_vserver_group_backend_server(vserver_group_id=vserver_group_id,
                                                            purge_backend_servers=purge_backend_servers,
                                                            backend_servers=backend_servers)
                if 'error' in (''.join(str(result))).lower():
                    module.fail_json(msg=result)                  
            else:
                module.fail_json(changed=changed_vsgpbs, msg=result_vsgpbs)
        else:
            module.fail_json(changed=changed, msg=result)
        
    except SLBResponseError as e:
        module.fail_json(msg='unable to modify vserver group due to following error: {0}'.format(e))
    return changed, result


def delete_vserver_group(module, slb, load_balancer_id, vserver_group_id):
    """
    Method Call to Delete VServer Group

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param load_balancer_id: The Id of the Load Balancer
    :param vserver_group_id: Virtual server group Id
    :return:
        changed: Changed is true if VServer Group is Removed
        result: return result of operation
    """
    changed = False
    if not vserver_group_id:
        module.fail_json(msg='VServerGroupID is required to Delete vserver group')
    if not load_balancer_id:
        module.fail_json(msg='LoadBalancerID is required to Delete vserver group')

    try:
        changed, result = slb.delete_vserver_group(load_balancer_id=load_balancer_id, vserver_group_id=vserver_group_id)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)
         
    except SLBResponseError as e:
        module.fail_json(msg='Unable to delete virtual server group due to following error :{0}'.format(e))
    return changed, result


def perform_operation_on_present_state(module, slb, ecs):
    """
    Method Call to Perform Operation on Present State

    :param module: Ansible module object
    :param slb: authenticated slb connection object
    :param ecs: authenticated ecs connection object
    :return:
        changed: Changed is true if any changes occurs 
        result: return result of operation
    """
    vserver_group_name = module.params['vserver_group_name']
    backend_servers = module.params['backend_servers']
    load_balancer_id = module.params['load_balancer_id']
    vserver_group_id = module.params['vserver_group_id'] 
    purge_backend_servers = module.params['purge_backend_servers']

    if load_balancer_id is not None and vserver_group_name is not None and backend_servers is not None:
        operation_flag = 'CreateVSG'
    elif vserver_group_id is not None and vserver_group_name is not None and backend_servers is not None:
        operation_flag = 'SetAttributeVSG'
    elif vserver_group_id is not None and backend_servers is not None and purge_backend_servers is not None:
        operation_flag = 'ModifyVSG'
    elif vserver_group_id is not None and purge_backend_servers is not None:
        operation_flag = 'RemoveBS'
    elif vserver_group_id is not None and backend_servers is not None:
        operation_flag = 'AddBS'
    else:
        module.fail_json(msg=[
            {'To create vserver group': 'load_balancer_id, '
                                        'vserver_group_name and backend_servers parameters are required.'},
            {' To set vserver group attribute': 'vserver_group_id, '
                                                'vserver_group_name and backend_servers parameters are required.'},
            {' To add backend server': 'vserver_group_id and '
                                       'backend_servers parameters are required.'},
            {' To modify backend server': 'vserver_group_id, '
                                          'backend_servers, purge_backend_servers '
                                          'parameters are required.'},
            {' To remove backend server': 'vserver_group_id and '
                                          'purge_backend_servers parameters are required.'}])

    if backend_servers:
        for key in backend_servers:
            if 'server_id' not in key:
                module.fail_json(msg='server_id key is required in BackendServer to perform operation')
            if 'port' not in key:
                module.fail_json(msg='port key is required in BackendServer to perform operation')
            if 'weight' not in key:
                module.fail_json(msg='weight key is required in BackendServer to perform operation')
            if not key['server_id']:
                module.fail_json(msg='server_id is required in BackendServer to perform operation')
            if not key['port']:
                module.fail_json(msg='port is required in BackendServer to perform operation')
            if len(backend_servers) > 20:
                    module.fail_json(msg='Backend Server List should not be greater than 20 to perform operation') 
            if not str(key['weight']).isdigit():                    
                    module.fail_json(msg='The weight must be an integer value, entered value is {0}'.format(
                        str(key['weight'])))   
            if not str(key['port']).isdigit():                    
                    module.fail_json(msg='The port must be an integer value, entered value is {0}'.format(
                        str(key['port'])))                                                 
            if key['port']:
                if int(key['port']) < 1 or int(key['port']) > 65535:
                    module.fail_json(msg='Valid port range is 1-65535')                
            if key['weight']:
                if int(key['weight']) < 0 or int(key['weight']) > 100:
                    module.fail_json(msg='Valid weight range is 0-100')

    if purge_backend_servers:
        for key in purge_backend_servers:
            if 'server_id' not in key:
                module.fail_json(msg='server_id key is required in BackendServer to perform operation')
            if 'port' not in key:
                module.fail_json(msg='port key is required in BackendServer to perform operation')
            if not key['server_id']:
                module.fail_json(msg='server_id is required in BackendServer to perform operation')
            if not key['port']:
                module.fail_json(msg='port is required in BackendServer to perform operation')
            if len(purge_backend_servers) > 20:
                    module.fail_json(msg='Purge Backend Server List should '
                                         'not be greater than 20 to perform operation')
            if not str(key['port']).isdigit():                    
                    module.fail_json(msg='The port must be an integer value, entered value is {0}'.format(
                        str(key['port']))) 
            if key['port']:
                if int(key['port']) < 1 or int(key['port']) > 65535:
                    module.fail_json(msg='Valid port range is 1-65535') 
                                
    if operation_flag == 'CreateVSG':
        (changed, result) = create_vserver_group(module=module, slb=slb, ecs=ecs, load_balancer_id=load_balancer_id,
                                                 vserver_group_name=vserver_group_name,
                                                 backend_servers=backend_servers)
        module.exit_json(changed=changed, result=result)

    elif operation_flag == 'SetAttributeVSG':
        (changed, result) = set_vserver_group_attribute(module=module, slb=slb, ecs=ecs,
                                                        vserver_group_id=vserver_group_id,
                                                        vserver_group_name=vserver_group_name,
                                                        backend_servers=backend_servers)
        module.exit_json(changed=changed, result=result)

    elif operation_flag == 'AddBS':
        (changed, result) = add_vservergroup_backend_server(module=module, slb=slb, ecs=ecs,
                                                            vserver_group_id=vserver_group_id,
                                                            backend_servers=backend_servers)
        module.exit_json(changed=changed, result=result)

    elif operation_flag == 'RemoveBS':
        (changed, result) = remove_vserver_group_backend_server(module=module, slb=slb, ecs=ecs,
                                                                vserver_group_id=vserver_group_id,
                                                                purge_backend_servers=purge_backend_servers)
        module.exit_json(changed=changed, result=result)

    elif operation_flag == 'ModifyVSG':
        (changed, result) = modify_vserver_group_backend_server(module=module, slb=slb, ecs=ecs, 
                                                                vserver_group_id=vserver_group_id,
                                                                purge_backend_servers=purge_backend_servers,
                                                                backend_servers=backend_servers)
        module.exit_json(changed=changed, result=result)

# endregion


# region Main module
def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        status=dict(default='present', aliases=['state'], choices=["present", "absent"]),
        load_balancer_id=dict(aliases=['ecs_slb']),
        vserver_group_name=dict(),
        backend_servers=dict(type='list'),
        vserver_group_id=dict(),
        purge_backend_servers=dict(type='list')
    ))

    module = AnsibleModule(argument_spec=argument_spec)
    slb = slb_connect(module)
    ecs = ecs_connect(module)
    region, acs_connect_kwargs = get_acs_connection_info(module)
    
    # set value
    status = module.params['status']
    load_balancer_id = module.params['load_balancer_id']
    vserver_group_id = module.params['vserver_group_id']

    if status == 'present':
        perform_operation_on_present_state(module=module, slb=slb, ecs=ecs)

    if status == 'absent':
        (changed, result) = delete_vserver_group(module=module, slb=slb, load_balancer_id=load_balancer_id,
                                                 vserver_group_id=vserver_group_id)
        module.exit_json(changed=changed, result=result)

# endregion


# region Execution Start
# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.alicloud_ecs import *

# import ECSConnection
main()
# endregion
