#!/usr/bin/python
# Copyright (c) 2016 Hewlett-Packard Enterprise Corporation
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


try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_keystone_domain_facts
short_description: Retrieve facts about one or more OpenStack domains
extends_documentation_fragment: openstack
version_added: "2.1"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
description:
    - Retrieve facts about a one or more OpenStack domains
requirements:
    - "python >= 2.6"
    - "shade"
options:
   name:
     description:
        - Name or ID of the domain
     required: true
   filters:
     description:
        - A dictionary of meta data to use for further filtering.  Elements of
          this dictionary may be additional dictionaries.
     required: false
     default: None
'''

EXAMPLES = '''
# Gather facts about previously created domain
- os_keystone_domain_facts:
    cloud: awesomecloud
- debug: var=openstack_domains

# Gather facts about a previously created domain by name
- os_keystone_domain_facts:
    cloud: awesomecloud
    name: demodomain
- debug: var=openstack_domains

# Gather facts about a previously created domain with filter
- os_keystone_domain_facts
    cloud: awesomecloud
    name: demodomain
    filters:
      enabled: False
- debug: var=openstack_domains
'''


RETURN = '''
openstack_domains:
    description: has all the OpenStack facts about domains
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: string
        name:
            description: Name given to the domain.
            returned: success
            type: string
        description:
            description: Description of the domain.
            returned: success
            type: string
        enabled:
            description: Flag to indicate if the domain is enabled.
            returned: success
            type: bool
'''

def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None),
        filters=dict(required=False, type='dict', default=None),
    )
    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[
            ['name', 'filters'],
        ]
    )
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        name = module.params['name']
        filters = module.params['filters']

        opcloud = shade.operator_cloud(**module.params)

        if name:
            # Let's suppose user is passing domain ID
            try:
                domains = cloud.get_domain(name)
            except:
                domains = opcloud.search_domains(filters={'name': name})

        else:
            domains = opcloud.search_domains(filters)

        module.exit_json(changed=False, ansible_facts=dict(
            openstack_domains=domains))

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
