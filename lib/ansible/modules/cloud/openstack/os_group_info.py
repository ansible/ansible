#!/usr/bin/python

# Copyright (c) 2019, Phillipe Smith <phillipelnx@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_group_info
short_description: Retrieve info about one or more OpenStack groups
extends_documentation_fragment: openstack
version_added: "2.9"
author: "Phillipe Smith (@phsmith)"
description:
    - Retrieve info about a one or more OpenStack groups.
requirements:
    - "python >= 2.7"
    - "openstacksdk"
options:
   name:
     description:
        - Name or ID of the group.
     required: true
     type: str
   domain:
     description:
        - Name or ID of the domain containing the group if the cloud supports domains
     type: str
   filters:
     description:
        - A dictionary of meta data to use for further filtering.  Elements of
          this dictionary may be additional dictionaries.
     type: dict
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     type: str
'''

EXAMPLES = '''
# Gather info about previously created groups
- os_group_info:
    cloud: awesomecloud
  register: openstack_groups
- debug:
    var: openstack_groups

# Gather info about a previously created group by name
- os_group_info:
    cloud: awesomecloud
    name: demogroup
  register: openstack_groups
- debug:
    var: openstack_groups

# Gather info about a previously created group in a specific domain
- os_group_info:
    cloud: awesomecloud
    name: demogroup
    domain: admindomain
  register: openstack_groups
- debug:
    var: openstack_groups

# Gather info about a previously created group in a specific domain with filter
- os_group_info:
    cloud: awesomecloud
    name: demogroup
    domain: admindomain
    filters:
      enabled: False
  register: openstack_groups
- debug:
    var: openstack_groups
'''


RETURN = '''
openstack_groups:
    description: Dictionary describing all the matching groups.
    returned: always, but can be null
    type: complex
    contains:
        name:
            description: Name given to the group.
            returned: success
            type: str
        description:
            description: Description of the group.
            returned: success
            type: str
        id:
            description: Unique UUID.
            returned: success
            type: str
        domain_id:
            description: Domain ID containing the group (keystone v3 clouds only)
            returned: success
            type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None),
        domain=dict(required=False, default=None),
        filters=dict(required=False, type='dict', default=None),
    )

    module = AnsibleModule(argument_spec)

    sdk, opcloud = openstack_cloud_from_module(module)
    try:
        name = module.params['name']
        domain = module.params['domain']
        filters = module.params['filters']

        if domain:
            try:
                # We assume admin is passing domain id
                dom = opcloud.get_domain(domain)['id']
                domain = dom
            except Exception:
                # If we fail, maybe admin is passing a domain name.
                # Note that domains have unique names, just like id.
                dom = opcloud.search_domains(filters={'name': domain})
                if dom:
                    domain = dom[0]['id']
                else:
                    module.fail_json(msg='Domain name or ID does not exist')

            if not filters:
                filters = {}

        groups = opcloud.search_groups(name, filters, domain_id=domain)
        module.exit_json(changed=False, groups=groups)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
