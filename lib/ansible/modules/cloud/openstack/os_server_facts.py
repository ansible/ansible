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
   host:
     description:
       - restrict results to servers host on a specific host.
   detailed:
    version_added: "2.8"
     description:
        - when true, return additional detail about servers at the expense
          of additional API calls.
     type: bool
     default: 'no'
   all_tenants:
     version_added: "2.8"
     description:
        - when true, return VMs from all projects
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

# Gather facts of servers on a specific compute node
- os_server_facts:
    cloud: sjc1
    all_tenants: true
    host: kvm482
- debug:
    var: openstack_servers
'''

import fnmatch

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        server=dict(required=False),
        host=dict(required=False),
        detailed=dict(required=False, type='bool'),
        all_tenants=dict(required=False, type='bool'),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        query = {'details': module.params['detailed']}
        if module.params['host']:
            query['host'] = module.params['host']
        if module.params['all_tenants']:
            query['all_tenants'] = module.params['all_tenants']

        openstack_servers = cloud.compute.servers(**query)

        if module.params['server']:
            # filter servers by name
            pattern = module.params['server']
            # TODO(mordred) This is handled by sdk now
            openstack_servers = [server for server in openstack_servers
                                 if fnmatch.fnmatch(server['name'], pattern) or fnmatch.fnmatch(server['id'], pattern)]

        # Normalize to dicts
        openstack_servers = [s.to_dict() for s in openstack_servers]

        module.exit_json(changed=False, ansible_facts=dict(
            openstack_servers=openstack_servers))

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
