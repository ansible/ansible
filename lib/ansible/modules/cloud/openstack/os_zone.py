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
     default: None
   email:
     description:
        - Email of the zone owner (only applies if zone_type is primary)
     required: false
   description:
     description:
        - Zone description
     required: false
     default: None
   ttl:
     description:
        -  TTL (Time To Live) value in seconds
     required: false
     default: None
   masters:
     description:
        - Master nameservers (only applies if zone_type is secondary)
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
            type: string
            sample: "c1c530a3-3619-46f3-b0f6-236927b2618c"
        name:
            description: Zone name
            type: string
            sample: "example.net."
        type:
            description: Zone type
            type: string
            sample: "PRIMARY"
        email:
            description: Zone owner email
            type: string
            sample: "test@example.net"
        description:
            description: Zone description
            type: string
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

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion


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

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')
    if StrictVersion(shade.__version__) < StrictVersion('1.8.0'):
        module.fail_json(msg="To utilize this module, the installed version of"
                             "the shade library MUST be >=1.8.0")

    name = module.params.get('name')
    state = module.params.get('state')

    try:
        cloud = shade.openstack_cloud(**module.params)
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
            module.exit_json(changed=changed, zone=zone)

        elif state == 'absent':
            if module.check_mode:
                module.exit_json(changed=_system_state_change(state, None,
                                                              None, None,
                                                              None, zone))

            if zone is None:
                changed=False
            else:
                cloud.delete_zone(name)
                changed=True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
