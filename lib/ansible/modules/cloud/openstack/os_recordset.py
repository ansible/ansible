#!/usr/bin/python
# Copyright (c) 2016 Hewlett-Packard Enterprise
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_recordset
short_description: Manage OpenStack DNS recordsets
extends_documentation_fragment: openstack
version_added: "2.2"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
description:
    - Manage OpenStack DNS recordsets. Recordsets can be created, deleted or
      updated. Only the I(records), I(description), and I(ttl) values
      can be updated.
options:
   zone:
     description:
        - Zone managing the recordset
     required: true
   name:
     description:
        - Name of the recordset
     required: true
   recordset_type:
     description:
        - Recordset type
     required: true
   records:
     description:
        - List of recordset definitions
     required: true
   description:
     description:
        - Description of the recordset
     required: false
     default: None
   ttl:
     description:
        -  TTL (Time To Live) value in seconds
     required: false
     default: None
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Create a recordset named "www.example.net."
- os_recordset:
    cloud: mycloud
    state: present
    zone: example.net.
    name: www
    recordset_type: primary
    records: ['10.1.1.1']
    description: test recordset
    ttl: 3600

# Update the TTL on existing "www.example.net." recordset
- os_recordset:
    cloud: mycloud
    state: present
    zone: example.net.
    name: www
    ttl: 7200

# Delete recorset named "www.example.net."
- os_recordset:
    cloud: mycloud
    state: absent
    zone: example.net.
    name: www
'''

RETURN = '''
recordset:
    description: Dictionary describing the recordset.
    returned: On success when I(state) is 'present'.
    type: complex
    contains:
        id:
            description: Unique recordset ID
            type: string
            sample: "c1c530a3-3619-46f3-b0f6-236927b2618c"
        name:
            description: Recordset name
            type: string
            sample: "www.example.net."
        zone_id:
            description: Zone id
            type: string
            sample: 9508e177-41d8-434e-962c-6fe6ca880af7
        type:
            description: Recordset type
            type: string
            sample: "A"
        description:
            description: Recordset description
            type: string
            sample: "Test description"
        ttl:
            description: Zone TTL value
            type: int
            sample: 3600
        records:
            description: Recordset records
            type: list
            sample: ['10.0.0.1']
'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion


def _system_state_change(state, records, description, ttl, zone, recordset):
    if state == 'present':
        if recordset is None:
            return True
        if records is not None and recordset.records != records:
            return True
        if description is not None and recordset.description != description:
            return True
        if ttl is not None and recordset.ttl != ttl:
            return True
    if state == 'absent' and recordset:
        return True
    return False

def main():
    argument_spec = openstack_full_argument_spec(
        zone=dict(required=True),
        name=dict(required=True),
        recordset_type=dict(required=False),
        records=dict(required=False, type='list'),
        description=dict(required=False, default=None),
        ttl=dict(required=False, default=None, type='int'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           required_if=[
                               ('state', 'present',
                                ['recordset_type', 'records'])],
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')
    if StrictVersion(shade.__version__) <= StrictVersion('1.8.0'):
        module.fail_json(msg="To utilize this module, the installed version of "
                             "the shade library MUST be >1.8.0")

    zone = module.params.get('zone')
    name = module.params.get('name')
    state = module.params.get('state')

    try:
        cloud = shade.openstack_cloud(**module.params)
        recordset = cloud.get_recordset(zone, name + '.' + zone)


        if state == 'present':
            recordset_type = module.params.get('recordset_type')
            records = module.params.get('records')
            description = module.params.get('description')
            ttl = module.params.get('ttl')

            if module.check_mode:
                module.exit_json(changed=_system_state_change(state,
                                                              records, description,
                                                              ttl, zone,
                                                              recordset))

            if recordset is None:
                recordset = cloud.create_recordset(
                    zone=zone, name=name, recordset_type=recordset_type,
                    records=records, description=description, ttl=ttl)
                changed = True
            else:
                if records is None:
                    records = []

                pre_update_recordset = recordset
                changed = _system_state_change(state, records,
                                               description, ttl,
                                               zone, pre_update_recordset)
                if changed:
                    zone = cloud.update_recordset(
                        zone, name + '.' + zone,
                        records=records,
                        description=description,
                        ttl=ttl)
            module.exit_json(changed=changed, recordset=recordset)

        elif state == 'absent':
            if module.check_mode:
                module.exit_json(changed=_system_state_change(state,
                                                              None, None,
                                                              None,
                                                              None, recordset))

            if recordset is None:
                changed=False
            else:
                cloud.delete_recordset(zone, name + '.' + zone)
                changed=True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
