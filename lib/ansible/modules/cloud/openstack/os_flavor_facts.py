#!/usr/bin/python

# Copyright (c) 2015 IBM
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: os_flavor_facts
short_description: Retrieve facts about one or more flavors
author: "David Shrewsbury (@Shrews)"
version_added: "2.1"
description:
    - Retrieve facts about available OpenStack instance flavors. By default,
      facts about ALL flavors are retrieved. Filters can be applied to get
      facts for only matching flavors. For example, you can filter on the
      amount of RAM available to the flavor, or the number of virtual CPUs
      available to the flavor, or both. When specifying multiple filters,
      *ALL* filters must match on a flavor before that flavor is returned as
      a fact.
notes:
    - This module creates a new top-level C(openstack_flavors) fact, which
      contains a list of unsorted flavors.
requirements:
    - "python >= 2.7"
    - "openstacksdk"
options:
   name:
     description:
       - A flavor name. Cannot be used with I(ram) or I(vcpus) or I(ephemeral).
   ram:
     description:
       - "A string used for filtering flavors based on the amount of RAM
         (in MB) desired. This string accepts the following special values:
         'MIN' (return flavors with the minimum amount of RAM), and 'MAX'
         (return flavors with the maximum amount of RAM)."

       - "A specific amount of RAM may also be specified. Any flavors with this
         exact amount of RAM will be returned."

       - "A range of acceptable RAM may be given using a special syntax. Simply
         prefix the amount of RAM with one of these acceptable range values:
         '<', '>', '<=', '>='. These values represent less than, greater than,
         less than or equal to, and greater than or equal to, respectively."
     type: bool
     default: 'no'
   vcpus:
     description:
       - A string used for filtering flavors based on the number of virtual
         CPUs desired. Format is the same as the I(ram) parameter.
     type: bool
     default: 'no'
   limit:
     description:
       - Limits the number of flavors returned. All matching flavors are
         returned by default.
   ephemeral:
     description:
       - A string used for filtering flavors based on the amount of ephemeral
         storage. Format is the same as the I(ram) parameter
     type: bool
     default: 'no'
     version_added: "2.3"
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather facts about all available flavors
- os_flavor_facts:
    cloud: mycloud

# Gather facts for the flavor named "xlarge-flavor"
- os_flavor_facts:
    cloud: mycloud
    name: "xlarge-flavor"

# Get all flavors that have exactly 512 MB of RAM.
- os_flavor_facts:
    cloud: mycloud
    ram: "512"

# Get all flavors that have 1024 MB or more of RAM.
- os_flavor_facts:
    cloud: mycloud
    ram: ">=1024"

# Get a single flavor that has the minimum amount of RAM. Using the 'limit'
# option will guarantee only a single flavor is returned.
- os_flavor_facts:
    cloud: mycloud
    ram: "MIN"
    limit: 1

# Get all flavors with 1024 MB of RAM or more, AND exactly 2 virtual CPUs.
- os_flavor_facts:
    cloud: mycloud
    ram: ">=1024"
    vcpus: "2"

# Get all flavors with 1024 MB of RAM or more, exactly 2 virtual CPUs, and
# less than 30gb of ephemeral storage.
- os_flavor_facts:
    cloud: mycloud
    ram: ">=1024"
    vcpus: "2"
    ephemeral: "<30"
'''


RETURN = '''
openstack_flavors:
    description: Dictionary describing the flavors.
    returned: On success.
    type: complex
    contains:
        id:
            description: Flavor ID.
            returned: success
            type: string
            sample: "515256b8-7027-4d73-aa54-4e30a4a4a339"
        name:
            description: Flavor name.
            returned: success
            type: string
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
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None),
        ram=dict(required=False, default=None),
        vcpus=dict(required=False, default=None),
        limit=dict(required=False, default=None, type='int'),
        ephemeral=dict(required=False, default=None),
    )
    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[
            ['name', 'ram'],
            ['name', 'vcpus'],
            ['name', 'ephemeral']
        ]
    )
    module = AnsibleModule(argument_spec, **module_kwargs)

    name = module.params['name']
    vcpus = module.params['vcpus']
    ram = module.params['ram']
    ephemeral = module.params['ephemeral']
    limit = module.params['limit']

    filters = {}
    if vcpus:
        filters['vcpus'] = vcpus
    if ram:
        filters['ram'] = ram
    if ephemeral:
        filters['ephemeral'] = ephemeral

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if name:
            flavors = cloud.search_flavors(filters={'name': name})

        else:
            flavors = cloud.list_flavors()
            if filters:
                flavors = cloud.range_search(flavors, filters)

        if limit is not None:
            flavors = flavors[:limit]

        module.exit_json(changed=False,
                         ansible_facts=dict(openstack_flavors=flavors))

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
