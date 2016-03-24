#!/usr/bin/python

# Copyright (c) 2015 IBM
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

import re

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion


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
    - "python >= 2.6"
    - "shade"
options:
   name:
     description:
       - A flavor name. Cannot be used with I(ram) or I(vcpus).
     required: false
     default: None
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
     required: false
     default: false
   vcpus:
     description:
       - A string used for filtering flavors based on the number of virtual
         CPUs desired. Format is the same as the I(ram) parameter.
     required: false
     default: false
   limit:
     description:
       - Limits the number of flavors returned. All matching flavors are
         returned by default.
     required: false
     default: None
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
'''


RETURN = '''
openstack_flavors:
    description: Dictionary describing the flavors.
    returned: On success.
    type: dictionary
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


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None),
        ram=dict(required=False, default=None),
        vcpus=dict(required=False, default=None),
        limit=dict(required=False, default=None, type='int'),
    )
    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[
            ['name', 'ram'],
            ['name', 'vcpus'],
        ]
    )
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']
    vcpus = module.params['vcpus']
    ram = module.params['ram']
    limit = module.params['limit']

    try:
        cloud = shade.openstack_cloud(**module.params)
        if name:
            flavors = cloud.search_flavors(filters={'name': name})

        else:
            flavors = cloud.list_flavors()
            filters = {}
            if vcpus:
                filters['vcpus'] = vcpus
            if ram:
                filters['ram'] = ram
            if filters:
                # Range search added in 1.5.0
                if StrictVersion(shade.__version__) < StrictVersion('1.5.0'):
                    module.fail_json(msg="Shade >= 1.5.0 needed for this functionality")
                flavors = cloud.range_search(flavors, filters)

        if limit is not None:
            flavors = flavors[:limit]

        module.exit_json(changed=False,
                         ansible_facts=dict(openstack_flavors=flavors))

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
