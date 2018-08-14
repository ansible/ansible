#!/usr/bin/python

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
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
    - "python >= 2.7"
    - "openstacksdk"
options:
   server:
     description:
       - restrict results to servers with names or UUID matching
         this glob expression (e.g., <web*>).
   detailed:
     description:
        - when true, return additional detail about servers at the expense
          of additional API calls.
     type: bool
     default: 'no'
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather facts about all servers named <web*>:
- os_server_facts:
    cloud: rax-dfw
    server: web*
- debug:
    var: openstack_servers
'''

import fnmatch

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        server=dict(required=False),
        detailed=dict(required=False, type='bool'),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        openstack_servers = cloud.list_servers(
            detailed=module.params['detailed'])

        if module.params['server']:
            # filter servers by name
            pattern = module.params['server']
            # TODO(mordred) This is handled by sdk now
            openstack_servers = [server for server in openstack_servers
                                 if fnmatch.fnmatch(server['name'], pattern) or fnmatch.fnmatch(server['id'], pattern)]
        module.exit_json(changed=False, ansible_facts=dict(
            openstack_servers=openstack_servers))

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
