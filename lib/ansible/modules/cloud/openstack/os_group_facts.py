#!/usr/bin/python
# Copyright (c) 2016 Hewlett-Packard Enterprise Corporation
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_group_facts
short_description: Retrieve facts about one or more OpenStack groups
extends_documentation_fragment: openstack
version_added: "2.1"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
description:
    - Retrieve facts about a one or more OpenStack groups
requirements:
    - "python >= 2.7"
    - "openstacksdk"
options:
   name:
     description:
        - Name or ID of the group
     required: true
   domain:
     description:
        - Name or ID of the domain containing the group if the cloud supports domains
   filters:
     description:
        - A dictionary of meta data to use for further filtering.  Elements of
          this dictionary may be additional dictionaries.
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
'''

EXAMPLES = '''
# Gather facts about previously created groups
- os_group_facts:
    cloud: awesomecloud
- debug:
    var: openstack_groups

# Gather facts about a previously created group by name
- os_group_facts:
    cloud: awesomecloud
    name: demogroup
- debug:
    var: openstack_groups

# Gather facts about a previously created group in a specific domain
- os_group_facts:
    cloud: awesomecloud
    name: demogroup
    domain: admindomain
- debug:
    var: openstack_groups

# Gather facts about a previously created group in a specific domain with filter
- os_group_facts:
    cloud: awesomecloud
    name: demogroup
    domain: admindomain
    filters:
      enabled: False
- debug:
    var: openstack_groups
'''


RETURN = '''
openstack_groups:
    description: has all the OpenStack facts about groups
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: string
        name:
            description: Name given to the group.
            returned: success
            type: string
        description:
            description: Description of the group
            returned: success
            type: string
        enabled:
            description: Flag to indicate if the group is enabled
            returned: success
            type: bool
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
            except:
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
        module.exit_json(changed=False, ansible_facts=dict(
            openstack_groups=groups))

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
