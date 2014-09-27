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
module: ec2_vol
short_description: create and attach a volume, return volume id and device map
description:
    - creates an EBS volume and optionally attaches it to an instance.  If both an instance ID and a device name is given and the instance has a device at the device name, then no volume is created and no attachment is made.  This module has a dependency on python-boto.
version_added: "1.1"
options:
  instance:
    description:
      - instance ID if you wish to attach the volume. 
    required: false
    default: null 
    aliases: []
  name:
    description:
      - volume Name tag if you wish to attach an existing volume (requires instance)
    required: false
    default: null
    aliases: []
    version_added: "1.6"
  id:
    description:
      - volume id if you wish to attach an existing volume (requires instance) or remove an existing volume
    required: false
    default: null
    aliases: []
    version_added: "1.6"
  volume_size:
    description:
      - size of volume (in GB) to create.
    required: false
    default: null
    aliases: []
  volume_type:
    description:
      - Type of EBS volume; standard (magnetic), gp2 (SSD), io1 (Provisioned IOPS). "Standard" is the old EBS default
        and continues to remain the Ansible default for backwards compatibility. 
    required: false
    default: standard
    aliases: []
  iops:
    description:
      - the provisioned IOPs you want to associate with this volume (integer).
    required: false
    default: 100
    aliases: []
    version_added: "1.3"
  encrypted:
    description:
      - Enable encryption at rest for this volume.
    default: false
    version_added: "1.8"
  device_name:
    description:
      - device id to override device mapping. Assumes /dev/sdf for Linux/UNIX and /dev/xvdf for Windows.
    required: false
    default: null
    aliases: []
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    default: null
    aliases: ['aws_region', 'ec2_region']
  zone:
    description:
      - zone in which to create the volume, if unset uses the zone the instance is in (if set) 
    required: false
    default: null
    aliases: ['aws_zone', 'ec2_zone']
  snapshot:
    description:
      - snapshot ID on which to base the volume
    required: false
    default: null
    version_added: "1.5"
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    required: false
    default: "yes"
    choices: ["yes", "no"]
    aliases: []
    version_added: "1.5"
  state:
    description: 
      - whether to ensure the volume is present or absent, or to list existing volumes (The C(list) option was added in version 1.8).
    required: false
    default: present
    choices: ['absent', 'present', 'list']
    version_added: "1.6"
author: Lester Wade
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Simple attachment action
- local_action: 
    module: ec2_vol 
    instance: XXXXXX 
    volume_size: 5 
    device_name: sdd

# Example using custom iops params   
- local_action: 
    module: ec2_vol 
    instance: XXXXXX 
    volume_size: 5 
    iops: 200
    device_name: sdd

# Example using snapshot id
- local_action:
    module: ec2_vol
    instance: XXXXXX
    snapshot: "{{ snapshot }}"

# Playbook example combined with instance launch 
- local_action: 
    module: ec2 
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    wait: yes 
    count: 3
    register: ec2
- local_action: 
    module: ec2_vol 
    instance: "{{ item.id }} " 
    volume_size: 5
    with_items: ec2.instances
    register: ec2_vol

# Example: Launch an instance and then add a volue if not already present
#   * Nothing will happen if the volume is already attached.
#   * Volume must exist in the same zone.

- local_action: 
    module: ec2 
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    zone: YYYYYY
    id: my_instance
    wait: yes 
    count: 1
    register: ec2

- local_action: 
    module: ec2_vol 
    instance: "{{ item.id }}" 
    name: my_existing_volume_Name_tag
    device_name: /dev/xvdf
    with_items: ec2.instances
    register: ec2_vol

# Remove a volume
- local_action:
    module: ec2_vol
    id: vol-XXXXXXXX
    state: absent

# List volumes for an instance
- local_action:
    module: ec2_vol
    instance: i-XXXXXX
    state: list
    
# Create new volume using SSD storage
- local_action: 
    module: ec2_vol 
    instance: XXXXXX 
    volume_size: 50 
    volume_type: gp2
    device_name: /dev/xvdf
