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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: ec2_ami
version_added: "1.3"
short_description: create or destroy an image in ec2
description:
     - Regsiters or deregisters ec2 images.
options:
  instance_id:
    description:
      - Instance ID to create the AMI from.
    required: false
    default: null
  name:
    description:
      - The name of the new AMI.
    required: false
    default: null
  architecture:
    version_added: "2.3"
    description:
      - The target architecture of the image to register
    required: false
    default: null
  kernel_id:
    version_added: "2.3"
    description:
      - The target kernel id of the image to register
    required: false
    default: null
  virtualization_type:
    version_added: "2.3"
    description:
      - The virtualization type of the image to register
    required: false
    default: null
  root_device_name:
    version_added: "2.3"
    description:
      - The root device name of the image to register
    required: false
    default: null
  wait:
    description:
      - Wait for the AMI to be in state 'available' before returning.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    default: 300
  state:
    description:
      - Create or deregister AMI.
    required: false
    default: 'present'
    choices: [ "absent", "present" ]
  description:
    description:
      - Human-readable string describing the contents and purpose of the AMI.
    required: false
    default: null
  no_reboot:
    description:
      - Flag indicating that the bundling process should not attempt to shutdown the instance before bundling. If this flag is True, the
        responsibility of maintaining file system integrity is left to the owner of the instance.
    required: false
    default: no
    choices: [ "yes", "no" ]
  image_id:
    description:
      - Image ID to be deregistered.
    required: false
    default: null
  device_mapping:
    version_added: "2.0"
    description:
      - List of device hashes/dictionaries with custom configurations (same block-device-mapping parameters)
      - >
        Valid properties include: device_name, volume_type, size (in GB), delete_on_termination (boolean), no_device (boolean),
        snapshot_id, iops (for io1 volume_type)
    required: false
    default: null
  delete_snapshot:
    description:
      - Delete snapshots when deregistering the AMI.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  tags:
    description:
      - A dictionary of tags to add to the new image; '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: false
    default: null
    version_added: "2.0"
  launch_permissions:
    description:
      - Users and groups that should be able to launch the AMI. Expects
        dictionary with a key of user_ids and/or group_names. user_ids should
        be a list of account ids. group_name should be a list of groups, "all"
        is the only acceptable value currently.
    required: false
    default: null
    version_added: "2.0"
author:
    - "Evan Duffield (@scicoin-project) <eduffield@iacquire.com>"
    - "Constantin Bugneac (@Constantin07) <constantin.bugneac@endava.com>"
    - "Ross Williams (@gunzy83) <gunzy83au@gmail.com>"
    - "Willem van Ketwich (@wilvk) <willvk@gmail.com>"
extends_documentation_fragment:
    - aws
    - ec2
'''

# Thank you to iAcquire for sponsoring development of this module.

EXAMPLES = '''
# Basic AMI Creation
- ec2_ami:
    instance_id: i-xxxxxx
    wait: yes
    name: newtest
    tags:
      Name: newtest
      Service: TestService
  register: image

# Basic AMI Creation, without waiting
- ec2_ami:
    region: xxxxxx
    instance_id: i-xxxxxx
    wait: no
    name: newtest
  register: image

# AMI Registration from EBS Snapshot
- ec2_ami:
    region: xxxxxx
    name: newtest
    state: present
    architecture: x86_64
    virtualization_type: hvm
    root_device_name: /dev/xvda
    device_mapping:
      - device_name: /dev/xvda
        size: 8
        snapshot_id: snap-xxxxxxxx
        delete_on_termination: true
        volume_type: gp2
  register: image

# AMI Creation, with a custom root-device size and another EBS attached
- ec2_ami:
    instance_id: i-xxxxxx
    name: newtest
    device_mapping:
        - device_name: /dev/sda1
          size: XXX
          delete_on_termination: true
          volume_type: gp2
        - device_name: /dev/sdb
          size: YYY
          delete_on_termination: false
          volume_type: gp2
  register: image

# AMI Creation, excluding a volume attached at /dev/sdb
- ec2_ami:
    instance_id: i-xxxxxx
    name: newtest
    device_mapping:
        - device_name: /dev/sda1
          size: XXX
          delete_on_termination: true
          volume_type: gp2
        - device_name: /dev/sdb
          no_device: yes
  register: image

# Deregister/Delete AMI (keep associated snapshots)
- ec2_ami:
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    delete_snapshot: False
    state: absent

# Deregister AMI (delete associated snapshots too)
- ec2_ami:
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    delete_snapshot: True
    state: absent

