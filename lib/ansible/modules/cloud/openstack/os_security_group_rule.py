#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
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

try:
    import shade
except ImportError:
    print("failed=True msg='shade is required for this module'")


DOCUMENTATION = '''
---
module: os_security_group_rule
short_description: Add/Delete rule from an existing security group
extends_documentation_fragment: openstack
version_added: "1.10"
description:
   - Add or Remove rule from an existing security group
options:
   security_group:
     description:
        - Name of the security group
     required: true
   protocol:
      description:
        - IP protocol
      choices: ['tcp', 'udp', 'icmp']
      default: tcp
   port_range_min:
      description:
        - Starting port
      required: true
   port_range_max:
      description:
        - Ending port
     required: true
   remote_ip_prefix:
      description:
        - Source IP address(es) in CIDR notation (exclusive with remote_group)
     required: false
   remote_group:
      description:
        - ID of Security group to link (exclusive with remote_ip_prefix)
     required: false
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present

requirements: ["shade"]
'''
# TODO(mordred): add ethertype and direction

EXAMPLES = '''
# Create a security group rule
- os_security_group_rule:
    cloud: mordred
    security_group: foo
    protocol: tcp
    port_range_min: 80
    port_range_max: 80
    remote_ip_prefix: 0.0.0.0/0
'''


def _security_group_rule(module, nova_client, action='create', **kwargs):
    f = getattr(nova_client.security_group_rules, action)
    try:
        secgroup = f(**kwargs)
    except Exception, e:
        module.fail_json(msg='Failed to %s security group rule: %s' %
                         (action, e.message))


def _get_rule_from_group(module, secgroup):
    for rule in secgroup['security_group_rules']:
        if (rule['protocol'] == module.params['protocol'] and
                rule['port_range_min'] == module.params['port_range_min'] and
                rule['port_range_max'] == module.params['port_range_max'] and
                rule['remote_ip_prefix'] == module.params['remote_ip_prefix']):
            return rule
    return None

def main():

    argument_spec = openstack_full_argument_spec(
        security_group     = dict(required=True),
        protocol           = dict(default='tcp', choices=['tcp', 'udp', 'icmp']),
        port_range_min     = dict(required=True),
        port_range_max     = dict(required=True),
        remote_ip_prefix   = dict(required=False, default=None),
        # TODO(mordred): Make remote_group handle name and id
        remote_group       = dict(required=False, default=None),
        state              = dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[
            ['remote_ip_prefix', 'remote_group'],
        ]
    )
    module = AnsibleModule(argument_spec, **module_kwargs)

    try:
        cloud = shade.openstack_cloud(**module.params)
        nova_client = cloud.nova_client
        changed = False

        secgroup = cloud.get_security_group(module.params['security_group'])

        if module.params['state'] == 'present':
            if not secgroup:
                module.fail_json(msg='Could not find security group %s' %
                                 module.params['security_group'])

            if not _get_rule_from_group(module, secgroup):
                _security_group_rule(module, nova_client, 'create',
                                     parent_group_id=secgroup.id,
                                     ip_protocol=module.params['protocol'],
                                     from_port=module.params['port_range_min'],
                                     to_port=module.params['port_range_max'],
                                     cidr=module.params['remote_ip_prefix']
                                     if 'remote_ip_prefix' in module.params else None,
                                     group_id=module.params['remote_group']
                                     if 'remote_group' in module.params else None
                                     )
                changed = True


        if module.params['state'] == 'absent' and secgroup:
            rule = _get_rule_from_group(module, secgroup)
            if secgroup and rule:
                _security_group_rule(module, nova_client, 'delete',
                                     rule=rule['id'])
                changed = True

        module.exit_json(changed=changed, result="success")

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

main()
