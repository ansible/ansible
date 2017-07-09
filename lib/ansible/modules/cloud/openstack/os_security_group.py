#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
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
module: os_security_group
short_description: Add/Delete security groups from an OpenStack cloud.
extends_documentation_fragment: openstack
author: "Monty Taylor (@emonty)"
version_added: "2.0"
description:
   - Add or Remove security groups from an OpenStack cloud.
options:
   name:
     description:
        - Name that has to be given to the security group. This module
          requires that security group names be unique.
     required: true
   description:
     description:
        - Long description of the purpose of the security group
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
'''

EXAMPLES = '''
# Create a security group
- os_security_group:
    cloud: mordred
    state: present
    name: foo
    description: security group for foo servers

# Update the existing 'foo' security group description
- os_security_group:
    cloud: mordred
    state: present
    name: foo
    description: updated description for the foo security group
'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def _needs_update(module, secgroup):
    """Check for differences in the updatable values.

    NOTE: We don't currently allow name updates.
    """
    if secgroup['description'] != module.params['description']:
        return True
    return False


def _system_state_change(module, secgroup):
    state = module.params['state']
    if state == 'present':
        if not secgroup:
            return True
        return _needs_update(module, secgroup)
    if state == 'absent' and secgroup:
        return True
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        description=dict(default=''),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']
    state = module.params['state']
    description = module.params['description']

    try:
        cloud = shade.openstack_cloud(**module.params)
        secgroup = cloud.get_security_group(name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, secgroup))

        changed = False
        if state == 'present':
            if not secgroup:
                secgroup = cloud.create_security_group(name, description)
                changed = True
            else:
                if _needs_update(module, secgroup):
                    secgroup = cloud.update_security_group(
                        secgroup['id'], description=description)
                    changed = True
            module.exit_json(
                changed=changed, id=secgroup['id'], secgroup=secgroup)

        if state == 'absent':
            if secgroup:
                cloud.delete_security_group(secgroup['id'])
                changed = True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == "__main__":
    main()
