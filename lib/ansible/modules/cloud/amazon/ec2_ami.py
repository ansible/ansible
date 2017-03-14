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
     - Creates or deletes ec2 images.
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
      - Create or deregister/delete AMI.
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
      - Flag indicating that the bundling process should not attempt to shutdown the instance before bundling. If this flag is True, the responsibility of maintaining file system integrity is left to the owner of the instance.
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
      - "Valid properties include: device_name, volume_type, size (in GB), delete_on_termination (boolean), no_device (boolean), snapshot_id, iops (for io1 volume_type)"
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
extends_documentation_fragment:
    - aws
    - ec2
'''

# Thank you to iAcquire for sponsoring development of this module.

EXAMPLES = '''
# Basic AMI Creation
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    instance_id: i-xxxxxx
    wait: yes
    name: newtest
    tags:
      Name: newtest
      Service: TestService
  register: image

# Basic AMI Creation, without waiting
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    instance_id: i-xxxxxx
    wait: no
    name: newtest
  register: image

# AMI Registration from EBS Snapshot
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
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
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
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
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
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
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    delete_snapshot: False
    state: absent

# Deregister AMI (delete associated snapshots too)
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    delete_snapshot: True
    state: absent

# Update AMI Launch Permissions, making it public
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    state: present
    launch_permissions:
      group_names: ['all']

# Allow AMI to be launched by another account
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
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
    type: a dictionary of block devices
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
    type: dictionary of tags
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

try:
    import boto
    import boto.ec2
    from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def get_block_device_mapping(image):
    """
    Retrieves block device mapping from AMI
    """

    bdm_dict = dict()

    if image is not None and hasattr(image, 'block_device_mapping'):
        bdm = getattr(image,'block_device_mapping')
        for device_name in bdm.keys():
            bdm_dict[device_name] = {
                'size': bdm[device_name].size,
                'snapshot_id': bdm[device_name].snapshot_id,
                'volume_type': bdm[device_name].volume_type,
                'encrypted': bdm[device_name].encrypted,
                'delete_on_termination': bdm[device_name].delete_on_termination
            }

    return bdm_dict


def get_ami_info(image):

    return dict(
        image_id=image.id,
        state=image.state,
        architecture=image.architecture,
        block_device_mapping=get_block_device_mapping(image),
        creationDate=image.creationDate,
        description=image.description,
        hypervisor=image.hypervisor,
        is_public=image.is_public,
        location=image.location,
        ownerId=image.ownerId,
        root_device_name=image.root_device_name,
        root_device_type=image.root_device_type,
        tags=image.tags,
        virtualization_type = image.virtualization_type
    )


def create_image(module, ec2):
    """
    Creates new AMI

    module : AnsibleModule object
    ec2: authenticated ec2 connection object
    """

    instance_id = module.params.get('instance_id')
    name = module.params.get('name')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    description = module.params.get('description')
    architecture = module.params.get('architecture')
    kernel_id = module.params.get('kernel_id')
    root_device_name = module.params.get('root_device_name')
    virtualization_type = module.params.get('virtualization_type')
    no_reboot = module.params.get('no_reboot')
    device_mapping = module.params.get('device_mapping')
    tags =  module.params.get('tags')
    launch_permissions = module.params.get('launch_permissions')

    try:
        params = {'name': name,
                  'description': description}

        images = ec2.get_all_images(filters={'name': name})

        if images and images[0]:
            # ensure that launch_permissions are up to date
            update_image(module, ec2, images[0].id)

        bdm = None
        if device_mapping:
            bdm = BlockDeviceMapping()
            for device in device_mapping:
                if 'device_name' not in device:
                    module.fail_json(msg = 'Device name must be set for volume')
                device_name = device['device_name']
                del device['device_name']
                bd = BlockDeviceType(**device)
                bdm[device_name] = bd

        if instance_id:
            params['instance_id'] = instance_id
            params['no_reboot'] = no_reboot
            if bdm:
                params['block_device_mapping'] = bdm
            image_id = ec2.create_image(**params)
        else:
            params['architecture'] = architecture
            params['virtualization_type'] = virtualization_type
            if kernel_id:
                params['kernel_id'] = kernel_id
            if root_device_name:
                params['root_device_name'] = root_device_name
            if bdm:
                params['block_device_map'] = bdm
            image_id = ec2.register_image(**params)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    # Wait until the image is recognized. EC2 API has eventual consistency,
    # such that a successful CreateImage API call doesn't guarantee the success
    # of subsequent DescribeImages API call using the new image id returned.
    for i in range(wait_timeout):
        try:
            img = ec2.get_image(image_id)

            if img.state == 'available':
                break
            elif img.state == 'failed':
                module.fail_json(msg="AMI creation failed, please see the AWS console for more details")
        except boto.exception.EC2ResponseError as e:
            if ('InvalidAMIID.NotFound' not in e.error_code and 'InvalidAMIID.Unavailable' not in e.error_code) and wait and i == wait_timeout - 1:
                module.fail_json(msg="Error while trying to find the new image. Using wait=yes and/or a longer wait_timeout may help. %s: %s" % (e.error_code, e.error_message))
        finally:
            time.sleep(1)

    if img.state != 'available':
        module.fail_json(msg="Error while trying to find the new image. Using wait=yes and/or a longer wait_timeout may help.")

    if tags:
        try:
            ec2.create_tags(image_id, tags)
        except boto.exception.EC2ResponseError as e:
            module.fail_json(msg = "Image tagging failed => %s: %s" % (e.error_code, e.error_message))
    if launch_permissions:
        try:
            img = ec2.get_image(image_id)
            img.set_launch_permissions(**launch_permissions)
        except boto.exception.BotoServerError as e:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message), image_id=image_id)

    module.exit_json(msg="AMI creation operation complete", changed=True, **get_ami_info(img))


