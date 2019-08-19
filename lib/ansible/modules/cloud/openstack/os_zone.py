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
module: os_zone
short_description: Manage OpenStack DNS zones
extends_documentation_fragment: openstack
version_added: "2.2"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
description:
    - Manage OpenStack DNS zones. Zones can be created, deleted or
      updated. Only the I(email), I(description), I(ttl) and I(masters) values
      can be updated.
options:
   name:
     description:
        - Zone name
     required: true
   zone_type:
     description:
        - Zone type
     choices: [primary, secondary]
   email:
     description:
        - Email of the zone owner (only applies if zone_type is primary)
   description:
     description:
        - Zone description
   ttl:
     description:
        -  TTL (Time To Live) value in seconds
   masters:
     description:
        - Master nameservers (only applies if zone_type is secondary)
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
# Create a zone named "example.net"
- os_zone:
    cloud: mycloud
    state: present
    name: example.net.
    zone_type: primary
    email: test@example.net
    description: Test zone
    ttl: 3600

# Update the TTL on existing "example.net." zone
- os_zone:
    cloud: mycloud
    state: present
    name: example.net.
    ttl: 7200

# Delete zone named "example.net."
- os_zone:
    cloud: mycloud
    state: absent
    name: example.net.
'''

RETURN = '''
zone:
    description: Dictionary describing the zone.
    returned: On success when I(state) is 'present'.
    type: complex
    contains:
        id:
            description: Unique zone ID
            type: str
            sample: "c1c530a3-3619-46f3-b0f6-236927b2618c"
        name:
            description: Zone name
            type: str
            sample: "example.net."
        type:
            description: Zone type
            type: str
            sample: "PRIMARY"
        email:
            description: Zone owner email
            type: str
            sample: "test@example.net"
        description:
            description: Zone description
            type: str
            sample: "Test description"
        ttl:
            description: Zone TTL value
            type: int
            sample: 3600
        masters:
            description: Zone master nameservers
            type: list
            sample: []
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _system_state_change(state, email, description, ttl, masters, zone):
    if state == 'present':
        if not zone:
            return True
        if email is not None and zone.email != email:
            return True
        if description is not None and zone.description != description:
            return True
        if ttl is not None and zone.ttl != ttl:
            return True
        if masters is not None and zone.masters != masters:
            return True
    if state == 'absent' and zone:
        return True
    return False


def _wait(timeout, cloud, zone, state, module, sdk):
    """Wait for a zone to reach the desired state for the given state."""

    for count in sdk.utils.iterate_timeout(
            timeout,
            "Timeout waiting for zone to be %s" % state):

        if (state == 'absent' and zone is None) or (state == 'present' and zone and zone.status == 'ACTIVE'):
            return

        try:
            zone = cloud.get_zone(zone.id)
        except Exception:
            continue

        if zone and zone.status == 'ERROR':
            module.fail_json(msg="Zone reached ERROR state while waiting for it to be %s" % state)


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        zone_type=dict(required=False, choice=['primary', 'secondary']),
        email=dict(required=False, default=None),
        description=dict(required=False, default=None),
        ttl=dict(required=False, default=None, type='int'),
        masters=dict(required=False, default=None, type='list'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    name = module.params.get('name')
    state = module.params.get('state')
    wait = module.params.get('wait')
    timeout = module.params.get('timeout')

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        zone = cloud.get_zone(name)

        if state == 'present':
            zone_type = module.params.get('zone_type')
            email = module.params.get('email')
            description = module.params.get('description')
            ttl = module.params.get('ttl')
            masters = module.params.get('masters')

            if module.check_mode:
                module.exit_json(changed=_system_state_change(state, email,
                                                              description, ttl,
                                                              masters, zone))

            if zone is None:
                zone = cloud.create_zone(
                    name=name, zone_type=zone_type, email=email,
                    description=description, ttl=ttl, masters=masters)
                changed = True
            else:
                if masters is None:
                    masters = []

                pre_update_zone = zone
                changed = _system_state_change(state, email,
                                               description, ttl,
                                               masters, pre_update_zone)
                if changed:
                    zone = cloud.update_zone(
                        name, email=email,
                        description=description,
                        ttl=ttl, masters=masters)

            if wait:
                _wait(timeout, cloud, zone, state, module, sdk)

            module.exit_json(changed=changed, zone=zone)

        elif state == 'absent':
            if module.check_mode:
                module.exit_json(changed=_system_state_change(state, None,
                                                              None, None,
                                                              None, zone))

            if zone is None:
                changed = False
            else:
                cloud.delete_zone(name)
                changed = True

            if wait:
                _wait(timeout, cloud, zone, state, module, sdk)

            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
