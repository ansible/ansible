#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Jefferson Girão <jefferson@girao.net>
# (c) 2015, René Moser <mail@renemoser.net>
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
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_volume
short_description: Manages volumes on Apache CloudStack based clouds.
description:
    - Create, destroy, attach, detach volumes.
version_added: "2.1"
author:
    - "Jefferson Girão (@jeffersongirao)"
    - "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the volume.
      - C(name) can only contain ASCII letters.
    required: true
  account:
    description:
      - Account the volume is related to.
    required: false
    default: null
  custom_id:
    description:
      - Custom id to the resource.
      - Allowed to Root Admins only.
    required: false
    default: null
  disk_offering:
    description:
      - Name of the disk offering to be used.
      - Required one of C(disk_offering), C(snapshot) if volume is not already C(state=present).
    required: false
    default: null
  display_volume:
    description:
      - Whether to display the volume to the end user or not.
      - Allowed to Root Admins only.
    required: false
    default: true
  domain:
    description:
      - Name of the domain the volume to be deployed in.
    required: false
    default: null
  max_iops:
    description:
      - Max iops
    required: false
    default: null
  min_iops:
    description:
      - Min iops
    required: false
    default: null
  project:
    description:
      - Name of the project the volume to be deployed in.
    required: false
    default: null
  size:
    description:
      - Size of disk in GB
    required: false
    default: null
  snapshot:
    description:
      - The snapshot name for the disk volume.
      - Required one of C(disk_offering), C(snapshot) if volume is not already C(state=present).
    required: false
    default: null
  force:
    description:
      - Force removal of volume even it is attached to a VM.
      - Considered on C(state=absnet) only.
    required: false
    default: false
  shrink_ok:
    description:
      - Whether to allow to shrink the volume.
    required: false
    default: false
  vm:
    description:
      - Name of the virtual machine to attach the volume to.
    required: false
    default: null
  zone:
    description:
      - Name of the zone in which the volume should be deployed.
      - If not set, default zone is used.
    required: false
    default: null
  state:
    description:
      - State of the volume.
    required: false
    default: 'present'
    choices: [ 'present', 'absent', 'attached', 'detached' ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Create volume within project, zone with specified storage options
- local_action:
    module: cs_volume
    name: web-vm-1-volume
    project: Integration
    zone: ch-zrh-ix-01
    disk_offering: PerfPlus Storage
    size: 20

# Create/attach volume to instance
- local_action:
    module: cs_volume
    name: web-vm-1-volume
    disk_offering: PerfPlus Storage
    size: 20
    vm: web-vm-1
    state: attached

# Detach volume
- local_action:
    module: cs_volume
    name: web-vm-1-volume
    state: detached

# Remove volume
- local_action:
    module: cs_volume
    name: web-vm-1-volume
    state: absent
'''

RETURN = '''
id:
  description: ID of the volume.
  returned: success
  type: string
  sample:
name:
  description: Name of the volume.
  returned: success
  type: string
  sample: web-volume-01
display_name:
  description: Display name of the volume.
  returned: success
  type: string
  sample: web-volume-01
group:
  description: Group the volume belongs to
  returned: success
  type: string
  sample: web
domain:
  description: Domain the volume belongs to
  returned: success
  type: string
  sample: example domain
project:
  description: Project the volume belongs to
  returned: success
  type: string
  sample: Production
zone:
  description: Name of zone the volume is in.
  returned: success
  type: string
  sample: ch-gva-2
created:
  description: Date of the volume was created.
  returned: success
  type: string
  sample: 2014-12-01T14:57:57+0100
attached:
  description: Date of the volume was attached.
  returned: success
  type: string
  sample: 2014-12-01T14:57:57+0100
type:
  description: Disk volume type.
  returned: success
  type: string
  sample: DATADISK
size:
  description: Size of disk volume.
  returned: success
  type: string
  sample: 20
vm:
  description: Name of the vm the volume is attached to (not returned when detached)
  returned: success
  type: string
  sample: web-01
state:
  description: State of the volume
  returned: success
  type: string
  sample: Attached
device_id:
  description: Id of the device on user vm the volume is attached to (not returned when detached)
  returned: success
  type: string
  sample: 1
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackVolume(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackVolume, self).__init__(module)
        self.returns = {
            'group':            'group',
            'attached':         'attached',
            'vmname':           'vm',
            'deviceid':         'device_id',
            'type':             'type',
            'size':             'size',
        }
        self.volume = None

    #TODO implement in cloudstack utils
    def get_disk_offering(self, key=None):
        disk_offering = self.module.params.get('disk_offering')
        if not disk_offering:
            return None

        # Do not add domain filter for disk offering listing.
        disk_offerings = self.cs.listDiskOfferings()
        if disk_offerings:
            for d in disk_offerings['diskoffering']:
                if disk_offering in [d['displaytext'], d['name'], d['id']]:
                    return self._get_by_key(key, d)
        self.module.fail_json(msg="Disk offering '%s' not found" % disk_offering)


    def get_volume(self):
        if not self.volume:
            args = {}
            args['account'] = self.get_account(key='name')
            args['domainid'] = self.get_domain(key='id')
            args['projectid'] = self.get_project(key='id')
            args['zoneid'] = self.get_zone(key='id')
            args['displayvolume'] = self.module.params.get('display_volume')
            args['type'] = 'DATADISK'

            volumes = self.cs.listVolumes(**args)
            if volumes:
                volume_name = self.module.params.get('name')
                for v in volumes['volume']:
                    if volume_name.lower() == v['name'].lower():
                        self.volume = v
                        break
        return self.volume


    def get_snapshot(self, key=None):
        snapshot = self.module.params.get('snapshot')
        if not snapshot:
            return None

        args = {}
        args['name'] = snapshot
        args['account'] = self.get_account('name')
        args['domainid'] = self.get_domain('id')
        args['projectid'] = self.get_project('id')

        snapshots = self.cs.listSnapshots(**args)
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

            args = {}
            args['name'] = self.module.params.get('name')
            args['account'] = self.get_account(key='name')
            args['domainid'] = self.get_domain(key='id')
            args['diskofferingid'] = disk_offering_id
            args['displayvolume'] = self.module.params.get('display_volume')
            args['maxiops'] = self.module.params.get('max_iops')
            args['miniops'] = self.module.params.get('min_iops')
            args['projectid'] = self.get_project(key='id')
            args['size'] = self.module.params.get('size')
            args['snapshotid'] = snapshot_id
            args['zoneid'] = self.get_zone(key='id')

            if not self.module.check_mode:
                res = self.cs.createVolume(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    volume = self.poll_job(res, 'volume')
        return volume


    def attached_volume(self):
        volume = self.present_volume()

        if volume.get('virtualmachineid') != self.get_vm(key='id'):
            self.result['changed'] = True

            if not self.module.check_mode:
                volume = self.detached_volume()

        if 'attached' not in volume:
            self.result['changed'] = True

            args = {}
            args['id'] = volume['id']
            args['virtualmachineid'] = self.get_vm(key='id')
            args['deviceid'] = self.module.params.get('device_id')

            if not self.module.check_mode:
                res = self.cs.attachVolume(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
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
                res = self.cs.detachVolume(id=volume['id'])
                if 'errortext' in volume:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    volume = self.poll_job(res, 'volume')
        return volume


    def absent_volume(self):
        volume = self.get_volume()

        if volume:
            if 'attached' in volume and not self.module.param.get('force'):
                self.module.fail_json(msg="Volume '%s' is attached, use force=true for detaching and removing the volume." % volume.get('name'))

            self.result['changed'] = True
            if not self.module.check_mode:
                volume = self.detached_volume()

                res = self.cs.deleteVolume(id=volume['id'])
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    res = self.poll_job(res, 'volume')

        return volume


    def update_volume(self, volume):
        args_resize = {}
        args_resize['id'] = volume['id']
        args_resize['diskofferingid'] = self.get_disk_offering(key='id')
        args_resize['maxiops'] = self.module.params.get('max_iops')
        args_resize['miniops'] = self.module.params.get('min_iops')
        args_resize['size'] = self.module.params.get('size')

        # change unit from bytes to giga bytes to compare with args
        volume_copy = volume.copy()
        volume_copy['size'] = volume_copy['size'] / (2**30)

        if self.has_changed(args_resize, volume_copy):

            self.result['changed'] = True
            if not self.module.check_mode:
                args_resize['shrinkok'] = self.module.params.get('shrink_ok')
                res = self.cs.resizeVolume(**args_resize)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    volume = self.poll_job(res, 'volume')
                self.volume = volume

        return volume


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name = dict(required=True),
        disk_offering = dict(default=None),
        display_volume = dict(type='bool', default=None),
        max_iops = dict(type='int', default=None),
        min_iops = dict(type='int', default=None),
        size = dict(type='int', default=None),
        snapshot = dict(default=None),
        vm = dict(default=None),
        device_id = dict(type='int', default=None),
        custom_id = dict(default=None),
        force = dict(type='bool', default=False),
        shrink_ok = dict(type='bool', default=False),
        state = dict(choices=['present', 'absent', 'attached', 'detached'], default='present'),
        zone = dict(default=None),
        domain = dict(default=None),
        account = dict(default=None),
        project = dict(default=None),
        poll_async = dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        mutually_exclusive = (
            ['snapshot', 'disk_offering'],
        ),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_vol = AnsibleCloudStackVolume(module)

        state = module.params.get('state')

        if state in ['absent']:
            volume = acs_vol.absent_volume()
        elif state in ['attached']:
            volume = acs_vol.attached_volume()
        elif state in ['detached']:
            volume = acs_vol.detached_volume()
        else:
            volume = acs_vol.present_volume()

        result = acs_vol.get_result(volume)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
