#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_auth
short_description: Retrieve an auth token
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
    - Retrieve an auth token from an OpenStack Cloud
requirements:
    - "python >= 2.7"
    - "openstacksdk"
options:
  availability_zone:
    description:
      - Ignored. Present for backwards compatibility
    required: false
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
- name: Authenticate to the cloud and retrieve the service catalog
  os_auth:
    cloud: rax-dfw

- name: Show service catalog
  debug:
    var: service_catalog
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec()
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        module.exit_json(
            changed=False,
            ansible_facts=dict(
                auth_token=cloud.auth_token,
                service_catalog=cloud.service_catalog))
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
