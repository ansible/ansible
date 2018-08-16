#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: ec2_vol
short_description: create and attach a volume, return volume id and device map
description:
    - creates an EBS volume and optionally attaches it to an instance.
      If both an instance ID and a device name is given and the instance has a device at the device name, then no volume is created and no attachment is made.
      This module has a dependency on python-boto.
version_added: "1.1"
options:
  instance:
    description:
      - instance ID if you wish to attach the volume. Since 1.9 you can set to None to detach.
  name:
    description:
      - volume Name tag if you wish to attach an existing volume (requires instance)
    version_added: "1.6"
  id:
    description:
      - volume id if you wish to attach an existing volume (requires instance) or remove an existing volume
    version_added: "1.6"
  volume_size:
    description:
      - size of volume (in GB) to create.
  volume_type:
    description:
      - Type of EBS volume; standard (magnetic), gp2 (SSD), io1 (Provisioned IOPS), st1 (Throughput Optimized HDD), sc1 (Cold HDD).
        "Standard" is the old EBS default and continues to remain the Ansible default for backwards compatibility.
    default: standard
    version_added: "1.9"
  iops:
    description:
      - the provisioned IOPs you want to associate with this volume (integer).
    default: 100
    version_added: "1.3"
  encrypted:
    description:
      - Enable encryption at rest for this volume.
    default: 'no'
    version_added: "1.8"
  kms_key_id:
    description:
      - Specify the id of the KMS key to use.
    version_added: "2.3"
  device_name:
    description:
      - device id to override device mapping. Assumes /dev/sdf for Linux/UNIX and /dev/xvdf for Windows.
  delete_on_termination:
    description:
      - When set to "yes", the volume will be deleted upon instance termination.
    type: bool
    default: 'no'
    version_added: "2.1"
  zone:
    description:
      - zone in which to create the volume, if unset uses the zone the instance is in (if set)
    aliases: ['aws_zone', 'ec2_zone']
  snapshot:
    description:
      - snapshot ID on which to base the volume
    version_added: "1.5"
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    type: bool
    default: 'yes'
    version_added: "1.5"
  state:
    description:
      - whether to ensure the volume is present or absent, or to list existing volumes (The C(list) option was added in version 1.8).
    default: present
    choices: ['absent', 'present', 'list']
    version_added: "1.6"
  tags:
    description:
      - tag:value pairs to add to the volume after creation
    default: {}
    version_added: "2.3"
author: "Lester Wade (@lwade)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Simple attachment action
- ec2_vol:
    instance: XXXXXX
    volume_size: 5
    device_name: sdd

# Example using custom iops params
- ec2_vol:
    instance: XXXXXX
    volume_size: 5
    iops: 100
    device_name: sdd

# Example using snapshot id
- ec2_vol:
    instance: XXXXXX
    snapshot: "{{ snapshot }}"

# Playbook example combined with instance launch
- ec2:
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    wait: yes
    count: 3
  register: ec2
- ec2_vol:
    instance: "{{ item.id }}"
    volume_size: 5
  with_items: "{{ ec2.instances }}"
  register: ec2_vol

# Example: Launch an instance and then add a volume if not already attached
#   * Volume will be created with the given name if not already created.
#   * Nothing will happen if the volume is already attached.
#   * Requires Ansible 2.0

- ec2:
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    zone: YYYYYY
    id: my_instance
    wait: yes
    count: 1
  register: ec2

- ec2_vol:
    instance: "{{ item.id }}"
    name: my_existing_volume_Name_tag
    device_name: /dev/xvdf
  with_items: "{{ ec2.instances }}"
  register: ec2_vol

# Remove a volume
- ec2_vol:
    id: vol-XXXXXXXX
    state: absent

# Detach a volume (since 1.9)
- ec2_vol:
    id: vol-XXXXXXXX
    instance: None

# List volumes for an instance
- ec2_vol:
    instance: i-XXXXXX
    state: list

# Create new volume using SSD storage
- ec2_vol:
    instance: XXXXXX
    volume_size: 50
    volume_type: gp2
    device_name: /dev/xvdf

