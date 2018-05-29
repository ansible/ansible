#!/usr/bin/python
# Copyright (c) 2016 Hewlett-Packard Enterprise
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
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
   ttl:
     description:
        -  TTL (Time To Live) value in seconds
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements:
    - "python >= 2.7"
    - "openstacksdk"
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


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

    zone = module.params.get('zone')
    name = module.params.get('name')
    state = module.params.get('state')

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        recordset_type = module.params.get('recordset_type')
        recordset_filter = {'type': recordset_type}

        recordsets = cloud.search_recordsets(zone, name_or_id=name + '.' + zone, filters=recordset_filter)

        if len(recordsets) == 1:
            recordset = recordsets[0]
            try:
                recordset_id = recordset['id']
            except KeyError as e:
                module.fail_json(msg=str(e))
        else:
            # recordsets is filtered by type and should never be more than 1 return
            recordset = None

        if state == 'present':
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
                        zone, recordset_id,
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
                changed = False
            else:
                cloud.delete_recordset(zone, recordset_id)
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
