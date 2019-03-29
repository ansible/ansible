#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Jefferson Girão <jefferson@girao.net>
# (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_volume
short_description: Manages volumes on Apache CloudStack based clouds.
description:
    - Create, destroy, attach, detach, extract or upload volumes.
version_added: '2.1'
author:
    - Jefferson Girão (@jeffersongirao)
    - René Moser (@resmo)
options:
  name:
    description:
      - Name of the volume.
      - I(name) can only contain ASCII letters.
    type: str
    required: true
  account:
    description:
      - Account the volume is related to.
    type: str
  device_id:
    description:
      - ID of the device on a VM the volume is attached to.
      - Only considered if I(state) is C(attached).
    type: int
  custom_id:
    description:
      - Custom id to the resource.
      - Allowed to Root Admins only.
    type: str
  disk_offering:
    description:
      - Name of the disk offering to be used.
      - Required one of I(disk_offering), I(snapshot) if volume is not already I(state=present).
    type: str
  display_volume:
    description:
      - Whether to display the volume to the end user or not.
      - Allowed to Root Admins only.
    type: bool
  domain:
    description:
      - Name of the domain the volume to be deployed in.
    type: str
  max_iops:
    description:
      - Max iops
    type: int
  min_iops:
    description:
      - Min iops
    type: int
  project:
    description:
      - Name of the project the volume to be deployed in.
    type: str
  size:
    description:
      - Size of disk in GB
    type: int
  snapshot:
    description:
      - The snapshot name for the disk volume.
      - Required one of I(disk_offering), I(snapshot) if volume is not already I(state=present).
    type: str
  force:
    description:
      - Force removal of volume even it is attached to a VM.
      - Considered on I(state=absent) only.
    default: no
    type: bool
  shrink_ok:
    description:
      - Whether to allow to shrink the volume.
    default: no
    type: bool
  vm:
    description:
      - Name of the virtual machine to attach the volume to.
    type: str
  zone:
    description:
      - Name of the zone in which the volume should be deployed.
      - If not set, default zone is used.
    type: str
  state:
    description:
      - State of the volume.
      - The choices C(extracted) and C(uploaded) were added in version 2.8.
    type: str
    default: present
    choices: [ present, absent, attached, detached, extracted, uploaded ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
  tags:
    description:
      - List of tags. Tags are a list of dictionaries having keys I(key) and I(value).
      - "To delete all tags, set a empty list e.g. I(tags: [])."
    type: list
    aliases: [ tag ]
    version_added: '2.4'
  url:
    description:
      - URL to which the volume would be extracted on I(state=extracted)
      - or the URL where to download the volume on I(state=uploaded).
      - Only considered if I(state) is C(extracted) or C(uploaded).
    type: str
    version_added: '2.8'
  mode:
    description:
      - Mode for the volume extraction.
      - Only considered if I(state=extracted).
    type: str
    choices: [ http_download, ftp_upload ]
    default: http_download
    version_added: '2.8'
  format:
    description:
      - The format for the volume.
      - Only considered if I(state=uploaded).
    type: str
    choices: [ QCOW2, RAW, VHD, VHDX, OVA ]
    version_added: '2.8'
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: create volume within project and zone with specified storage options
  cs_volume:
    name: web-vm-1-volume
    project: Integration
    zone: ch-zrh-ix-01
    disk_offering: PerfPlus Storage
    size: 20
  delegate_to: localhost

- name: create/attach volume to instance
  cs_volume:
    name: web-vm-1-volume
    disk_offering: PerfPlus Storage
    size: 20
    vm: web-vm-1
    state: attached
  delegate_to: localhost

- name: detach volume
  cs_volume:
    name: web-vm-1-volume
    state: detached
  delegate_to: localhost

- name: remove volume
  cs_volume:
    name: web-vm-1-volume
    state: absent
  delegate_to: localhost

# New in version 2.8
- name: Extract DATA volume to make it downloadable
  cs_volume:
    state: extracted
    name: web-vm-1-volume
  register: data_vol_out
  delegate_to: localhost

- name: Create new volume by downloading source volume
  cs_volume:
    state: uploaded
    name: web-vm-1-volume-2
    format: VHD
    url: "{{ data_vol_out.url }}"
  delegate_to: localhost
'''

RETURN = '''
id:
  description: ID of the volume.
  returned: success
  type: str
  sample:
name:
  description: Name of the volume.
  returned: success
  type: str
  sample: web-volume-01
display_name:
  description: Display name of the volume.
  returned: success
  type: str
  sample: web-volume-01
group:
  description: Group the volume belongs to
  returned: success
  type: str
  sample: web
domain:
  description: Domain the volume belongs to
  returned: success
  type: str
  sample: example domain
project:
  description: Project the volume belongs to
  returned: success
  type: str
  sample: Production
zone:
  description: Name of zone the volume is in.
  returned: success
  type: str
  sample: ch-gva-2
created:
  description: Date of the volume was created.
  returned: success
  type: str
  sample: 2014-12-01T14:57:57+0100
attached:
  description: Date of the volume was attached.
  returned: success
  type: str
  sample: 2014-12-01T14:57:57+0100
type:
  description: Disk volume type.
  returned: success
  type: str
  sample: DATADISK
size:
  description: Size of disk volume.
  returned: success
  type: int
  sample: 20
vm:
  description: Name of the vm the volume is attached to (not returned when detached)
  returned: success
  type: str
  sample: web-01
state:
  description: State of the volume
  returned: success
  type: str
  sample: Attached
device_id:
  description: Id of the device on user vm the volume is attached to (not returned when detached)
  returned: success
  type: int
  sample: 1
url:
  description: The url of the uploaded volume or the download url depending extraction mode.
  returned: success when I(state=extracted)
  type: str
  sample: http://1.12.3.4/userdata/387e2c7c-7c42-4ecc-b4ed-84e8367a1965.vhd
  version_added: '2.8'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_required_together,
    cs_argument_spec
)


