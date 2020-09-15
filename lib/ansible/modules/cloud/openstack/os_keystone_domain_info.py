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
module: os_keystone_domain_info
short_description: Retrieve information about one or more OpenStack domains
extends_documentation_fragment: openstack
version_added: "2.1"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
description:
    - Retrieve information about a one or more OpenStack domains
    - This module was called C(os_keystone_domain_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(os_keystone_domain_info) module no longer returns C(ansible_facts)!
requirements:
    - "python >= 2.7"
    - "sdk"
options:
   name:
     description:
        - Name or ID of the domain
   filters:
     description:
        - A dictionary of meta data to use for further filtering.  Elements of
          this dictionary may be additional dictionaries.
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
'''

EXAMPLES = '''
# Gather information about previously created domain
- os_keystone_domain_info:
    cloud: awesomecloud
  register: result
- debug:
    msg: "{{ result.openstack_domains }}"

# Gather information about a previously created domain by name
- os_keystone_domain_info:
    cloud: awesomecloud
    name: demodomain
  register: result
- debug:
    msg: "{{ result.openstack_domains }}"

# Gather information about a previously created domain with filter
- os_keystone_domain_info:
    cloud: awesomecloud
    name: demodomain
    filters:
      enabled: false
  register: result
- debug:
    msg: "{{ result.openstack_domains }}"
'''


RETURN = '''
openstack_domains:
    description: has all the OpenStack information about domains
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: str
        name:
            description: Name given to the domain.
            returned: success
            type: str
        description:
            description: Description of the domain.
            returned: success
            type: str
        enabled:
            description: Flag to indicate if the domain is enabled.
            returned: success
            type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


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
    is_old_facts = module._name == 'os_keystone_domain_facts'
    if is_old_facts:
        module.deprecate("The 'os_keystone_domain_facts' module has been renamed to 'os_keystone_domain_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    sdk, opcloud = openstack_cloud_from_module(module)
    try:
        name = module.params['name']
        filters = module.params['filters']

        if name:
            # Let's suppose user is passing domain ID
            try:
                domains = opcloud.get_domain(name)
            except Exception:
                domains = opcloud.search_domains(filters={'name': name})

        else:
            domains = opcloud.search_domains(filters)

        if is_old_facts:
            module.exit_json(changed=False, ansible_facts=dict(
                openstack_domains=domains))
        else:
            module.exit_json(changed=False, openstack_domains=domains)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
