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

DOCUMENTATION = '''
---
module: ecs_disk
short_description: Create, Attach, Detach or Delete a disk in ECS
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
    description: The state of the disk after operation.
    required: false
    default: 'present'
    aliases: [ 'state' ]
    choices: ['present', 'absent'] map operation ['create', 'attach', 'detach', 'delete']

function: Create a disk in ECS
  description: Create a disk in ECS
  options:
      alicloud_zone:
        description: Aliyun availability zone ID in which to launch the disk
        required: true
        default: null
        aliases: [ 'acs_zone', 'ecs_zone', 'availability_zone', 'zone_id', 'zone' ]
      disk_name:
        description: name of disk to create in ECS
        required: false
        default: null
        aliases: [ 'name' ]
      description:
        description:
          - The value of disk description is blank by default. [2, 256] characters. The disk description will appear on the console. It cannot begin with http:// or https://.
        required: false
        default: null
        aliases: [ 'disk_description' ]
      disk_category:
        description: Category to use for the disk.
        required: false
        default: cloud
        aliases: ['volume_type', 'disk_type']
        choices: ['cloud', 'cloud_efficiency', 'cloud_ssd']
      size:
        description: Size of disk in GB
        required: false
        default: null
        aliases: ['volume_size', 'disk_size']
      snapshot_id:
        description:
          - Snapshots are used to create the data disk After this parameter is specified, Size is ignored. The actual size of the created disk is the size of the specified snapshot Snapshots from on or before July 15, 2013 cannot be used to create a disk
        required: false
        default: null
        aliases: ['snapshot']
      disk_tags:
        description:
          - A list of hash/dictionaries of instance tags, ['{"tag_key":"value", "tag_value":"value"}'], tag_key must be not null when tag_value isn't null
        required: false
        default: null
        aliases: ['tags']

function: Attach disk
  description: Attach disk to instance in ECS
  options:
      instance_id:
        description: The ID of the destination instance in ECS.
        required: true
        default: null
        aliases: ['instance']
      disk_id:
        description: The disk ID. The disk and Instance must be in the same zone.
        required: true
        default: null
        aliases: ['vol_id', 'id']
      device:
        description:
          - The value null indicates that the value is allocated by default, starting from /dev/xvdb to /dev/xvdz.
        required: false
        default: null
        aliases: ['device_name']
      delete_with_instance:
        description:
          - Whether or not the disk is released along with the instance. True/Yes indicates that when the instance is released, this disk will be released with it.False/No indicates that when the instance is released, this disk will be retained.
        required: false
        default: none
        aliases: ['delete_on_termination']
        choices: ["yes", "no"]

function: Detach disk
  description: Detach disk from instance in ECS
  options:
    instance_id:
        description: The ID of the destination instance in ECS.
        required: false
        default: null
        aliases: ['instance']
    disk_id:
        description: Id of disk to detach from instance in ECS.
        required: true
        default: null
        aliases: ['vol_id', 'id']


function: Delete disk
  description: Delete disk which is not in use
  options:
    disk_id:
        description: The ID of the disk device that needs to be removed.
        required: true
        default: null
        aliases: ['vol_id', 'id']

'''

EXAMPLES = '''
#
# Provisioning new disk
#

# Basic provisioning example create a disk
- name: create disk
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-beijing
    alicloud_zone: cn-beijing-b
    size: 20
    status: present
  tasks:
    - name: create disk
      ecs_disk:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        alicloud_zone: '{{ alicloud_zone }}'
        size: '{{ size }}'
        status: '{{ status }}'
      register: result
    - debug: var=result

# Advanced example with tagging and snapshot
- name: create disk
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    alicloud_zone: cn-hongkong-b
    disk_name: disk_1
    description: data disk_1
    size: 20
    snapshot_id: xxxxxxxxxx
    disk_category: cloud_ssd
    status: present
  tasks:
    - name: create disk
      ecs_disk:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        alicloud_zone: '{{ alicloud_zone }}'
        disk_name: '{{ disk_name }}'
        description: '{{ description }}'
        size: '{{ size }}'
        snapshot_id: '{{ snapshot_id }}'
        disk_category: '{{ disk_category }}'
        status: '{{ status }}'
      register: result
    - debug: var=result


# Example to attach disk to an instance
- name: attach disk to instance
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    status: present
    alicloud_region: us-west-1
    instance_id: xxxxxxxxxx
    disk_id: xxxxxxxxxx
    device: /dev/xvdb
    delete_with_instance: false
  tasks:
    - name: Attach Disk to instance
      ecs_disk:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        status: '{{ status }}'
        alicloud_region: '{{ alicloud_region }}'
        instance_id: '{{ instance_id }}'
        disk_id: '{{ disk_id }}'
        device: '{{ device }}'
        delete_with_instance: '{{ delete_with_instance }}'
      register: result
    - debug: var=result


# Example to detach disk from instance
- name: detach disk
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: us-west-1
    disk_id: xxxxxxxxxx
    status: present
  tasks:
    - name: detach disk
      ecs_disk:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        id: '{{ disk_id }}'
        status: '{{ status }}'
      register: result
    - debug: var=result


# Example to delete disk
- name: detach disk
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: us-west-1
    disk_id: xxxxxxxxxx
    status: absent
  tasks:
    - name: detach disk
      ecs_disk:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        disk_id: '{{ disk_id }}'
        status: '{{ status }}'
      register: result
    - debug: var=result
'''

