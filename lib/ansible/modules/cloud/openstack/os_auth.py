#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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
module: os_auth
short_description: Retrieve an auth token
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
    - Retrieve an auth token from an OpenStack Cloud
requirements:
    - "python >= 2.6"
    - "shade"
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

try:
    import shade
    from shade import meta
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def main():

    argument_spec = openstack_full_argument_spec()
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud(**module.params)
        module.exit_json(
            changed=False,
            ansible_facts=dict(
                auth_token=cloud.auth_token,
                service_catalog=cloud.service_catalog))
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