# Update AMI Launch Permissions, making it public
- ec2_ami:
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    state: present
    launch_permissions:
      group_names: ['all']

# Allow AMI to be launched by another account
- ec2_ami:
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    state: present
    launch_permissions:
      user_ids: ['123456789012']
'''

RETURN = '''
architecture:
    description: architecture of image
    returned: when AMI is created or already exists
    type: string
    sample: "x86_64"
block_device_mapping:
    description: block device mapping associated with image
    returned: when AMI is created or already exists
    type: dict
    sample: {
        "/dev/sda1": {
            "delete_on_termination": true,
            "encrypted": false,
            "size": 10,
            "snapshot_id": "snap-1a03b80e7",
            "volume_type": "standard"
        }
    }
creationDate:
    description: creation date of image
    returned: when AMI is created or already exists
    type: string
    sample: "2015-10-15T22:43:44.000Z"
description:
    description: description of image
    returned: when AMI is created or already exists
    type: string
    sample: "nat-server"
hypervisor:
    description: type of hypervisor
    returned: when AMI is created or already exists
    type: string
    sample: "xen"
image_id:
    description: id of the image
    returned: when AMI is created or already exists
    type: string
    sample: "ami-1234abcd"
is_public:
    description: whether image is public
    returned: when AMI is created or already exists
    type: bool
    sample: false
location:
    description: location of image
    returned: when AMI is created or already exists
    type: string
    sample: "315210894379/nat-server"
name:
    description: ami name of image
    returned: when AMI is created or already exists
    type: string
    sample: "nat-server"
ownerId:
    description: owner of image
    returned: when AMI is created or already exists
    type: string
    sample: "435210894375"
platform:
    description: platform of image
    returned: when AMI is created or already exists
    type: string
    sample: null
root_device_name:
    description: root device name of image
    returned: when AMI is created or already exists
    type: string
    sample: "/dev/sda1"
root_device_type:
    description: root device type of image
    returned: when AMI is created or already exists
    type: string
    sample: "ebs"
state:
    description: state of image
    returned: when AMI is created or already exists
    type: string
    sample: "available"
tags:
    description: a dictionary of tags assigned to image
    returned: when AMI is created or already exists
    type: dict
    sample: {
        "Env": "devel",
        "Name": "nat-server"
    }
virtualization_type:
    description: image virtualization type
    returned: when AMI is created or already exists
    type: string
    sample: "hvm"
snapshots_deleted:
    description: a list of snapshot ids deleted after deregistering image
    returned: after AMI is deregistered, if 'delete_snapshot' is set to 'yes'
    type: list
    sample: [
        "snap-fbcccb8f",
        "snap-cfe7cdb4"
    ]
