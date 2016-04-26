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

DOCUMENTATION = """
---
module: ec2_lc
short_description: Create or delete AWS Autoscaling Launch Configurations
description:
  - Can create or delete AWS Autoscaling Configurations
  - Works with the ec2_asg module to manage Autoscaling Groups
notes:
  - "Amazon ASG Autoscaling Launch Configurations are immutable once created, so modifying the configuration
    after it is changed will not modify the launch configuration on AWS. You must create a new config and assign
    it to the ASG instead."
version_added: "1.6"
author: "Gareth Rushgrove (@garethr)"
options:
  state:
    description:
      - register or deregister the instance
    required: true
    choices: ['present', 'absent']
  name:
    description:
      - Unique name for configuration
    required: true
  instance_type:
    description:
      - instance type to use for the instance
    required: true
    default: null
    aliases: []
  image_id:
    description:
      - The AMI unique identifier to be used for the group
    required: false
  key_name:
    description:
      - The SSH key name to be used for access to managed instances
    required: false
  security_groups:
    description:
      - A list of security groups into which instances should be found
    required: false
  volumes:
    description:
      - a list of volume dicts, each containing device name and optionally ephemeral id or snapshot id. Size and type (and number of iops for io device type) must be specified for a new volume or a root volume, and may be passed for a snapshot volume. For any volume, a volume size less than 1 will be interpreted as a request not to create the volume.
    required: false
  user_data:
    description:
      - opaque blob of data which is made available to the ec2 instance
    required: false
  kernel_id:
    description:
      - Kernel id for the EC2 instance
    required: false
  spot_price:
    description:
      - The spot price you are bidding. Only applies for an autoscaling group with spot instances.
    required: false
  instance_monitoring:
    description:
      - whether instances in group are launched with detailed monitoring.
    default: false
  assign_public_ip:
    description:
      - Used for Auto Scaling groups that launch instances into an Amazon Virtual Private Cloud. Specifies whether to assign a public IP address to each instance launched in a Amazon VPC.
    required: false
    version_added: "1.8"
  ramdisk_id:
    description:
      - A RAM disk id for the instances.
    required: false
    version_added: "1.8"
  instance_profile_name:
    description:
      - The name or the Amazon Resource Name (ARN) of the instance profile associated with the IAM role for the instances.
    required: false
    version_added: "1.8"
  ebs_optimized:
    description:
      - Specifies whether the instance is optimized for EBS I/O (true) or not (false).
    required: false
    default: false
    version_added: "1.8"
  classic_link_vpc_id:
    description:
      - Id of ClassicLink enabled VPC
    required: false
    version_added: "2.0"
  classic_link_vpc_security_groups:
    description:
      - A list of security group id's with which to associate the ClassicLink VPC instances.
    required: false
    version_added: "2.0"
extends_documentation_fragment:
    - aws
    - ec2
requires: 
    - "boto >= 2.39.0"
"""

EXAMPLES = '''
- ec2_lc:
    name: special
    image_id: ami-XXX
    key_name: default
    security_groups: ['group', 'group2' ]
    instance_type: t1.micro
    volumes:
    - device_name: /dev/sda1
      volume_size: 100
      device_type: io1
      iops: 3000
      delete_on_termination: true
    - device_name: /dev/sdb
      ephemeral: ephemeral0

'''

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

try:
    from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping
    import boto.ec2.autoscale
    from boto.ec2.autoscale import LaunchConfiguration
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def create_block_device(module, volume):
    # Not aware of a way to determine this programatically
    # http://aws.amazon.com/about-aws/whats-new/2013/10/09/ebs-provisioned-iops-maximum-iops-gb-ratio-increased-to-30-1/
    MAX_IOPS_TO_SIZE_RATIO = 30
    if 'snapshot' not in volume and 'ephemeral' not in volume:
        if 'volume_size' not in volume:
            module.fail_json(msg='Size must be specified when creating a new volume or modifying the root volume')
    if 'snapshot' in volume:
        if 'device_type' in volume and volume.get('device_type') == 'io1' and 'iops' not in volume:
            module.fail_json(msg='io1 volumes must have an iops value set')
    if 'ephemeral' in volume:
        if 'snapshot' in volume:
            module.fail_json(msg='Cannot set both ephemeral and snapshot')
    return BlockDeviceType(snapshot_id=volume.get('snapshot'),
                           ephemeral_name=volume.get('ephemeral'),
                           size=volume.get('volume_size'),
                           volume_type=volume.get('device_type'),
                           delete_on_termination=volume.get('delete_on_termination', False),
                           iops=volume.get('iops'))