class AnsibleCloudStackVolume(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackVolume, self).__init__(module)
        self.returns = {
            'group': 'group',
            'attached': 'attached',
            'vmname': 'vm',
            'deviceid': 'device_id',
            'type': 'type',
            'size': 'size',
            'url': 'url',
        }
        self.volume = None

    def get_volume(self):
        if not self.volume:
            args = {
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'projectid': self.get_project(key='id'),
                'zoneid': self.get_zone(key='id'),
                'displayvolume': self.module.params.get('display_volume'),
                'type': 'DATADISK',
                'fetch_list': True,
            }
            # Do not filter on DATADISK when state=extracted
            if self.module.params.get('state') == 'extracted':
                del args['type']

            volumes = self.query_api('listVolumes', **args)
            if volumes:
                volume_name = self.module.params.get('name')
                for v in volumes:
                    if volume_name.lower() == v['name'].lower():
                        self.volume = v
                        break
        return self.volume

    def get_snapshot(self, key=None):
        snapshot = self.module.params.get('snapshot')
        if not snapshot:
            return None

        args = {
            'name': snapshot,
            'account': self.get_account('name'),
            'domainid': self.get_domain('id'),
            'projectid': self.get_project('id'),
        }
        snapshots = self.query_api('listSnapshots', **args)
        if snapshots:
            return self._get_by_key(key, snapshots['snapshot'][0])
        self.module.fail_json(msg="Snapshot with name %s not found" % snapshot)

    def present_volume(self):
        volume = self.get_volume()
        if volume:
            volume = self.update_volume(volume)
        else:
            disk_offering_id = self.get_disk_offering(key='id')
            snapshot_id = self.get_snapshot(key='id')

            if not disk_offering_id and not snapshot_id:
                self.module.fail_json(msg="Required one of: disk_offering,snapshot")

            self.result['changed'] = True

            args = {
                'name': self.module.params.get('name'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'diskofferingid': disk_offering_id,
                'displayvolume': self.module.params.get('display_volume'),
                'maxiops': self.module.params.get('max_iops'),
                'miniops': self.module.params.get('min_iops'),
                'projectid': self.get_project(key='id'),
                'size': self.module.params.get('size'),
                'snapshotid': snapshot_id,
                'zoneid': self.get_zone(key='id')
            }
            if not self.module.check_mode:
                res = self.query_api('createVolume', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    volume = self.poll_job(res, 'volume')
        if volume:
            volume = self.ensure_tags(resource=volume, resource_type='Volume')
            self.volume = volume

        return volume

    def attached_volume(self):
        volume = self.present_volume()

        if volume:
            if volume.get('virtualmachineid') != self.get_vm(key='id'):
                self.result['changed'] = True

                if not self.module.check_mode:
                    volume = self.detached_volume()

            if 'attached' not in volume:
                self.result['changed'] = True

                args = {
                    'id': volume['id'],
                    'virtualmachineid': self.get_vm(key='id'),
                    'deviceid': self.module.params.get('device_id'),
                }
                if not self.module.check_mode:
                    res = self.query_api('attachVolume', **args)
                    poll_async = self.module.params.get('poll_async')
                    if poll_async:
                        volume = self.poll_job(res, 'volume')
        return volume

    def detached_volume(self):
        volume = self.present_volume()

        if volume:
            if 'attached' not in volume:
                return volume

            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('detachVolume', id=volume['id'])
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    volume = self.poll_job(res, 'volume')
        return volume

    def absent_volume(self):
        volume = self.get_volume()

        if volume:
            if 'attached' in volume and not self.module.params.get('force'):
                self.module.fail_json(msg="Volume '%s' is attached, use force=true for detaching and removing the volume." % volume.get('name'))

            self.result['changed'] = True
            if not self.module.check_mode:
                volume = self.detached_volume()
                res = self.query_api('deleteVolume', id=volume['id'])
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'volume')

        return volume

    def update_volume(self, volume):
        args_resize = {
            'id': volume['id'],
            'diskofferingid': self.get_disk_offering(key='id'),
            'maxiops': self.module.params.get('max_iops'),
            'miniops': self.module.params.get('min_iops'),
            'size': self.module.params.get('size')
        }
        # change unit from bytes to giga bytes to compare with args
        volume_copy = volume.copy()
        volume_copy['size'] = volume_copy['size'] / (2**30)

        if self.has_changed(args_resize, volume_copy):

            self.result['changed'] = True
            if not self.module.check_mode:
                args_resize['shrinkok'] = self.module.params.get('shrink_ok')
                res = self.query_api('resizeVolume', **args_resize)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    volume = self.poll_job(res, 'volume')
                self.volume = volume

        return volume

    def extract_volume(self):
        volume = self.get_volume()
        if not volume:
            self.module.fail_json(msg="Failed: volume not found")

        args = {
            'id': volume['id'],
            'url': self.module.params.get('url'),
            'mode': self.module.params.get('mode').upper(),
            'zoneid': self.get_zone(key='id')
        }
        self.result['changed'] = True

        if not self.module.check_mode:
            res = self.query_api('extractVolume', **args)
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                volume = self.poll_job(res, 'volume')
            self.volume = volume

        return volume

    def upload_volume(self):
        volume = self.get_volume()
        if not volume:
            disk_offering_id = self.get_disk_offering(key='id')

            self.result['changed'] = True

            args = {
                'name': self.module.params.get('name'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'projectid': self.get_project(key='id'),
                'zoneid': self.get_zone(key='id'),
                'format': self.module.params.get('format'),
                'url': self.module.params.get('url'),
                'diskofferingid': disk_offering_id,
            }
            if not self.module.check_mode:
                res = self.query_api('uploadVolume', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    volume = self.poll_job(res, 'volume')
        if volume:
            volume = self.ensure_tags(resource=volume, resource_type='Volume')
            self.volume = volume

        return volume


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        disk_offering=dict(),
        display_volume=dict(type='bool'),
        max_iops=dict(type='int'),
        min_iops=dict(type='int'),
        size=dict(type='int'),
        snapshot=dict(),
        vm=dict(),
        device_id=dict(type='int'),
        custom_id=dict(),
        force=dict(type='bool', default=False),
        shrink_ok=dict(type='bool', default=False),
        state=dict(default='present', choices=[
            'present',
            'absent',
            'attached',
            'detached',
            'extracted',
            'uploaded',
        ]),
        zone=dict(),
        domain=dict(),
        account=dict(),
        project=dict(),
        poll_async=dict(type='bool', default=True),
        tags=dict(type='list', aliases=['tag']),
        url=dict(),
        mode=dict(choices=['http_download', 'ftp_upload'], default='http_download'),
        format=dict(choices=['QCOW2', 'RAW', 'VHD', 'VHDX', 'OVA']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        mutually_exclusive=(
            ['snapshot', 'disk_offering'],
        ),
        required_if=[
            ('state', 'uploaded', ['url', 'format']),
        ],
        supports_check_mode=True
    )

    acs_vol = AnsibleCloudStackVolume(module)

    state = module.params.get('state')

    if state in ['absent']:
        volume = acs_vol.absent_volume()
    elif state in ['attached']:
        volume = acs_vol.attached_volume()
    elif state in ['detached']:
        volume = acs_vol.detached_volume()
    elif state == 'extracted':
        volume = acs_vol.extract_volume()
    elif state == 'uploaded':
        volume = acs_vol.upload_volume()
    else:
        volume = acs_vol.present_volume()

    result = acs_vol.get_result(volume)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