'''

import sys
import time
import traceback
from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec, ec2_connect, boto3_conn, camel_dict_to_snake_dict, HAS_BOTO3
from ansible.module_utils.basic import AnsibleModule

try:
    import botocore
except ImportError:
    pass


def create_image(module, connection):
    instance_id = module.params.get('instance_id')
    name = module.params.get('name')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    description = module.params.get('description')
    architecture = module.params.get('architecture')
    kernel_id = module.params.get('kernel_id')
    root_device_name = module.params.get('root_device_name')
    virtualization_type = module.params.get('virtualization_type')
    no_reboot = module.params.get('no_reboot')
    device_mapping = module.params.get('device_mapping')
    tags = module.params.get('tags')
    launch_permissions = module.params.get('launch_permissions')
    image_location = module.params.get('image_location')
    ena_support = module.params.get('ena_support')
    billing_products = module.params.get('billing_products')
    ramdisk_id = module.params.get('ramdisk_id')
    sriov_net_support = module.params.get('sriov_net_support')

    try:
        params = {
            'Name': name,
            'Description': description
        }

        images = connection.describe_images(
            Filters=[
                {
                    'Name': 'name',
                    'Values': [name]
                }
            ]
        ).get('Images')

        # ensure that launch_permissions are up to date
        if images and images[0]:
            update_image(module, connection, images[0].get('ImageId'))

        block_device_mapping = None

        if device_mapping:
            block_device_mapping = []
            for device in device_mapping:
                device['Ebs'] = {}
                if 'device_name' not in device:
                    module.fail_json(msg="Error - Device name must be set for volume.")
                device = rename_item_if_exists(device, 'device_name', 'DeviceName')
                device = rename_item_if_exists(device, 'virtual_name', 'VirtualName')
                device = rename_item_if_exists(device, 'no_device', 'NoDevice')
                device = rename_item_if_exists(device, 'volume_type', 'VolumeType', 'Ebs')
                device = rename_item_if_exists(device, 'snapshot_id', 'SnapshotId', 'Ebs')
                device = rename_item_if_exists(device, 'snapshot_id', 'SnapshotId', 'Ebs')
                device = rename_item_if_exists(device, 'delete_on_termination', 'DeleteOnTermination', 'Ebs')
                device = rename_item_if_exists(device, 'size', 'VolumeSize', 'Ebs')
                device = rename_item_if_exists(device, 'volume_size', 'VolumeSize', 'Ebs')
                device = rename_item_if_exists(device, 'iops', 'Iops', 'Ebs')
                device = rename_item_if_exists(device, 'encrypted', 'Encrypted', 'Ebs')
                block_device_mapping.append(device)
        if instance_id:
            params['InstanceId'] = instance_id
            params['NoReboot'] = no_reboot
            if block_device_mapping:
                params['BlockDeviceMappings'] = block_device_mapping
            image_id = connection.create_image(**params).get('ImageId')
        else:
            if architecture:
                params['Architecture'] = architecture
            if virtualization_type:
                params['VirtualizationType'] = virtualization_type
            if image_location:
                params['ImageLocation'] = image_location
            if ena_support:
                params['EnaSupport'] = ena_support
            if billing_products:
                params['BillingProducts'] = billing_products
            if ramdisk_id:
                params['RamdiskId'] = ramdisk_id
            if sriov_net_support:
                params['SriovNetSupport'] = sriov_net_support
            if kernel_id:
                params['KernelId'] = kernel_id
            if root_device_name:
                params['RootDeviceName'] = root_device_name
            if block_device_mapping:
                params['BlockDeviceMappings'] = block_device_mapping
            image_id = connection.register_image(**params).get('ImageId')
    except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Error registering image - " + str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    # Wait until the image is recognized. EC2 API has eventual consistency such that a successful CreateImage API call doesn't guarantee the success
    # of subsequent DescribeImages API call using the new image id returned.
    image_create_error_message = "Error while trying to find the new image. Using wait=yes and/or a longer wait_timeout may help."

    for i in range(wait_timeout):
        try:
            image = get_image_by_id(module, connection, image_id)
            if image.get('State') == 'available':
                break
            elif image.get('State') == 'failed':
                module.fail_json(msg="AMI creation failed, please see the AWS console for more details.")
        except botocore.exceptions.ClientError as e:
            if ('InvalidAMIID.NotFound' not in e.error_code and 'InvalidAMIID.Unavailable' not in e.error_code) and wait and i == wait_timeout - 1:
                module.fail_json(msg="%s %s: %s" % (image_create_error_message, e.error_code, e.error_message))
        finally:
            time.sleep(1)

    if tags:
        try:
            connection.create_tags(Resources=[image_id], Tags=convert_dict_to_tag_list(tags))
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Error tagging image - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if launch_permissions:
        try:
            image = get_image_by_id(module, connection, image_id)
            image.set_launch_permissions(**launch_permissions)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Error setting launch permissions for image: " + image_id + " - " + str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    module.exit_json(msg="AMI creation operation complete.", changed=True, **camel_dict_to_snake_dict(image))


def deregister_image(module, connection):
    image_id = module.params.get('image_id')
    delete_snapshot = module.params.get('delete_snapshot')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    image = get_image_by_id(module, connection, image_id)

    if image is None:
        module.fail_json(msg="Image %s does not exist." % image_id, changed=False)

    # Get all associated snapshot ids before deregistering image otherwise this information becomes unavailable.
    snapshots = []
    if 'BlockDeviceMappings' in image:
        for mapping in image.get('BlockDeviceMappings'):
            snapshots.append(mapping.get('SnapshotId'))

    # When trying to re-deregister an already deregistered image it doesn't raise an exception, it just returns an object without image attributes.
    if 'ImageId' in image:
        try:
            params = {'ImageId': image_id}
            res = connection.deregister_image(**params)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Error deregistering image - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    else:
        module.exit_json(msg="Image %s has already been deregistered." % image_id, changed=False)

    image = get_image_by_id(module, connection, image_id)
    wait_timeout = time.time() + wait_timeout

    while wait and wait_timeout > time.time() and image is not None:
        image = get_image_by_id(module, connection, image_id)
        time.sleep(3)

    if wait and wait_timeout <= time.time():
        module.fail_json(msg="Timed out waiting for image to be deregistered.")

    # Boto library has hardcoded the deletion of the snapshot for the root volume mounted as '/dev/sda1' only.
    # Make it possible to deregister all snapshots which belong to image, including root block device mapped as '/dev/xvda'
    deregister_complete_message = "AMI deregister operation complete."

    if delete_snapshot:
        try:
            for snapshot_id in snapshots:
                connection.delete_snapshot(snapshot_id)
        except botocore.exceptions.ClientError as e:
            # Don't error out if root volume snapshot was already deregistered as part of deregister_image
            if e.error_code == 'InvalidSnapshot.NotFound':
                pass
        module.exit_json(msg=deregister_complete_message, changed=True, snapshots_deleted=snapshots)
    else:
        module.exit_json(msg=deregister_complete_message, changed=True)


def update_image(module, connection, image_id):
    launch_permissions = module.params.get('launch_permissions') or []

    if 'user_ids' in launch_permissions:
        launch_permissions['user_ids'] = [str(user_id) for user_id in launch_permissions['user_ids']]

    image = get_image_by_id(module, connection, image_id)

    if image is None:
        module.fail_json(msg="Image %s does not exist" % image_id, changed=False)

    try:
        set_permissions = connection.describe_image_attribute(Attribute='launchPermission', ImageId=image_id).get('LaunchPermissions')
        if set_permissions != launch_permissions:
            if (('user_ids' in launch_permissions and launch_permissions['user_ids']) or
                    ('group_names' in launch_permissions and launch_permissions['group_names'])):
                res = image.set_launch_permissions(**launch_permissions)
            elif set_permissions and set_permissions[0].get('UserId') is not None and set_permissions[0].get('Group') is not None:
                res = image.remove_launch_permissions(**set_permissions)
            else:
                module.exit_json(msg="AMI not updated", launch_permissions=set_permissions, changed=False)
            module.exit_json(msg="AMI launch permissions updated", launch_permissions=launch_permissions, set_perms=set_permissions, changed=True)
        else:
            module.exit_json(msg="AMI not updated", launch_permissions=set_permissions, changed=False)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Error updating image - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def get_image_by_id(module, connection, image_id):
    try:
        images_response = connection.describe_images(ImageIds=[image_id])
        images = images_response.get('Images')
        no_images = len(images)
        if no_images == 0:
            return None
        if no_images == 1:
            return images[0]
        module.fail_json(msg="Invalid number of instances (%s) found for image_id: %s" % (str(len(images)), image_id))
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Error retreiving image by image_id - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def convert_dict_to_tag_list(dict_object):
    dict_list = []
    for key, value in dict_object.iteritems():
        tag_item = {'Key': key, 'Value': value}
        dict_list.append(tag_item)
    return dict_list


def rename_item_if_exists(dict_object, attribute, new_attribute, child_node=None):
    new_item = dict_object.get(attribute)
    if new_item is not None:
        if child_node is None:
            dict_object[new_attribute] = dict_object.get(attribute)
        else:
            dict_object[child_node][new_attribute] = dict_object.get(attribute)
        dict_object.pop(attribute)
    return dict_object


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        instance_id=dict(),
        image_id=dict(),
        architecture=dict(default='x86_64'),
        kernel_id=dict(),
        virtualization_type=dict(default='hvm'),
        root_device_name=dict(),
        delete_snapshot=dict(default=False, type='bool'),
        name=dict(),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(default=900, type='int'),
        description=dict(default=''),
        no_reboot=dict(default=False, type='bool'),
        state=dict(default='present'),
        device_mapping=dict(type='list'),
        tags=dict(type='dict'),
        launch_permissions=dict(type='dict'),
        image_location=dict(),
        ena_support=dict(type='bool'),
        billing_products=dict(type='list'),
        ramdisk_id=dict(),
        sriov_net_support=dict()
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoRegionError:
        module.fail_json(msg=("Region must be specified as a parameter in AWS_DEFAULT_REGION environment variable or in boto configuration file."))
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to establish connection - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if module.params.get('state') == 'absent':
        if not module.params.get('image_id'):
            module.fail_json(msg="The parameter image_id is required to deregister an AMI.")
        deregister_image(module, connection)
    elif module.params.get('state') == 'present':
        if module.params.get('image_id') and module.params.get('launch_permissions'):
            update_image(module, connection, module.params.get('image_id'))
        if not module.params.get('instance_id') and not module.params.get('device_mapping'):
            module.fail_json(msg="The parameters instance_id or device_mapping (register from EBS snapshot) are required for a new image.")
        if not module.params.get('name'):
            module.fail_json(msg="The name parameter is required for a new image.")
        create_image(module, connection)


if __name__ == '__main__':
    main()