def create_launch_config(connection, module):
    name = module.params.get('name')
    image_id = module.params.get('image_id')
    key_name = module.params.get('key_name')
    security_groups = module.params['security_groups']
    user_data = module.params.get('user_data')
    volumes = module.params['volumes']
    instance_type = module.params.get('instance_type')
    spot_price = module.params.get('spot_price')
    instance_monitoring = module.params.get('instance_monitoring')
    assign_public_ip = module.params.get('assign_public_ip')
    kernel_id = module.params.get('kernel_id')
    ramdisk_id = module.params.get('ramdisk_id')
    instance_profile_name = module.params.get('instance_profile_name')
    ebs_optimized = module.params.get('ebs_optimized')
    classic_link_vpc_id = module.params.get('classic_link_vpc_id')
    classic_link_vpc_security_groups = module.params.get('classic_link_vpc_security_groups')
    bdm = BlockDeviceMapping()

    if volumes:
        for volume in volumes:
            if 'device_name' not in volume:
                module.fail_json(msg='Device name must be set for volume')
            # Minimum volume size is 1GB. We'll use volume size explicitly set to 0
            # to be a signal not to create this volume
            if 'volume_size' not in volume or int(volume['volume_size']) > 0:
                bdm[volume['device_name']] = create_block_device(module, volume)

    lc = LaunchConfiguration(
        name=name,
        image_id=image_id,
        key_name=key_name,
        security_groups=security_groups,
        user_data=user_data,
        block_device_mappings=[bdm],
        instance_type=instance_type,
        kernel_id=kernel_id,
        spot_price=spot_price,
        instance_monitoring=instance_monitoring,
        associate_public_ip_address=assign_public_ip,
        ramdisk_id=ramdisk_id,
        instance_profile_name=instance_profile_name,
        ebs_optimized=ebs_optimized,
        classic_link_vpc_security_groups=classic_link_vpc_security_groups,
        classic_link_vpc_id=classic_link_vpc_id,
    )

    launch_configs = connection.get_all_launch_configurations(names=[name])
    changed = False
    if not launch_configs:
        try:
            connection.create_launch_configuration(lc)
            launch_configs = connection.get_all_launch_configurations(names=[name])
            changed = True
        except BotoServerError, e:
            module.fail_json(msg=str(e))

    result = dict(
                 ((a[0], a[1]) for a in vars(launch_configs[0]).items()
                  if a[0] not in ('connection', 'created_time', 'instance_monitoring', 'block_device_mappings'))
                 )
    result['created_time'] = str(launch_configs[0].created_time)
    # Looking at boto's launchconfig.py, it looks like this could be a boolean
    # value or an object with an enabled attribute.  The enabled attribute
    # could be a boolean or a string representation of a boolean.  Since
    # I can't test all permutations myself to see if my reading of the code is
    # correct, have to code this *very* defensively
    if launch_configs[0].instance_monitoring is True:
        result['instance_monitoring'] = True
    else:
        try:
            result['instance_monitoring'] = module.boolean(launch_configs[0].instance_monitoring.enabled)
        except AttributeError:
            result['instance_monitoring'] = False
    if launch_configs[0].block_device_mappings is not None:
        result['block_device_mappings'] = []
        for bdm in launch_configs[0].block_device_mappings:
            result['block_device_mappings'].append(dict(device_name=bdm.device_name, virtual_name=bdm.virtual_name))
            if bdm.ebs is not None:
                result['block_device_mappings'][-1]['ebs'] = dict(snapshot_id=bdm.ebs.snapshot_id, volume_size=bdm.ebs.volume_size)


    module.exit_json(changed=changed, name=result['name'], created_time=result['created_time'],
                     image_id=result['image_id'], arn=result['launch_configuration_arn'],
                     security_groups=result['security_groups'],
                     instance_type=result['instance_type'],
                     result=result)


def delete_launch_config(connection, module):
    name = module.params.get('name')
    launch_configs = connection.get_all_launch_configurations(names=[name])
    if launch_configs:
        launch_configs[0].delete()
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            image_id=dict(type='str'),
            key_name=dict(type='str'),
            security_groups=dict(type='list'),
            user_data=dict(type='str'),
            kernel_id=dict(type='str'),
            volumes=dict(type='list'),
            instance_type=dict(type='str'),
            state=dict(default='present', choices=['present', 'absent']),
            spot_price=dict(type='float'),
            ramdisk_id=dict(type='str'),
            instance_profile_name=dict(type='str'),
            ebs_optimized=dict(default=False, type='bool'),
            associate_public_ip_address=dict(type='bool'),
            instance_monitoring=dict(default=False, type='bool'),
            assign_public_ip=dict(type='bool'),
            classic_link_vpc_security_groups=dict(type='list'),
            classic_link_vpc_id=dict(type='str')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    try:
        connection = connect_to_aws(boto.ec2.autoscale, region, **aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, AnsibleAWSError), e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')

    if state == 'present':
        create_launch_config(connection, module)
    elif state == 'absent':
        delete_launch_config(connection, module)

main()