HAS_ECS = False
HAS_FOOTMARK = False

try:
    from footmark.exception import ECSResponseError 
    HAS_FOOTMARK = True    
except ImportError:
    HAS_FOOTMARK = False

def create_disk(module, ecs, zone_id, disk_name, description, 
                disk_category, size, disk_tags, snapshot_id):
    """
    create an disk in ecs
    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param zone_id: ID of a zone to which an disk belongs.
    :param disk_name: Display name of the disk, which is a string
        of 2 to 128 Chinese or English characters. It must begin with an
        uppercase/lowercase letter or a Chinese character and can contain
        numerals, ".", "_", or "-".
    :param description: Description of the disk, which is a string of
        2 to 256 characters.
    :param disk_category: Displays category of the data disk
    :param size: Size of the system disk, in GB, values range
    :param disk_tags: A list of hash/dictionaries of instance
        tags, '[{tag_key:"value", tag_value:"value"}]', tag_key
        must be not null when tag_value isn't null   
    :param snapshot_id: Snapshots are used to create the data disk
        After this parameter is specified, Size is ignored.
    :return: Returns a dictionary of disk information
    """

    changed = False
    if not zone_id:
        module.fail_json(msg='zone_id is required for new disk')

    try:
        changed, disk_id, result = ecs.create_disk(zone_id=zone_id, disk_name=disk_name,
                                                   description=description, disk_category=disk_category, size=size,
                                                   disk_tags=disk_tags, snapshot_id=snapshot_id)
       
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, disk_id=disk_id, msg=result)
        changed = True

    except ECSResponseError as e:
        module.fail_json(msg='Unable to create disk, error: {0}'.format(e))
    
    return changed, disk_id, result


def attach_disk(module, ecs, disk_id, instance_id, device, delete_with_instance):
    """
    Method call to attach disk

    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param disk_id:  ID of Disk to Detach
    :param instance_id:  ID of an instance for disk to be attached
    :param region_id: ID of Region
    :param device: device for attaching
    :param delete_with_instance: should the disk be deleted with instance
    :return: return status of operation
    """
    changed = False
    if not instance_id:
        module.fail_json(msg='instance_id is required to attach disk')
        
    if not disk_id:
        module.fail_json(msg='disk id is required to attach disk')

    if delete_with_instance:
        if delete_with_instance.strip().lower() == "true":
            delete_with_instance = delete_with_instance.strip().lower()
        elif delete_with_instance.strip().lower() == "false":
            delete_with_instance = delete_with_instance.strip().lower()
        elif delete_with_instance.strip().lower() == "yes":
            delete_with_instance = "true"
        elif delete_with_instance.strip().lower() == "no":
            delete_with_instance = "false"
        else:
            delete_with_instance = None
            
    if delete_with_instance:
        delete_with_instance = delete_with_instance.strip().lower()

    if device:
        device = str(device).lower().strip()
        if len(device) == 9:
            first = device[0:8]
            last = device[8:9]
    
            if first != '/dev/xvd':
                module.fail_json(msg='device should be in proper format', operation='attach_disk')
            if "bcdefghijklmnopqrstuvwxyz".find(last) == -1:
                module.fail_json(msg='device should be in proper format, /dev/xvdb .. /dev/xvdz',
                                 operation='attach_disk')
        else:
            module.fail_json(msg='device should be in proper format, /dev/xvdb .. /dev/xvdz', operation='attach_disk')

    try:
        changed, result = ecs.attach_disk(disk_id=disk_id, instance_id=instance_id, device=device,
                                          delete_with_instance=delete_with_instance)

        if 'error code' in str(result).lower():
            module.fail_json(msg=result)
    except ECSResponseError as e:
        module.fail_json(msg='Unable to attach disk, error: {0}'.format(e), disk_id=disk_id, instance_id=instance_id)
    return changed, result, disk_id, instance_id


def detach_disk(module, ecs, disk_id):    
    """
    Method call to detach disk

    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param disk_id:  ID of Disk to Detach
    :return: return status of operation
    """
    changed = False            
    if not disk_id:
        module.fail_json(msg='disk id is required to detach disk')

    try:
        changed, result, instance_id = ecs.detach_disk(disk_id=disk_id)
        if 'error code' in (''.join(str(result))).lower():
            module.fail_json(msg=result, instance_id=instance_id, disk_id=disk_id)

    except ECSResponseError as e:
        module.fail_json(msg='Unable to detach disk, error: {0}'.format(e), instance_id=instance_id, disk_id=disk_id)

    return changed, result, instance_id


