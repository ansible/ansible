#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, David Passante <@dpassante>
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cs_disk_offering
description:
  - Create and delete disk offerings for guest VMs.
  - Update display_text or display_offering of existing disk offering.
short_description: Manages disk offerings on Apache CloudStack based clouds.
version_added: "2.7"
author:
  - "David Passante (@dpassante)"
  - "René Moser(@resmo)"
options:
  disk_size:
    description:
      - Size of the disk offering in GB (1GB = 1,073,741,824 bytes).
  bytes_read_rate:
    description:
      - Bytes read rate of the disk offering.
  bytes_write_rate:
    description:
      - Bytes write rate of the disk offering.
  display_text:
    description:
      - Display text of the disk offering.
      - If not set, C(name) will be used as C(display_text) while creating.
  domain:
    description:
      - Domain the disk offering is related to.
      - Public for all domains and subdomains if not set.
  hypervisor_snapshot_reserve:
    description:
      - Hypervisor snapshot reserve space as a percent of a volume.
      - Only for managed storage using Xen or VMware.
  customized:
    description:
      - Whether disk offering iops is custom or not.
    type: bool
    default: false
  iops_read_rate:
    description:
      - IO requests read rate of the disk offering.
  iops_write_rate:
    description:
      - IO requests write rate of the disk offering.
  iops_max:
    description:
      - Max. iops of the disk offering.
  iops_min:
    description:
      - Min. iops of the disk offering.
  name:
    description:
      - Name of the disk offering.
    required: true
  provisioning_type:
    description:
      - Provisioning type used to create volumes.
    choices:
      - thin
      - sparse
      - fat
  state:
    description:
      - State of the disk offering.
    choices:
      - present
      - absent
    default: present
  storage_type:
    description:
      - The storage type of the disk offering.
    choices:
      - local
      - shared
  storage_tags:
    description:
      - The storage tags for this disk offering.
    aliases:
      - storage_tag
  display_offering:
    description:
      - An optional field, whether to display the offering to the end user or not.
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a disk offering with local storage
  local_action:
    module: cs_disk_offering
    name: small
    display_text: Small 10GB
    disk_size: 10
    storage_type: local

- name: Create or update a disk offering with shared storage
  local_action:
    module: cs_disk_offering
    name: small
    display_text: Small 10GB
    disk_size: 10
    storage_type: shared
    storage_tags: SAN01

- name: Remove a disk offering
  local_action:
    module: cs_disk_offering
    name: small
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the disk offering
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
disk_size:
  description: Size of the disk offering in GB
  returned: success
  type: int
  sample: 10
iops_max:
  description: Max iops of the disk offering
  returned: success
  type: int
  sample: 1000
iops_min:
  description: Min iops of the disk offering
  returned: success
  type: int
  sample: 500
bytes_read_rate:
  description: Bytes read rate of the disk offering
  returned: success
  type: int
  sample: 1000
bytes_write_rate:
  description: Bytes write rate of the disk offering
  returned: success
  type: int
  sample: 1000
iops_read_rate:
  description: IO requests per second read rate of the disk offering
  returned: success
  type: int
  sample: 1000
iops_write_rate:
  description: IO requests per second write rate of the disk offering
  returned: success
  type: int
  sample: 1000
created:
  description: Date the offering was created
  returned: success
  type: string
  sample: 2017-11-19T10:48:59+0000
display_text:
  description: Display text of the offering
  returned: success
  type: string
  sample: Small 10GB
domain:
  description: Domain the offering is into
  returned: success
  type: string
  sample: ROOT
storage_tags:
  description: List of storage tags
  returned: success
  type: list
  sample: [ 'eco' ]
customized:
  description: Whether the offering uses custom IOPS or not
  returned: success
  type: bool
  sample: false
name:
  description: Name of the system offering
  returned: success
  type: string
  sample: Micro
provisioning_type:
  description: Provisioning type used to create volumes
  returned: success
  type: string
  sample: thin
storage_type:
  description: Storage type used to create volumes
  returned: success
  type: string
  sample: shared
