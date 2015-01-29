#!/usr/bin/python
# Copyright 2013 Google Inc.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: gce_pd
version_added: "1.4"
short_description: utilize GCE persistent disk resources
description:
    - This module can create and destroy unformatted GCE persistent disks
      U(https://developers.google.com/compute/docs/disks#persistentdisks).
      It also supports attaching and detaching disks from running instances.
      Full install/configuration instructions for the gce* modules can
      be found in the comments of ansible/test/gce_tests.py.
options:
  detach_only:
    description:
      - do not destroy the disk, merely detach it from an instance
    required: false
    default: "no"
    choices: ["yes", "no"]
    aliases: []
  instance_name:
    description:
      - instance name if you wish to attach or detach the disk 
    required: false
    default: null 
    aliases: []
  mode:
    description:
      - GCE mount mode of disk, READ_ONLY (default) or READ_WRITE
    required: false
    default: "READ_ONLY" 
    choices: ["READ_WRITE", "READ_ONLY"]
    aliases: []
  name:
    description:
      - name of the disk
    required: true
    default: null 
    aliases: []
  size_gb:
    description:
      - whole integer size of disk (in GB) to create, default is 10 GB
    required: false
    default: 10
    aliases: []
  image:
    description:
      - the source image to use for the disk
    required: false
    default: null
    aliases: []
    version_added: "1.7"
  snapshot:
    description:
      - the source snapshot to use for the disk
    required: false
    default: null
    aliases: []
    version_added: "1.7"
  state:
    description:
      - desired state of the persistent disk
    required: false
    default: "present"
    choices: ["active", "present", "absent", "deleted"]
    aliases: []
  zone:
    description:
      - zone in which to create the disk
    required: false
    default: "us-central1-b"
    aliases: []
  service_account_email:
    version_added: "1.6"
    description:
      - service account email
    required: false
    default: null
    aliases: []
  pem_file:
    version_added: "1.6"
    description:
      - path to the pem file associated with the service account email
    required: false
    default: null
    aliases: []
  project_id:
    version_added: "1.6"
    description:
      - your GCE project ID
    required: false
    default: null
    aliases: []
  disk_type:
    version_added: "1.9"
    description:
      - type of disk provisioned
    required: false
    default: "pd-standard"
    choices: ["pd-standard", "pd-ssd"]
    aliases: []

requirements: [ "libcloud" ]
author: Eric Johnson <erjohnso@google.com>
'''

EXAMPLES = '''
# Simple attachment action to an existing instance
- local_action:
    module: gce_pd
    instance_name: notlocalhost
    size_gb: 5
    name: pd
'''

import sys

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
            ResourceExistsError, ResourceNotFoundError, ResourceInUseError
    _ = Provider.GCE
except ImportError:
    print("failed=True " + \
        "msg='libcloud with GCE support is required for this module.'")
    sys.exit(1)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            detach_only = dict(type='bool'),
            instance_name = dict(),
            mode = dict(default='READ_ONLY', choices=['READ_WRITE', 'READ_ONLY']),
            name = dict(required=True),
            size_gb = dict(default=10),
            disk_type = dict(default='pd-standard'),
            image = dict(),
            snapshot = dict(),
            state = dict(default='present'),
            zone = dict(default='us-central1-b'),
            service_account_email = dict(),
            pem_file = dict(),
            project_id = dict(),
        )
    )

    gce = gce_connect(module)

    detach_only = module.params.get('detach_only')
    instance_name = module.params.get('instance_name')
    mode = module.params.get('mode')
    name = module.params.get('name')
    size_gb = module.params.get('size_gb')
    disk_type = module.params.get('disk_type')
    image = module.params.get('image')
    snapshot = module.params.get('snapshot')
    state = module.params.get('state')
    zone = module.params.get('zone')

    if detach_only and not instance_name:
        module.fail_json(
            msg='Must specify an instance name when detaching a disk',
            changed=False)

    disk = inst = None
    changed = is_attached = False

    json_output = { 'name': name, 'zone': zone, 'state': state, 'disk_type': disk_type  }
    if detach_only:
        json_output['detach_only'] = True
        json_output['detached_from_instance'] = instance_name

    if instance_name:
        # user wants to attach/detach from an existing instance
        try:
            inst = gce.ex_get_node(instance_name, zone)
            # is the disk attached?
            for d in inst.extra['disks']:
                if d['deviceName'] == name:
                    is_attached = True
                    json_output['attached_mode'] = d['mode']
                    json_output['attached_to_instance'] = inst.name
        except:
            pass

    # find disk if it already exists
    try:
        disk = gce.ex_get_volume(name)
        json_output['size_gb'] = int(disk.size)
    except ResourceNotFoundError:
        pass
    except Exception, e:
        module.fail_json(msg=unexpected_error_msg(e), changed=False)

    # user wants a disk to exist.  If "instance_name" is supplied the user
    # also wants it attached
    if state in ['active', 'present']:

        if not size_gb:
            module.fail_json(msg="Must supply a size_gb", changed=False)
        try:
            size_gb = int(round(float(size_gb)))
            if size_gb < 1: 
                raise Exception
        except:        
            module.fail_json(msg="Must supply a size_gb larger than 1 GB",
                    changed=False)

        if instance_name and inst is None:
            module.fail_json(msg='Instance %s does not exist in zone %s' % (
                    instance_name, zone), changed=False)

        if not disk:
            if image is not None and snapshot is not None:
                module.fail_json(
                    msg='Cannot give both image (%s) and snapshot (%s)' % (
                        image, snapshot), changed=False)
            lc_image = None
            lc_snapshot = None
            if image is not None:
                lc_image = gce.ex_get_image(image)
            elif snapshot is not None:
                lc_snapshot = gce.ex_get_snapshot(snapshot)
            try:
                disk = gce.create_volume(
                    size_gb, name, location=zone, image=lc_image,
                    snapshot=lc_snapshot, ex_disk_type=disk_type)
            except ResourceExistsError:
                pass
            except QuotaExceededError:
                module.fail_json(msg='Requested disk size exceeds quota',
                        changed=False)
            except Exception, e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            json_output['size_gb'] = size_gb
            if image is not None:
                json_output['image'] = image
            if snapshot is not None:
                json_output['snapshot'] = snapshot
            changed = True
        if inst and not is_attached:
            try:
                gce.attach_volume(inst, disk, device=name, ex_mode=mode)
            except Exception, e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            json_output['attached_to_instance'] = inst.name
            json_output['attached_mode'] = mode
            changed = True

    # user wants to delete a disk (or perhaps just detach it).
    if state in ['absent', 'deleted'] and disk:

        if inst and is_attached:
            try:
                gce.detach_volume(disk, ex_node=inst)
            except Exception, e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            changed = True
        if not detach_only:
            try:
                gce.destroy_volume(disk)
            except ResourceInUseError, e:
                module.fail_json(msg=str(e.value), changed=False)
            except Exception, e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            changed = True

    json_output['changed'] = changed
    print json.dumps(json_output)
    sys.exit(0)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.gce import *

main()