# Attach an existing volume to instance. The volume will be deleted upon instance termination.
- ec2_vol:
    instance: XXXXXX
    id: XXXXXX
    device_name: /dev/sdf
    delete_on_termination: yes
'''

RETURN = '''
device:
    description: device name of attached volume
    returned: when success
    type: string
    sample: "/def/sdf"
volume_id:
    description: the id of volume
    returned: when success
    type: string
    sample: "vol-35b333d9"
volume_type:
    description: the volume type
    returned: when success
    type: string
    sample: "standard"
volume:
    description: a dictionary containing detailed attributes of the volume
    returned: when success
    type: string
    sample: {
        "attachment_set": {
            "attach_time": "2015-10-23T00:22:29.000Z",
            "deleteOnTermination": "false",
            "device": "/dev/sdf",
            "instance_id": "i-8356263c",
            "status": "attached"
        },
        "create_time": "2015-10-21T14:36:08.870Z",
        "encrypted": false,
        "id": "vol-35b333d9",
        "iops": null,
        "size": 1,
        "snapshot_id": "",
        "status": "in-use",
        "tags": {
            "env": "dev"
        },
        "type": "standard",
        "zone": "us-east-1b"
    }
'''

import time

from distutils.version import LooseVersion

try:
    import boto
    import boto.ec2
    import boto.exception
    from boto.exception import BotoServerError
    from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO, AnsibleAWSError, connect_to_aws, ec2_argument_spec,
                                      get_aws_connection_info)


def get_volume(module, ec2):
    name = module.params.get('name')
    id = module.params.get('id')
    zone = module.params.get('zone')
    filters = {}
    volume_ids = None

    # If no name or id supplied, just try volume creation based on module parameters
    if id is None and name is None:
        return None

    if zone:
        filters['availability_zone'] = zone
    if name:
        filters = {'tag:Name': name}
    if id:
        volume_ids = [id]
    try:
        vols = ec2.get_all_volumes(volume_ids=volume_ids, filters=filters)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    if not vols:
        if id:
            msg = "Could not find the volume with id: %s" % id
            if name:
                msg += (" and name: %s" % name)
            module.fail_json(msg=msg)
        else:
            return None

    if len(vols) > 1:
        module.fail_json(msg="Found more than one volume in zone (if specified) with name: %s" % name)
    return vols[0]


def get_volumes(module, ec2):

    instance = module.params.get('instance')

    try:
        if not instance:
            vols = ec2.get_all_volumes()
        else:
            vols = ec2.get_all_volumes(filters={'attachment.instance-id': instance})
    except boto.exception.BotoServerError as e:
        module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))
    return vols


def delete_volume(module, ec2):
    volume_id = module.params['id']
    try:
        ec2.delete_volume(volume_id)
        module.exit_json(changed=True)
    except boto.exception.EC2ResponseError as ec2_error:
        if ec2_error.code == 'InvalidVolume.NotFound':
            module.exit_json(changed=False)
        module.fail_json(msg=ec2_error.message)


def boto_supports_volume_encryption():
    """
    Check if Boto library supports encryption of EBS volumes (added in 2.29.0)

    Returns:
        True if boto library has the named param as an argument on the request_spot_instances method, else False
    """
    return hasattr(boto, 'Version') and LooseVersion(boto.Version) >= LooseVersion('2.29.0')


def boto_supports_kms_key_id():
    """
    Check if Boto library supports kms_key_ids (added in 2.39.0)

    Returns:
        True if version is equal to or higher then the version needed, else False
    """
    return hasattr(boto, 'Version') and LooseVersion(boto.Version) >= LooseVersion('2.39.0')


def create_volume(module, ec2, zone):
    changed = False
    name = module.params.get('name')
    iops = module.params.get('iops')
    encrypted = module.params.get('encrypted')
    kms_key_id = module.params.get('kms_key_id')
    volume_size = module.params.get('volume_size')
    volume_type = module.params.get('volume_type')
    snapshot = module.params.get('snapshot')
    tags = module.params.get('tags')
    # If custom iops is defined we use volume_type "io1" rather than the default of "standard"
    if iops:
        volume_type = 'io1'

    volume = get_volume(module, ec2)
    if volume is None:
        try:
            if boto_supports_volume_encryption():
                if kms_key_id is not None:
                    volume = ec2.create_volume(volume_size, zone, snapshot, volume_type, iops, encrypted, kms_key_id)
                else:
                    volume = ec2.create_volume(volume_size, zone, snapshot, volume_type, iops, encrypted)
                changed = True
            else:
                volume = ec2.create_volume(volume_size, zone, snapshot, volume_type, iops)
                changed = True

            while volume.status != 'available':
                time.sleep(3)
                volume.update()

            if name:
                tags["Name"] = name
            if tags:
                ec2.create_tags([volume.id], tags)
        except boto.exception.BotoServerError as e:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    return volume, changed


def attach_volume(module, ec2, volume, instance):

    device_name = module.params.get('device_name')
    delete_on_termination = module.params.get('delete_on_termination')
    changed = False

    # If device_name isn't set, make a choice based on best practices here:
    # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/block-device-mapping-concepts.html

    # In future this needs to be more dynamic but combining block device mapping best practices
    # (bounds for devices, as above) with instance.block_device_mapping data would be tricky. For me ;)

    # Use password data attribute to tell whether the instance is Windows or Linux
    if device_name is None:
        try:
            if not ec2.get_password_data(instance.id):
                device_name = '/dev/sdf'
            else:
                device_name = '/dev/xvdf'
        except boto.exception.BotoServerError as e:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    if volume.attachment_state() is not None:
        adata = volume.attach_data
        if adata.instance_id != instance.id:
            module.fail_json(msg="Volume %s is already attached to another instance: %s"
                             % (volume.id, adata.instance_id))
        else:
            # Volume is already attached to right instance
            changed = modify_dot_attribute(module, ec2, instance, device_name)
    else:
        try:
            volume.attach(instance.id, device_name)
            while volume.attachment_state() != 'attached':
                time.sleep(3)
                volume.update()
            changed = True
        except boto.exception.BotoServerError as e:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

        modify_dot_attribute(module, ec2, instance, device_name)

    return volume, changed


def modify_dot_attribute(module, ec2, instance, device_name):
    """ Modify delete_on_termination attribute """

    delete_on_termination = module.params.get('delete_on_termination')
    changed = False

    try:
        instance.update()
        dot = instance.block_device_mapping[device_name].delete_on_termination
    except boto.exception.BotoServerError as e:
        module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    if delete_on_termination != dot:
        try:
            bdt = BlockDeviceType(delete_on_termination=delete_on_termination)
            bdm = BlockDeviceMapping()
            bdm[device_name] = bdt

            ec2.modify_instance_attribute(instance_id=instance.id, attribute='blockDeviceMapping', value=bdm)

            while instance.block_device_mapping[device_name].delete_on_termination != delete_on_termination:
                time.sleep(3)
                instance.update()
            changed = True
        except boto.exception.BotoServerError as e:
            module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    return changed


def detach_volume(module, ec2, volume):

    changed = False

    if volume.attachment_state() is not None:
        adata = volume.attach_data
        volume.detach()
        while volume.attachment_state() is not None:
            time.sleep(3)
            volume.update()
        changed = True

    return volume, changed


def get_volume_info(volume, state):

    # If we're just listing volumes then do nothing, else get the latest update for the volume
    if state != 'list':
        volume.update()

    volume_info = {}
    attachment = volume.attach_data

    volume_info = {
        'create_time': volume.create_time,
        'encrypted': volume.encrypted,
        'id': volume.id,
        'iops': volume.iops,
        'size': volume.size,
        'snapshot_id': volume.snapshot_id,
        'status': volume.status,
        'type': volume.type,
        'zone': volume.zone,
        'attachment_set': {
            'attach_time': attachment.attach_time,
            'device': attachment.device,
            'instance_id': attachment.instance_id,
            'status': attachment.status
        },
        'tags': volume.tags
    }
    if hasattr(attachment, 'deleteOnTermination'):
        volume_info['attachment_set']['deleteOnTermination'] = attachment.deleteOnTermination

    return volume_info


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        instance=dict(),
        id=dict(),
        name=dict(),
        volume_size=dict(),
        volume_type=dict(choices=['standard', 'gp2', 'io1', 'st1', 'sc1'], default='standard'),
        iops=dict(),
        encrypted=dict(type='bool', default=False),
        kms_key_id=dict(),
        device_name=dict(),
        delete_on_termination=dict(type='bool', default=False),
        zone=dict(aliases=['availability_zone', 'aws_zone', 'ec2_zone']),
        snapshot=dict(),
        state=dict(choices=['absent', 'present', 'list'], default='present'),
        tags=dict(type='dict', default={})
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    id = module.params.get('id')
    name = module.params.get('name')
    instance = module.params.get('instance')
    volume_size = module.params.get('volume_size')
    encrypted = module.params.get('encrypted')
    kms_key_id = module.params.get('kms_key_id')
    device_name = module.params.get('device_name')
    zone = module.params.get('zone')
    snapshot = module.params.get('snapshot')
    state = module.params.get('state')
    tags = module.params.get('tags')

    # Ensure we have the zone or can get the zone
    if instance is None and zone is None and state == 'present':
        module.fail_json(msg="You must specify either instance or zone")

    # Set volume detach flag
    if instance == 'None' or instance == '':
        instance = None
        detach_vol_flag = True
    else:
        detach_vol_flag = False

    # Set changed flag
    changed = False

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            ec2 = connect_to_aws(boto.ec2, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    if state == 'list':
        returned_volumes = []
        vols = get_volumes(module, ec2)

        for v in vols:
            attachment = v.attach_data

            returned_volumes.append(get_volume_info(v, state))

        module.exit_json(changed=False, volumes=returned_volumes)

    if encrypted and not boto_supports_volume_encryption():
        module.fail_json(msg="You must use boto >= v2.29.0 to use encrypted volumes")

    if kms_key_id is not None and not boto_supports_kms_key_id():
        module.fail_json(msg="You must use boto >= v2.39.0 to use kms_key_id")

    # Here we need to get the zone info for the instance. This covers situation where
    # instance is specified but zone isn't.
    # Useful for playbooks chaining instance launch with volume create + attach and where the
    # zone doesn't matter to the user.
    inst = None
    if instance:
        try:
            reservation = ec2.get_all_instances(instance_ids=instance)
        except BotoServerError as e:
            module.fail_json(msg=e.message)
        inst = reservation[0].instances[0]
        zone = inst.placement

        # Check if there is a volume already mounted there.
        if device_name:
            if device_name in inst.block_device_mapping:
                module.exit_json(msg="Volume mapping for %s already exists on instance %s" % (device_name, instance),
                                 volume_id=inst.block_device_mapping[device_name].volume_id,
                                 device=device_name,
                                 changed=False)

    # Delaying the checks until after the instance check allows us to get volume ids for existing volumes
    # without needing to pass an unused volume_size
    if not volume_size and not (id or name or snapshot):
        module.fail_json(msg="You must specify volume_size or identify an existing volume by id, name, or snapshot")

    if volume_size and id:
        module.fail_json(msg="Cannot specify volume_size together with id")

    if state == 'present':
        volume, changed = create_volume(module, ec2, zone)
        if detach_vol_flag:
            volume, changed = detach_volume(module, ec2, volume)
        elif inst is not None:
            volume, changed = attach_volume(module, ec2, volume, inst)

        # Add device, volume_id and volume_type parameters separately to maintain backward compatibility
        volume_info = get_volume_info(volume, state)

        # deleteOnTermination is not correctly reflected on attachment
        if module.params.get('delete_on_termination'):
            for attempt in range(0, 8):
                if volume_info['attachment_set'].get('deleteOnTermination') == 'true':
                    break
                time.sleep(5)
                volume = ec2.get_all_volumes(volume_ids=volume.id)[0]
                volume_info = get_volume_info(volume, state)
        module.exit_json(changed=changed, volume=volume_info, device=volume_info['attachment_set']['device'],
                         volume_id=volume_info['id'], volume_type=volume_info['type'])
    elif state == 'absent':
        delete_volume(module, ec2)


if __name__ == '__main__':
    main()
