#!/usr/bin/python

# Copyright (c) 2017 Ulrich Fink <fink@netzlink.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: os_security_group_facts
short_description: Retrieve facts about all OpenStack security groups.
version_added: "2.5"
author: "Ulrich Fink (fink@netzlink.com)"
description:
    - Retrieve facts about all security groups from OpenStack.
requirements:
    - "python >= 2.6"
    - "shade"
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather facts about previously created networks
- os_security_groups_facts:
    auth:
      auth_url: https://your_api_url.com:9000/v2.0
      username: user
      password: password
      project_name: someproject
- debug: var=openstack_security_groups
'''

RETURN = '''
openstack_security_groups:
    description: has all the openstack facts about the security groups
    returned: always, but can be null
    type: complex
    contains:
        - description: Security group description
          id: Unique UUID
          location:
              cloud: Cloud name
              project:
                  domain_id:
                  domain_name:
                  id:
                  name:
              region_name:
              zone:
          name: Security group name
          project_id:
          properties: {}
          security_group_rules:
              - description: Security group rule description
                direction: ingress/egress
                ethertype: e.g. IPv4
                id: Unique UUID
                location:
                    cloud:
                    project:
                        domain_id:
                        domain_name:
                        id:
                        name:
                    region_name:
                    zone:
                port_range_max:
                port_range_min:
                project_id:
                properties:
                    description:
                    port_range_min:
                protocol: icmp/tcp/udp
                remote_group_id:
                remote_group:
                remote_ip_prefix:
                security_group_id:
                tenant_id:
          tenant_id:
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None),
        filters=dict(required=False, type='dict', default=None)
    )
    module = AnsibleModule(argument_spec)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud(**module.params)
        security_groups = cleanProtocol(cloud.list_security_groups())

        module.exit_json(changed=False, ansible_facts=dict(
            openstack_security_groups=security_groups))

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


def cleanProtocol(security_groups):
    for group in security_groups:
        for rule in group['security_group_rules']:
            if rule['protocol'] is None or rule['protocol'].strip() == '':
                rule['protocol'] = None
    return security_groups


if __name__ == '__main__':
    main()
