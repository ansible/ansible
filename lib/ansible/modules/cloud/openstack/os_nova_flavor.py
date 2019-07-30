#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_nova_flavor
short_description: Manage OpenStack compute flavors
extends_documentation_fragment: openstack
version_added: "2.0"
author: "David Shrewsbury (@Shrews)"
description:
   - Add or remove flavors from OpenStack.
options:
   state:
     description:
        - Indicate desired state of the resource. When I(state) is 'present',
          then I(ram), I(vcpus), and I(disk) are all required. There are no
          default values for those parameters.
     choices: ['present', 'absent']
     default: present
   name:
     description:
        - Flavor name.
     required: true
   ram:
     description:
        - Amount of memory, in MB.
   vcpus:
     description:
        - Number of virtual CPUs.
   disk:
     description:
        - Size of local disk, in GB.
   ephemeral:
     description:
        - Ephemeral space size, in GB.
     default: 0
   swap:
     description:
        - Swap space size, in MB.
     default: 0
   rxtx_factor:
     description:
        - RX/TX factor.
     default: 1.0
   is_public:
     description:
        - Make flavor accessible to the public.
     type: bool
     default: 'yes'
   flavorid:
     description:
        - ID for the flavor. This is optional as a unique UUID will be
          assigned if a value is not specified.
     default: "auto"
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
   extra_specs:
     description:
        - Metadata dictionary
     version_added: "2.3"
requirements: ["openstacksdk"]
'''

EXAMPLES = '''
- name: "Create 'tiny' flavor with 1024MB of RAM, 1 virtual CPU, and 10GB of local disk, and 10GB of ephemeral."
  os_nova_flavor:
    cloud: mycloud
    state: present
    name: tiny
    ram: 1024
    vcpus: 1
    disk: 10
    ephemeral: 10

- name: "Delete 'tiny' flavor"
  os_nova_flavor:
    cloud: mycloud
    state: absent
    name: tiny

- name: Create flavor with metadata
  os_nova_flavor:
    cloud: mycloud
    state: present
    name: tiny
    ram: 1024
    vcpus: 1
    disk: 10
    extra_specs:
      "quota:disk_read_iops_sec": 5000
      "aggregate_instance_extra_specs:pinned": false
'''

RETURN = '''
flavor:
    description: Dictionary describing the flavor.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: Flavor ID.
            returned: success
            type: str
            sample: "515256b8-7027-4d73-aa54-4e30a4a4a339"
        name:
            description: Flavor name.
            returned: success
            type: str
            sample: "tiny"
        disk:
            description: Size of local disk, in GB.
            returned: success
            type: int
            sample: 10
        ephemeral:
            description: Ephemeral space size, in GB.
            returned: success
            type: int
            sample: 10
        ram:
            description: Amount of memory, in MB.
            returned: success
            type: int
            sample: 1024
        swap:
            description: Swap space size, in MB.
            returned: success
            type: int
            sample: 100
        vcpus:
            description: Number of virtual CPUs.
            returned: success
            type: int
            sample: 2
        is_public:
            description: Make flavor accessible to the public.
            returned: success
            type: bool
            sample: true
        extra_specs:
            description: Flavor metadata
            returned: success
            type: dict
            sample:
                "quota:disk_read_iops_sec": 5000
                "aggregate_instance_extra_specs:pinned": false
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _system_state_change(module, flavor):
    state = module.params['state']
    if state == 'present' and not flavor:
        return True
    if state == 'absent' and flavor:
        return True
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        state=dict(required=False, default='present',
                   choices=['absent', 'present']),
        name=dict(required=False),

        # required when state is 'present'
        ram=dict(required=False, type='int'),
        vcpus=dict(required=False, type='int'),
        disk=dict(required=False, type='int'),

        ephemeral=dict(required=False, default=0, type='int'),
        swap=dict(required=False, default=0, type='int'),
        rxtx_factor=dict(required=False, default=1.0, type='float'),
        is_public=dict(required=False, default=True, type='bool'),
        flavorid=dict(required=False, default="auto"),
        extra_specs=dict(required=False, default=None, type='dict'),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['ram', 'vcpus', 'disk'])
        ],
        **module_kwargs)

    state = module.params['state']
    name = module.params['name']
    extra_specs = module.params['extra_specs'] or {}

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        flavor = cloud.get_flavor(name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, flavor))

        if state == 'present':
            old_extra_specs = {}
            require_update = False

            if flavor:
                old_extra_specs = flavor['extra_specs']
                for param_key in ['ram', 'vcpus', 'disk', 'ephemeral', 'swap', 'rxtx_factor', 'is_public']:
                    if module.params[param_key] != flavor[param_key]:
                        require_update = True
                        break

            if flavor and require_update:
                cloud.delete_flavor(name)
                flavor = None

            if not flavor:
                flavor = cloud.create_flavor(
                    name=name,
                    ram=module.params['ram'],
                    vcpus=module.params['vcpus'],
                    disk=module.params['disk'],
                    flavorid=module.params['flavorid'],
                    ephemeral=module.params['ephemeral'],
                    swap=module.params['swap'],
                    rxtx_factor=module.params['rxtx_factor'],
                    is_public=module.params['is_public']
                )
                changed = True
            else:
                changed = False

            new_extra_specs = dict([(k, str(v)) for k, v in extra_specs.items()])
            unset_keys = set(old_extra_specs.keys()) - set(extra_specs.keys())

            if unset_keys and not require_update:
                cloud.unset_flavor_specs(flavor['id'], unset_keys)

            if old_extra_specs != new_extra_specs:
                cloud.set_flavor_specs(flavor['id'], extra_specs)

            changed = (changed or old_extra_specs != new_extra_specs)

            module.exit_json(changed=changed,
                             flavor=flavor,
                             id=flavor['id'])

        elif state == 'absent':
            if flavor:
                cloud.delete_flavor(name)
                module.exit_json(changed=True)
            module.exit_json(changed=False)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