display_offering:
  description: Whether to display the offering to the end user or not.
  returned: success
  type: bool
  sample: false
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackDiskOffering(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackDiskOffering, self).__init__(module)
        self.returns = {
            'disksize': 'disk_size',
            'diskBytesReadRate': 'bytes_read_rate',
            'diskBytesWriteRate': 'bytes_write_rate',
            'diskIopsReadRate': 'iops_read_rate',
            'diskIopsWriteRate': 'iops_write_rate',
            'maxiops': 'iops_max',
            'miniops': 'iops_min',
            'hypervisorsnapshotreserve': 'hypervisor_snapshot_reserve',
            'customized': 'customized',
            'provisioningtype': 'provisioning_type',
            'storagetype': 'storage_type',
            'tags': 'storage_tags',
            'displayoffering': 'display_offering',
        }

        self.disk_offering = None

    def get_disk_offering(self):
        args = {
            'name': self.module.params.get('name'),
            'domainid': self.get_domain(key='id'),
        }
        disk_offerings = self.query_api('listDiskOfferings', **args)
        if disk_offerings:
            for disk_offer in disk_offerings['diskoffering']:
                if args['name'] == disk_offer['name']:
                    self.disk_offering = disk_offer

        return self.disk_offering

    def present_disk_offering(self):
        disk_offering = self.get_disk_offering()
        if not disk_offering:
            disk_offering = self._create_offering(disk_offering)
        else:
            disk_offering = self._update_offering(disk_offering)

        return disk_offering

    def absent_disk_offering(self):
        disk_offering = self.get_disk_offering()
        if disk_offering:
            self.result['changed'] = True
            if not self.module.check_mode:
                args = {
                    'id': disk_offering['id'],
                }
                self.query_api('deleteDiskOffering', **args)
        return disk_offering

    def _create_offering(self, disk_offering):
        self.result['changed'] = True

        args = {
            'name': self.module.params.get('name'),
            'displaytext': self.get_or_fallback('display_text', 'name'),
            'disksize': self.module.params.get('disk_size'),
            'bytesreadrate': self.module.params.get('bytes_read_rate'),
            'byteswriterate': self.module.params.get('bytes_write_rate'),
            'customized': self.module.params.get('customized'),
            'domainid': self.get_domain(key='id'),
            'hypervisorsnapshotreserve': self.module.params.get('hypervisor_snapshot_reserve'),
            'iopsreadrate': self.module.params.get('iops_read_rate'),
            'iopswriterate': self.module.params.get('iops_write_rate'),
            'maxiops': self.module.params.get('iops_max'),
            'miniops': self.module.params.get('iops_min'),
            'provisioningtype': self.module.params.get('provisioning_type'),
            'diskofferingdetails': self.module.params.get('disk_offering_details'),
            'storagetype': self.module.params.get('storage_type'),
            'tags': self.module.params.get('storage_tags'),
            'displayoffering': self.module.params.get('display_offering'),
        }
        if not self.module.check_mode:
            res = self.query_api('createDiskOffering', **args)
            disk_offering = res['diskoffering']
        return disk_offering

    def _update_offering(self, disk_offering):
        args = {
            'id': disk_offering['id'],
            'name': self.module.params.get('name'),
            'displaytext': self.get_or_fallback('display_text', 'name'),
            'displayoffering': self.module.params.get('display_offering'),
        }
        if self.has_changed(args, disk_offering):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('updateDiskOffering', **args)
                disk_offering = res['diskoffering']
        return disk_offering

    def get_result(self, disk_offering):
        super(AnsibleCloudStackDiskOffering, self).get_result(disk_offering)
        if disk_offering:
            # Prevent confusion, the api returns a tags key for storage tags.
            if 'tags' in disk_offering:
                self.result['storage_tags'] = disk_offering['tags'].split(',') or [disk_offering['tags']]
            if 'tags' in self.result:
                del self.result['tags']

        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        display_text=dict(),
        domain=dict(),
        disk_size=dict(type='int'),
        display_offering=dict(type='bool'),
        hypervisor_snapshot_reserve=dict(type='int'),
        bytes_read_rate=dict(type='int'),
        bytes_write_rate=dict(type='int'),
        customized=dict(type='bool'),
        iops_read_rate=dict(type='int'),
        iops_write_rate=dict(type='int'),
        iops_max=dict(type='int'),
        iops_min=dict(type='int'),
        provisioning_type=dict(choices=['thin', 'sparse', 'fat']),
        storage_type=dict(choices=['local', 'shared']),
        storage_tags=dict(type='list', aliases=['storage_tag']),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_do = AnsibleCloudStackDiskOffering(module)

    state = module.params.get('state')
    if state == "absent":
        disk_offering = acs_do.absent_disk_offering()
    else:
        disk_offering = acs_do.present_disk_offering()

    result = acs_do.get_result(disk_offering)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
