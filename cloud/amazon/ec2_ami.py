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
      - instance id of the image to create
    required: false
    default: null
  name:
    description:
      - The name of the new image to create
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
    default: 300
  state:
    description:
      - create or deregister/delete image
    required: false
    default: 'present'
  description:
    description:
      - An optional human-readable string describing the contents and purpose of the AMI.
    required: false
    default: null
  no_reboot:
    description:
      - An optional flag indicating that the bundling process should not attempt to shutdown the instance before bundling. If this flag is True, the responsibility of maintaining file system integrity is left to the owner of the instance. The default choice is "no".
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
      - An optional list of device hashes/dictionaries with custom configurations (same block-device-mapping parameters)
      - "Valid properties include: device_name, volume_type, size (in GB), delete_on_termination (boolean), no_device (boolean), snapshot_id, iops (for io1 volume_type)"
    required: false
    default: null
  delete_snapshot:
    description:
      - Whether or not to delete an AMI while deregistering it.
    required: false
    default: null
  tags:
    description:
      - a hash/dictionary of tags to add to the new image; '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: false
    default: null
    version_added: "2.0"
  launch_permissions:
    description:
      - Users and groups that should be able to launch the ami. Expects dictionary with a key of user_ids and/or group_names. user_ids should be a list of account ids. group_name should be a list of groups, "all" is the only acceptable value currently.
    required: false
    default: null
    version_added: "2.0"
author: "Evan Duffield (@scicoin-project) <eduffield@iacquire.com>"
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
  register: instance

# Basic AMI Creation, without waiting
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    instance_id: i-xxxxxx
    wait: no
    name: newtest
  register: instance

# AMI Creation, with a custom root-device size and another EBS attached
- ec2_ami
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
  register: instance

# AMI Creation, excluding a volume attached at /dev/sdb
- ec2_ami
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
  register: instance

# Deregister/Delete AMI
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    delete_snapshot: True
    state: absent

# Deregister AMI
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    delete_snapshot: False
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

import sys
import time

try:
    import boto
    import boto.ec2
    from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


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
    no_reboot = module.params.get('no_reboot')
    device_mapping = module.params.get('device_mapping')
    tags =  module.params.get('tags')
    launch_permissions = module.params.get('launch_permissions')

    try:
        params = {'instance_id': instance_id,
                  'name': name,
                  'description': description,
                  'no_reboot': no_reboot}

        if device_mapping:
            bdm = BlockDeviceMapping()
            for device in device_mapping:
                if 'device_name' not in device:
                    module.fail_json(msg = 'Device name must be set for volume')
                device_name = device['device_name']
                del device['device_name']
                bd = BlockDeviceType(**device)
                bdm[device_name] = bd
            params['block_device_mapping'] = bdm

        image_id = ec2.create_image(**params)
    except boto.exception.BotoServerError, e:
        if e.error_code == 'InvalidAMIName.Duplicate':
            images = ec2.get_all_images()
            for img in images:
                if img.name == name:
                    module.exit_json(msg="AMI name already present", image_id=img.id, state=img.state, changed=False)
                    sys.exit(0)
            else:
                module.fail_json(msg="Error in retrieving duplicate AMI details")
        else:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    # Wait until the image is recognized. EC2 API has eventual consistency,
    # such that a successful CreateImage API call doesn't guarantee the success
    # of subsequent DescribeImages API call using the new image id returned.
    for i in range(wait_timeout):
        try:
            img = ec2.get_image(image_id)
            break
        except boto.exception.EC2ResponseError, e:
            if 'InvalidAMIID.NotFound' in e.error_code and wait:
                time.sleep(1)
            else:
                module.fail_json(msg="Error while trying to find the new image. Using wait=yes and/or a longer wait_timeout may help.")
    else:
        module.fail_json(msg="timed out waiting for image to be recognized")

    # wait here until the image is created
    wait_timeout = time.time() + wait_timeout
    while wait and wait_timeout > time.time() and (img is None or img.state != 'available'):
        img = ec2.get_image(image_id)
        time.sleep(3)
    if wait and wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "timed out waiting for image to be created")

    if tags:
        try:
            ec2.create_tags(image_id, tags)
        except boto.exception.EC2ResponseError, e:
            module.fail_json(msg = "Image tagging failed => %s: %s" % (e.error_code, e.error_message))
    if launch_permissions:
        try:
            img = ec2.get_image(image_id)
            img.set_launch_permissions(**launch_permissions)
        except boto.exception.BotoServerError, e:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message), image_id=image_id)

    module.exit_json(msg="AMI creation operation complete", image_id=image_id, state=img.state, changed=True)


def deregister_image(module, ec2):
    """
    Deregisters AMI
    """

    image_id = module.params.get('image_id')
    delete_snapshot = module.params.get('delete_snapshot')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    img = ec2.get_image(image_id)
    if img == None:
        module.fail_json(msg = "Image %s does not exist" % image_id, changed=False)

    try:
        params = {'image_id': image_id,
                  'delete_snapshot': delete_snapshot}

        res = ec2.deregister_image(**params)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

    # wait here until the image is gone
    img = ec2.get_image(image_id)
    wait_timeout = time.time() + wait_timeout
    while wait and wait_timeout > time.time() and img is not None:
        img = ec2.get_image(image_id)
        time.sleep(3)
    if wait and wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "timed out waiting for image to be reregistered/deleted")

    module.exit_json(msg="AMI deregister/delete operation complete", changed=True)
    sys.exit(0)


def update_image(module, ec2):
    """
    Updates AMI
    """

    image_id = module.params.get('image_id')
    launch_permissions = module.params.get('launch_permissions')
    if 'user_ids' in launch_permissions:
        launch_permissions['user_ids'] = [str(user_id) for user_id in launch_permissions['user_ids']]

    img = ec2.get_image(image_id)
    if img == None:
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

    except boto.exception.BotoServerError, e:
        module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            instance_id = dict(),
            image_id = dict(),
            delete_snapshot = dict(),
            name = dict(),
            wait = dict(type="bool", default=False),
            wait_timeout = dict(default=900),
            description = dict(default=""),
            no_reboot = dict(default=False, type="bool"),
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
    except Exception, e:
        module.json_fail(msg="Error while connecting to aws: %s" % str(e))

    if module.params.get('state') == 'absent':
        if not module.params.get('image_id'):
            module.fail_json(msg='image_id needs to be an ami image to registered/delete')

        deregister_image(module, ec2)

    elif module.params.get('state') == 'present':
        if module.params.get('image_id') and module.params.get('launch_permissions'):
            # Update image's launch permissions
            update_image(module, ec2)

        # Changed is always set to true when provisioning new AMI
        if not module.params.get('instance_id'):
            module.fail_json(msg='instance_id parameter is required for new image')
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required for new image')
        create_image(module, ec2)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
