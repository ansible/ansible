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
module: ecs_ami
version_added: "1.0"
short_description: Create or Delete User-defined Image
description:
    - Creates or deletes User-defined Images
options:
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
    description: create or deregister/delete image
    required: false
    choices: [ "present", "absent" ]
    default: 'present'
    aliases: [ 'state' ]

function: create image
  description: Creates or delete User-defined Images in ecs
  options:
    instance_id:
      description:
        - instance id of the image to create
      required: false
      default: null
      aliases: [ "instance" ]
    snapshot_id:
      description:
        - snapshot id of the image to create, image from system of instance
      required: true
      default: null
      aliases: [ "snapshot" ]
    image_name:
      description:
        - The name of the new image to create
      required: false
      default: null
      aliases: [ "name" ]
    description:
      description:
        - An optional human-readable string describing the contents and purpose of the AMI.
      required: false
      default: null
    image_version:
      description:
        - The version of the new image to create.
      required: false
      default: null
      aliases: [ "version" ]
    disk_mapping:
      description:
        - An optional list of device hashes/dictionaries with custom configurations (same block-device-mapping
          parameters)
        - keys allowed are
            - device (required=false;) - Disk Device Name value /dev/xvda start to /dev/xvdz, /dev/xvda default system 
              disk is a snapshot of /dev/xvdb-z is only a snapshot of the data disk
            - snapshot_id (required=false;) - Snapshot Id
            - disk_size (required=false;) - Size of the disk, in the range [5-2000GB]
      required: false
      default: null
    wait:
      description:
        - wait for the AMI to be in state 'available' before returning.
      required: false
      default: "no"
      choices: [ "yes", "no" ]
    wait_timeout:
      description:
        - how long before wait gives up, in seconds
      required: false
      default: 300
    images_tags:
      description:
        - a dictionary of tags to add to the new image; '{"key":"value"}' and '{"key":"value","key":"value"}'
      required: false
      default: null
      aliases: [ "tags" ]
    launch_permission:
      description:
        - Users that should be able to launch the ami. Expects dictionary with a key of user_ids. user_ids should be a
          list of account ids and the number no more than 10.
      required: false
      default: null

function: delete user-defined image
  description: delete user-defined image
  options:
    image_id:
      description:
        - Image ID to be deregistered.
      required: true
      default: null
'''

EXAMPLES = '''
#
# provisioning to create new user-defined image
#

# basic provisioning example to create image using ecs instance
- name: create image from ecs instance
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    instance_id: xxxxxxxxxx
  tasks:
    - name: create image form ecs instance
      ecs_ami:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        instance_id: '{{ instance_id }}'
      register: result
    - debug: var=result

# basic provisioning example to create image using snapshot
- name: create image using snapshot
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    snapshot_id: xxxxxxxxxx
    status: present
  tasks:
    - name: create image using snapshot
      ecs_ami:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        snapshot_id: '{{ snapshot_id }}'
        status: '{{ status }}'
      register: result
    - debug: var=result

# basic provisioning example to create image using disk mapping
- name: create image using disk mapping
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    disk_mapping:
      - device: /dev/xvda
        disk_size: 5
        snapshot_id: xxxxxxxxxx
    status: present
  tasks:
    - name: create image using disk mapping
      ecs_ami:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        disk_mapping: '{{ disk_mapping }}'
        status: '{{ status }}'
      register: result
    - debug: var=result

# advanced example to create image with tagging, version and launch permission
- name: create image
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    image_name: image_test
    image_version: 4
    description: description
    images_tags:
      - tag_key: key
        tag_value: value
    disk_mapping:
      - device: /dev/xvda
        disk_size: 5
        snapshot_id: xxxxxxxxxx
    status: present
    wait: false
    wait_timeout: 10
    launch_permission: xxxxxxxxxx
  tasks:
    - name: create image
      ecs_ami:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        image_name: '{{ image_name }}'
        image_version: '{{ image_version }}'
        description: '{{ description }}'
        images_tags: '{{ images_tags }}'
        disk_mapping: '{{ disk_mapping }}'
        status: '{{ status }}'
        wait: '{{ wait }}'
        wait_timeout: '{{ wait_timeout }}'
        launch_permission: '{{ launch_permission }}'
      register: result
    - debug: var=result

#
# provisioning to delete user-defined image
#

# provisioning to delete user-defined image
- name: delete image
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: us-west-1
    image_id: xxxxxxxxxx
    status: absent
  tasks:
    - name: delete image
      ecs_ami:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        image_id: '{{ image_id }}'
        status: '{{ status }}'
      register: result
    - debug: var=result