def deregister_image(module, ec2):
    """
    Deregisters AMI
    """

    image_id = module.params.get('image_id')
    delete_snapshot = module.params.get('delete_snapshot')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    img = ec2.get_image(image_id)
    if img is None:
        module.fail_json(msg = "Image %s does not exist" % image_id, changed=False)

    # Get all associated snapshot ids before deregistering image otherwise this information becomes unavailable
    snapshots = []
    if hasattr(img, 'block_device_mapping'):
        for key in img.block_device_mapping:
            snapshots.append(img.block_device_mapping[key].snapshot_id)

    # When trying to re-delete already deleted image it doesn't raise an exception
    # It just returns an object without image attributes
    if hasattr(img, 'id'):
        try:
            params = {'image_id': image_id,
                      'delete_snapshot': delete_snapshot}
            res = ec2.deregister_image(**params)
        except boto.exception.BotoServerError as e:
            module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))
    else:
        module.exit_json(msg = "Image %s has already been deleted" % image_id, changed=False)

    # wait here until the image is gone
    img = ec2.get_image(image_id)
    wait_timeout = time.time() + wait_timeout
    while wait and wait_timeout > time.time() and img is not None:
        img = ec2.get_image(image_id)
        time.sleep(3)
    if wait and wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "timed out waiting for image to be deregistered/deleted")

    # Boto library has hardcoded the deletion of the snapshot for the root volume mounted as '/dev/sda1' only
    # Make it possible to delete all snapshots which belong to image, including root block device mapped as '/dev/xvda'
    if delete_snapshot:
        try:
            for snapshot_id in snapshots:
                ec2.delete_snapshot(snapshot_id)
        except boto.exception.BotoServerError as e:
            if e.error_code == 'InvalidSnapshot.NotFound':
                # Don't error out if root volume snapshot was already deleted as part of deregister_image
                pass
        module.exit_json(msg="AMI deregister/delete operation complete", changed=True, snapshots_deleted=snapshots)
    else:
        module.exit_json(msg="AMI deregister/delete operation complete", changed=True)


def update_image(module, ec2, image_id):
    """
    Updates AMI
    """

    launch_permissions = module.params.get('launch_permissions') or []
    if 'user_ids' in launch_permissions:
        launch_permissions['user_ids'] = [str(user_id) for user_id in launch_permissions['user_ids']]

    img = ec2.get_image(image_id)
    if img is None:
        module.fail_json(msg = "Image %s does not exist" % image_id, changed=False)

    try:
        set_permissions = img.get_launch_permissions()
        if set_permissions != launch_permissions:
            if ('user_ids' in launch_permissions and launch_permissions['user_ids']) or ('group_names' in launch_permissions and launch_permissions['group_names']):
                res = img.set_launch_permissions(**launch_permissions)
            elif ('user_ids' in set_permissions and set_permissions['user_ids']) or ('group_names' in set_permissions and set_permissions['group_names']):
                res = img.remove_launch_permissions(**set_permissions)
            else:
                module.exit_json(msg="AMI not updated", launch_permissions=set_permissions, changed=False)
            module.exit_json(msg="AMI launch permissions updated", launch_permissions=launch_permissions, set_perms=set_permissions, changed=True)
        else:
            module.exit_json(msg="AMI not updated", launch_permissions=set_permissions, changed=False)

    except boto.exception.BotoServerError as e:
        module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        instance_id = dict(),
        image_id = dict(),
        architecture = dict(default="x86_64"),
        kernel_id = dict(),
        virtualization_type = dict(default="hvm"),
        root_device_name = dict(),
        delete_snapshot = dict(default=False, type='bool'),
        name = dict(),
        wait = dict(type='bool', default=False),
        wait_timeout = dict(default=900),
        description = dict(default=""),
        no_reboot = dict(default=False, type='bool'),
        state = dict(default='present'),
        device_mapping = dict(type='list'),
        tags = dict(type='dict'),
        launch_permissions = dict(type='dict')
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    try:
        ec2 = ec2_connect(module)
    except Exception as e:
        module.fail_json(msg="Error while connecting to aws: %s" % str(e))

    if module.params.get('state') == 'absent':
        if not module.params.get('image_id'):
            module.fail_json(msg='image_id needs to be an ami image to registered/delete')

        deregister_image(module, ec2)

    elif module.params.get('state') == 'present':
        if module.params.get('image_id') and module.params.get('launch_permissions'):
            # Update image's launch permissions
            update_image(module, ec2,module.params.get('image_id'))

        # Changed is always set to true when provisioning new AMI
        if not module.params.get('instance_id') and not module.params.get('device_mapping'):
            module.fail_json(msg='instance_id or device_mapping (register from ebs snapshot) parameter is required for new image')
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required for new image')
        create_image(module, ec2)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
