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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_server_facts
short_description: Retrieve facts about one or more compute instances
author: Monty
version_added: "2.0"
description:
    - Retrieve facts about server instances from OpenStack.
notes:
    - This module creates a new top-level C(openstack_servers) fact, which
      contains a list of servers.
requirements:
    - "python >= 2.6"
    - "shade"
options:
   server:
     description:
       - restrict results to servers with names or UUID matching
         this glob expression (e.g., C<web*>).
     required: false
     default: None
   detailed:
     description:
        - when true, return additional detail about servers at the expense
          of additional API calls.
     required: false
     default: false
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather facts about all servers named C<web*>:
- os_server_facts:
    cloud: rax-dfw
    server: web*
- debug:
    var: openstack_servers
'''

import fnmatch

try:
    import shade
    from shade import meta
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def main():

    argument_spec = openstack_full_argument_spec(
        server=dict(required=False),
        detailed=dict(required=False, type='bool'),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud(**module.params)
        openstack_servers = cloud.list_servers(
            detailed=module.params['detailed'])

        if module.params['server']:
            # filter servers by name
            pattern = module.params['server']
            openstack_servers = [server for server in openstack_servers
                                 if fnmatch.fnmatch(server['name'], pattern) or fnmatch.fnmatch(server['id'], pattern)]
        module.exit_json(changed=False, ansible_facts=dict(
            openstack_servers=openstack_servers))

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
