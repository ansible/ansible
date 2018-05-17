#!/usr/bin/python
# Copyright 2013 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
    type: bool
    default: 'no'
  instance_name:
    description:
      - instance name if you wish to attach or detach the disk
  mode:
    description:
      - GCE mount mode of disk, READ_ONLY (default) or READ_WRITE
    default: "READ_ONLY"
    choices: ["READ_WRITE", "READ_ONLY"]
  name:
    description:
      - name of the disk
    required: true
  size_gb:
    description:
      - whole integer size of disk (in GB) to create, default is 10 GB
    default: 10
  image:
    description:
      - the source image to use for the disk
    version_added: "1.7"
  snapshot:
    description:
      - the source snapshot to use for the disk
    version_added: "1.7"
  state:
    description:
      - desired state of the persistent disk
    default: "present"
    choices: ["active", "present", "absent", "deleted"]
  zone:
    description:
      - zone in which to create the disk
    default: "us-central1-b"
  service_account_email:
    version_added: "1.6"
    description:
      - service account email
  pem_file:
    version_added: "1.6"
    description:
      - path to the pem file associated with the service account email
        This option is deprecated. Use 'credentials_file'.
  credentials_file:
    version_added: "2.1.0"
    description:
      - path to the JSON file associated with the service account email
  project_id:
    version_added: "1.6"
    description:
      - your GCE project ID
  disk_type:
    version_added: "1.9"
    description:
      - type of disk provisioned
    default: "pd-standard"
    choices: ["pd-standard", "pd-ssd"]
  delete_on_termination:
    version_added: "2.3"
    description:
      - If C(yes), deletes the volume when instance is terminated
    type: bool
    default: 'no'

requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.13.3, >= 0.17.0 if using JSON credentials"
author: "Eric Johnson (@erjohnso) <erjohnso@google.com>"
'''

EXAMPLES = '''
# Simple attachment action to an existing instance
- local_action:
    module: gce_pd
    instance_name: notlocalhost
    size_gb: 5
    name: pd
'''

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, ResourceExistsError, ResourceNotFoundError, ResourceInUseError
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect, unexpected_error_msg


def main():
    module = AnsibleModule(
        argument_spec=dict(
            delete_on_termination=dict(type='bool'),
            detach_only=dict(type='bool'),
            instance_name=dict(),
            mode=dict(default='READ_ONLY', choices=['READ_WRITE', 'READ_ONLY']),
            name=dict(required=True),
            size_gb=dict(default=10),
            disk_type=dict(default='pd-standard'),
            image=dict(),
            image_family=dict(),
            external_projects=dict(type='list'),
            snapshot=dict(),
            state=dict(default='present'),
            zone=dict(default='us-central1-b'),
            service_account_email=dict(),
            pem_file=dict(type='path'),
            credentials_file=dict(type='path'),
            project_id=dict(),
        )
    )
    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support (0.17.0+) is required for this module')

    gce = gce_connect(module)

    delete_on_termination = module.params.get('delete_on_termination')
    detach_only = module.params.get('detach_only')
    instance_name = module.params.get('instance_name')
    mode = module.params.get('mode')
    name = module.params.get('name')
    size_gb = module.params.get('size_gb')
    disk_type = module.params.get('disk_type')
    image = module.params.get('image')
    image_family = module.params.get('image_family')
    external_projects = module.params.get('external_projects')
    snapshot = module.params.get('snapshot')
    state = module.params.get('state')
    zone = module.params.get('zone')

    if delete_on_termination and not instance_name:
        module.fail_json(
            msg='Must specify an instance name when requesting delete on termination',
            changed=False)

    if detach_only and not instance_name:
        module.fail_json(
            msg='Must specify an instance name when detaching a disk',
            changed=False)

    disk = inst = None
    changed = is_attached = False

    json_output = {'name': name, 'zone': zone, 'state': state, 'disk_type': disk_type}
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
    except Exception as e:
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
            if image_family is not None:
                lc_image = gce.ex_get_image_from_family(image_family, ex_project_list=external_projects)
            elif image is not None:
                lc_image = gce.ex_get_image(image, ex_project_list=external_projects)
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
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            json_output['size_gb'] = size_gb
            if image is not None:
                json_output['image'] = image
            if snapshot is not None:
                json_output['snapshot'] = snapshot
            changed = True
        if inst and not is_attached:
            try:
                gce.attach_volume(inst, disk, device=name, ex_mode=mode,
                                  ex_auto_delete=delete_on_termination)
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            json_output['attached_to_instance'] = inst.name
            json_output['attached_mode'] = mode
            if delete_on_termination:
                json_output['delete_on_termination'] = True
            changed = True

    # user wants to delete a disk (or perhaps just detach it).
    if state in ['absent', 'deleted'] and disk:

        if inst and is_attached:
            try:
                gce.detach_volume(disk, ex_node=inst)
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            changed = True
        if not detach_only:
            try:
                gce.destroy_volume(disk)
            except ResourceInUseError as e:
                module.fail_json(msg=str(e.value), changed=False)
            except Exception as e:
                module.fail_json(msg=unexpected_error_msg(e), changed=False)
            changed = True

    json_output['changed'] = changed
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
