#!/usr/bin/python

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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
    from shade import meta
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_server_facts
short_description: Retrieve facts about a compute instance
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
   - Retrieve facts about a server instance from OpenStack.
notes:
   - Facts are placed in the C(openstack) variable.
options:
   server:
     description:
        - Name or ID of the instance
     required: true
requirements: ["shade"]
'''

EXAMPLES = '''
# Gather facts about a previously created server named vm1
- os_server_facts:
    cloud: rax-dfw
    server: vm1
- debug: var=openstack
'''

def main():

    argument_spec = openstack_full_argument_spec(
        server=dict(required=True),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud(**module.params)
        server = cloud.get_server(module.params['server'])
        hostvars = dict(openstack=meta.get_hostvars_from_server(
            cloud, server))
        module.exit_json(changed=False, ansible_facts=hostvars)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()

