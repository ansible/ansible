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
module: os_server_info
short_description: Retrieve information about one or more compute instances
author: Monty (@emonty)
version_added: "2.0"
description:
    - Retrieve information about server instances from OpenStack.
    - This module was called C(os_server_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(os_server_info) module no longer returns C(ansible_facts)!
notes:
    - The result contains a list of servers.
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
   filters:
     description:
        - restrict results to servers matching a dictionary of
          filters
     version_added: "2.8"
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
   all_projects:
     description:
       - Whether to list servers from all projects or just the current auth
         scoped project.
     type: bool
     default: 'no'
     version_added: "2.8"
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather information about all servers named <web*> that are in an active state:
- os_server_info:
    cloud: rax-dfw
    server: web*
    filters:
      vm_state: active
  register: result
- debug:
    msg: "{{ result.openstack_servers }}"
'''

import fnmatch

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        server=dict(required=False),
        detailed=dict(required=False, type='bool', default=False),
        filters=dict(required=False, type='dict', default=None),
        all_projects=dict(required=False, type='bool', default=False),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)
    is_old_facts = module._name == 'os_server_facts'
    if is_old_facts:
        module.deprecate("The 'os_server_facts' module has been renamed to 'os_server_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        openstack_servers = cloud.search_servers(
            detailed=module.params['detailed'], filters=module.params['filters'],
            all_projects=module.params['all_projects'])

        if module.params['server']:
            # filter servers by name
            pattern = module.params['server']
            # TODO(mordred) This is handled by sdk now
            openstack_servers = [server for server in openstack_servers
                                 if fnmatch.fnmatch(server['name'], pattern) or fnmatch.fnmatch(server['id'], pattern)]
        if is_old_facts:
            module.exit_json(changed=False, ansible_facts=dict(
                openstack_servers=openstack_servers))
        else:
            module.exit_json(changed=False, openstack_servers=openstack_servers)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