'''

# Note: this module needs to be made idempotent. Possible solution is to use resource tags with the volumes.
# if state=present and it doesn't exist, create, tag and attach. 
# Check for state by looking for volume attachment with tag (and against block device mapping?).
# Would personally like to revisit this in May when Eucalyptus also has tagging support (3.3).

import sys
import time

from distutils.version import LooseVersion

try:
    import boto.ec2
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def get_volume(module, ec2):
    name = module.params.get('name')
    id = module.params.get('id')
    zone = module.params.get('zone')
    filters = {}
    volume_ids = None
    if zone:
        filters['availability_zone'] = zone
    if name:
        filters = {'tag:Name': name}
    if id:
        volume_ids = [id]
    try:
        vols = ec2.get_all_volumes(volume_ids=volume_ids, filters=filters)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

    if not vols:
        module.fail_json(msg="Could not find volume in zone (if specified): %s" % name or id)
    if len(vols) > 1:
        module.fail_json(msg="Found more than one volume in zone (if specified) with name: %s" % name)
    return vols[0]

def get_volumes(module, ec2):
    instance = module.params.get('instance')

    if not instance:
        module.fail_json(msg = "Instance must be specified to get volumes")

    try:
        vols = ec2.get_all_volumes(filters={'attachment.instance-id': instance})
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))
    return vols

def delete_volume(module, ec2):
    vol = get_volume(module, ec2)
    if not vol:
        module.exit_json(changed=False)
    else:
       if vol.attachment_state() is not None: 
           adata = vol.attach_data
           module.fail_json(msg="Volume %s is attached to an instance %s." % (vol.id, adata.instance_id))
       ec2.delete_volume(vol.id)
       module.exit_json(changed=True)

def boto_supports_volume_encryption():
    """
    Check if Boto library supports encryption of EBS volumes (added in 2.29.0)

    Returns:
        True if boto library has the named param as an argument on the request_spot_instances method, else False
    """
    return hasattr(boto, 'Version') and LooseVersion(boto.Version) >= LooseVersion('2.29.0')

def create_volume(module, ec2, zone):
    name = module.params.get('name')
    id = module.params.get('id')
    instance = module.params.get('instance')
    iops = module.params.get('iops')
    encrypted = module.params.get('encrypted')
    volume_size = module.params.get('volume_size')
    volume_type = module.params.get('volume_type')
    snapshot = module.params.get('snapshot')
    # If custom iops is defined we use volume_type "io1" rather than the default of "standard"
    if iops:
        volume_type = 'io1'

    # If no instance supplied, try volume creation based on module parameters.
    if name or id:
        if not instance:
            module.fail_json(msg = "If name or id is specified, instance must also be specified")
        if iops or volume_size:
            module.fail_json(msg = "Parameters are not compatible: [id or name] and [iops or volume_size]")

        volume = get_volume(module, ec2)
        if volume.attachment_state() is not None:
            adata = volume.attach_data
            if adata.instance_id != instance:
                module.fail_json(msg = "Volume %s is already attached to another instance: %s"
                                 % (name or id, adata.instance_id))
            else:
                module.exit_json(msg="Volume %s is already mapped on instance %s: %s" %
                                 (name or id, adata.instance_id, adata.device),
                                 volume_id=id,
                                 device=adata.device,
                                 changed=False)
    else:
        try:
            if boto_supports_volume_encryption():
                volume = ec2.create_volume(volume_size, zone, snapshot, volume_type, iops, encrypted)
            else:
                volume = ec2.create_volume(volume_size, zone, snapshot, volume_type, iops)

            while volume.status != 'available':
                time.sleep(3)
                volume.update()
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))
    return volume


def attach_volume(module, ec2, volume, instance):
    device_name = module.params.get('device_name')

    if device_name and instance:
        try:
            attach = volume.attach(instance.id, device_name)
            while volume.attachment_state() != 'attached':
                time.sleep(3)
                volume.update()
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

    # If device_name isn't set, make a choice based on best practices here:
    # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/block-device-mapping-concepts.html

    # In future this needs to be more dynamic but combining block device mapping best practices
    # (bounds for devices, as above) with instance.block_device_mapping data would be tricky. For me ;)

    # Use password data attribute to tell whether the instance is Windows or Linux
    if device_name is None and instance:
        try:
            if not ec2.get_password_data(instance.id):
                device_name = '/dev/sdf'
                attach = volume.attach(instance.id, device_name)
                while volume.attachment_state() != 'attached':
                    time.sleep(3)
                    volume.update()
            else:
                device_name = '/dev/xvdf'
                attach = volume.attach(instance.id, device_name)
                while volume.attachment_state() != 'attached':
                    time.sleep(3)
                    volume.update()
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            instance = dict(),
            id = dict(),
            name = dict(),
            volume_size = dict(),
            volume_type = dict(choices=['standard', 'gp2', 'io1'], default='standard'),
            iops = dict(),
            encrypted = dict(),
            device_name = dict(),
            zone = dict(aliases=['availability_zone', 'aws_zone', 'ec2_zone']),
            snapshot = dict(),
            state = dict(choices=['absent', 'present', 'list'], default='present')
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    id = module.params.get('id')
    name = module.params.get('name')
    instance = module.params.get('instance')
    volume_size = module.params.get('volume_size')
    volume_type = module.params.get('volume_type')
    iops = module.params.get('iops')
    encrypted = module.params.get('encrypted')
    device_name = module.params.get('device_name')
    zone = module.params.get('zone')
    snapshot = module.params.get('snapshot')
    state = module.params.get('state')

    ec2 = ec2_connect(module)

    if state == 'list':
        returned_volumes = []
        vols = get_volumes(module, ec2)

        for v in vols:
            attachment = v.attach_data

            returned_volumes.append({
                'create_time': v.create_time,
                'id': v.id,
                'iops': v.iops,
                'size': v.size,
                'snapshot_id': v.snapshot_id,
                'status': v.status,
                'type': v.type,
                'zone': v.zone,
                'attachment_set': {
                    'attach_time': attachment.attach_time,
                    'device': attachment.device,
                    'status': attachment.status
                }
            })

        module.exit_json(changed=False, volumes=returned_volumes)

    if id and name:
        module.fail_json(msg="Both id and name cannot be specified")

    if encrypted and not boto_supports_volume_encryption():
        module.fail_json(msg="You must use boto >= v2.29.0 to use encrypted volumes")

    # Here we need to get the zone info for the instance. This covers situation where 
    # instance is specified but zone isn't.
    # Useful for playbooks chaining instance launch with volume create + attach and where the
    # zone doesn't matter to the user.
    if instance:
        reservation = ec2.get_all_instances(instance_ids=instance)
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
    if not volume_size and not (id or name):
        module.fail_json(msg="You must specify an existing volume with id or name or a volume_size")

    if volume_size and (id or name):
        module.fail_json(msg="Cannot specify volume_size and either one of name or id")


    if state == 'absent':
        delete_volume(module, ec2)

    if state == 'present':
        volume = create_volume(module, ec2, zone)
        if instance:
            attach_volume(module, ec2, volume, inst)
        module.exit_json(volume_id=volume.id, device=device_name, volume_type=volume.type)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