'''

HAS_FOOTMARK = False

try:
    from footmark.exception import ECSResponseError 
    HAS_FOOTMARK = True    
except ImportError:
    HAS_FOOTMARK = False

def create_image(module, ecs, snapshot_id, image_name, image_version, description, images_tags, instance_id,
                 disk_mapping, wait, wait_timeout, launch_permission):
    """
    Create a user-defined image with snapshots.

    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param snapshot_id: A user-defined image is created from the specified snapshot.
    :param image_name: image name which is to be created
    :param image_version: version of image
    :param description: description of the image
    :param images_tags: tags for the instance
    :param instance_id: the specified instance_id
    :param disk_mapping: list relating device and disk
    :param wait: Used to indicate wait for instance to be running before running
    :param wait_timeout: Used to indicate how long to wait, default 300
    :param launch_permission: Used to send list of userIds who are permitted to launch ami
    :return: id of image
    """
    changed = False
    if image_name:
        if len(image_name) < 2 or len(image_name) > 128:
            module.fail_json(msg='image_name must be 2 - 128 characters long')

        if image_name.startswith('http://') or image_name.startswith('https://'):
            module.fail_json(msg='image_name can not start with http:// or https://')
    if image_version:
        if image_version.isdigit():
            if int(image_version) < 1 or int(image_version) > 40:
                    module.fail_json(msg='The permitted range of image_version is between 1 - 40')
        else:
            module.fail_json(msg='The permitted range of image_version is between 1 - 40, entered value is {0}'
                                .format(image_version))    

    if disk_mapping:        
        for mapping in disk_mapping:
            if mapping:
                if 'snapshot_id' not in mapping:
                    module.fail_json(msg='The snapshot_id of system disk is needed for disk mapping.')

                if not('disk_size' in mapping or 'device' in mapping or 'snapshot_id' in mapping):
                    module.fail_json(msg='The disk_size, device and snapshot_id parameters '
                                         'are valid for disk mapping.')

                if 'disk_size' in mapping:
                    map_disk = mapping['disk_size']
                    if map_disk:
                        if str(map_disk).isdigit():
                            if int(map_disk) < 5 or int(map_disk) > 2000:
                                module.fail_json(msg='The permitted range of disk-size is 5 GB - 2000 GB ')
                        else:
                            module.fail_json(msg='The disk_size must be an integer value, entered value is {0}'.format(
                                map_disk))

    if images_tags:
        key = ''
        key_val = ''
        for tags in images_tags:
            if tags:
                if 'tag_key' in tags:
                    key = tags['tag_key']
                if 'tag_value' in tags:
                    key_val = tags['tag_value']
                if not key and key_val:
                    module.fail_json(msg='tag_key must be present when tag_value is present')          

    if not snapshot_id and not instance_id and not disk_mapping:
        module.fail_json(msg='Either of SnapshotId or InstanceId or disk_mapping, must be present for '
                             'create image operation to get performed')

    if (snapshot_id and instance_id) or (snapshot_id and disk_mapping) or (instance_id and disk_mapping):
        module.fail_json(msg='Only 1 of SnapshotId or InstanceId or disk_mapping, must be present for '
                             'create image operation to get performed')

    # call to create_image method in footmark
    try:
        changed, image_id, result, request_id = ecs.create_image(snapshot_id=snapshot_id, image_name=image_name,
                                                                 image_version=image_version, description=description,
                                                                 images_tags=images_tags,
                                                                 instance_id=instance_id, disk_mapping=disk_mapping,
                                                                 wait=wait, wait_timeout=wait_timeout,
                                                                 launch_permission=launch_permission)

        if 'error code' in str(result).lower():
            module.fail_json(msg=result, image_id=image_id, changed=changed, RequestId=request_id)

    except ECSResponseError as e:
        module.fail_json(msg='Unable to create image, error: {0}'.format(e))
    return changed, image_id, result, request_id


def delete_image(module, ecs, image_id):
    """
    Delete a user-defined image .

    :param module: Ansible module object
    :param ecs: authenticated ecs connection object
    :param image_id: Unique image id which is to be deleted
    :return: Result of an operation
    """
    changed = False
    if not image_id:
        module.fail_json(msg='image id is required to delete image')
    try:
        changed, result = ecs.delete_image(image_id=image_id)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(msg=result)

    except ECSResponseError as e:
        module.fail_json(msg='Unable to delete image, error: {0}'.format(e))

    return changed, result


def main():
    if HAS_FOOTMARK is False:
        print("Footmark required for this module")
        sys.exit(1)  
    else:
        argument_spec = ecs_argument_spec()
        argument_spec.update(dict(
            image_id=dict(),
            snapshot_id=dict(aliases=['snapshot']),
            description=dict(),
            image_name=dict(aliases=['name']),
            image_version=dict(aliases=['version']),
            disk_mapping=dict(type='list'),
            instance_id=dict(aliases=['instance']),
            status=dict(default='present', choices=['present', 'absent'], aliases=['state']),
            images_tags=dict(type='list', aliases=['tags']),
            launch_permission=dict(type='list'),
            wait=dict(default='no', choices=['yes', 'no', 'Yes', 'No', "true", "false", "True", "False"]),
            wait_timeout=dict(type='int', default='300')
        ))
        module = AnsibleModule(argument_spec=argument_spec)

        ecs = ecs_connect(module)
        status = module.params['status']

        if status == 'present':
            snapshot_id = module.params['snapshot_id']
            image_name = module.params['image_name']
            image_version = module.params['image_version']
            description = module.params['description']
            disk_mapping = module.params['disk_mapping']
            instance_id = module.params['instance_id']
            images_tags = module.params['images_tags']
            wait = module.params['wait']
            wait_timeout = module.params['wait_timeout']
            launch_permission = module.params['launch_permission']

            # Calling create_image method
            changed, image_id, result, request_id = create_image(module=module, ecs=ecs, snapshot_id=snapshot_id,
                                                                 image_name=image_name, image_version=image_version,
                                                                 description=description, images_tags=images_tags,
                                                                 instance_id=instance_id, disk_mapping=disk_mapping,
                                                                 wait=wait, wait_timeout=wait_timeout,
                                                                 launch_permission=launch_permission)

            module.exit_json(changed=changed, result=result, image_id=image_id, RequestId=request_id)

        elif status == 'absent':
            image_id = module.params['image_id']

            (changed, result) = delete_image(module=module, ecs=ecs, image_id=image_id)
            module.exit_json(changed=changed, result=result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.alicloud_ecs import *

# import ECSConnection
main()