def delete_disk(module, ecs, disk_id):
    """
    Method to delete a disk

    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param disk_id:  ID of Disk to be Deleted
    :return: return status of operation
    """
    changed = False
    if not disk_id:
        module.fail_json(msg='disk id is required to delete disk')
    try:
        changed, result = ecs.delete_disk(disk_id=disk_id)
        if 'error code' in (''.join(str(result))).lower():
            module.fail_json(msg=result)

    except ECSResponseError as e:
        module.fail_json(msg='Unable to delete disk, error: {0}'.format(e))
                 
    return (changed, result)


def main():  
    if HAS_FOOTMARK is False:
        print("footmark required for this module")
        sys.exit(1)  
    else:    
        argument_spec = ecs_argument_spec()
        argument_spec.update(dict(
            group_id=dict(),
            alicloud_zone=dict(aliases=['zone_id', 'acs_zone', 'ecs_zone', 'zone', 'availability_zone']),         
            status=dict(default='present', aliases=['state'], choices=['present','absent'] ),
            disk_id=dict(aliases=['vol_id','id']),
            disk_name=dict(aliases=['name']),
            disk_category=dict(aliases=['disk_type','volume_type']), 
            size=dict(aliases=['disk_size','volume_size']), 
            disk_tags=dict(type='list', aliases=['tags']),
            snapshot_id=dict(aliases=['snapshot']),
            device=dict(aliases=['device_name']),        
            description=dict(aliases=['disk_description']),  
            instance_id=dict(aliases=['instance']),
            delete_with_instance = dict(aliases=['delete_on_termination'])
        )
        )	
        module = AnsibleModule(argument_spec=argument_spec)       
        ecs = ecs_connect(module)                                 
        region, acs_connect_kwargs = get_acs_connection_info(module)
        status = module.params['status']
  
        instance_id = module.params['instance_id']
        disk_id = module.params['disk_id']

        if status == 'present':

            len_instance = 0
            len_disk = 0
            operation_flag = ''

            if instance_id:
                len_instance = len(instance_id.strip())

            if disk_id:
                len_disk = len(disk_id.strip())

            if not instance_id:
                if disk_id is None or len_disk == 0:
                    operation_flag = 'present'
                elif disk_id is not None or len_disk > 0:
                    operation_flag = 'detach'
            elif instance_id is not None or len_instance > 0:
                if disk_id is not None or len_disk > 0:
                    operation_flag = 'attach'

            if operation_flag == '':
                module.fail_json(msg='To attach disk: instance_id and disk_id both parameters are required.'
                                     ' To detach disk: only disk_id is to be sent.'
                                     ' To create disk: disk_id and instance_id both are not to be sent.',
                                 instance_id=instance_id, disk_id=disk_id)

            if operation_flag == 'present':
                # create disk parameter values
                zone_id = module.params['alicloud_zone']
                disk_name = module.params['disk_name']
                description = module.params['description']
                disk_category = module.params['disk_category']
                size = module.params['size']
                disk_tags = module.params['disk_tags']            
                snapshot_id = module.params['snapshot_id']
                # create disk parameter values end

                # performing operation create disk
            
                new_instance_ids = []
                changed, disk_id, instance_dict_array = create_disk(module=module, ecs=ecs, zone_id=zone_id,
                                                                    disk_name=disk_name, description=description,
                                                                    disk_category=disk_category, size=size,
                                                                    disk_tags=disk_tags, snapshot_id=snapshot_id)
                module.exit_json(changed=changed,disk_id=disk_id, result=instance_dict_array)
        
            elif operation_flag == 'attach':
            
                delete_with_instance = module.params['delete_with_instance']
                device = module.params['device']

                # performing operation attach disk to instance

                instance_dict_array = []
                new_instance_ids = []
            
                (changed, result, disk_id, instance_id) = attach_disk(module, ecs, disk_id, instance_id, device,
                                                                      delete_with_instance)
                module.exit_json(changed=changed, result=result, disk_id=disk_id, instance_id=instance_id,
                                 operation='attach_disk')
               
            elif operation_flag == 'detach':
                # performing operation detach disk from instance
                # instance_id is to be retreived in call

                (changed, result, instance_id) = detach_disk(module=module, ecs=ecs, disk_id=disk_id)
                module.exit_json(changed=changed, result=result, instance_id=instance_id, disk_id=disk_id)

        elif status == 'absent':
            # performing operation delete disk

            (changed, result) = delete_disk(module=module, ecs=ecs, disk_id=disk_id)
            module.exit_json(changed=changed, result=result, disk_id=disk_id)



# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.alicloud_ecs import *

# import ECSConnection
main()
