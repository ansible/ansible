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
   ethertype:
      description:
        - Must be IPv4 or IPv6, and addresses represented in CIDR must
          match the ingress or egress rules. Not all providers support IPv6.
      choices: ['IPv4', 'IPv6']
      default: IPv4
   direction:
     description:
        - The direction in which the security group rule is applied. Not
          all providers support egress.
     choices: ['egress', 'ingress']
     default: ingress
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


def _find_matching_rule(module, secgroup):
    """
    Find a rule in the group that matches the module parameters.
    :returns: The matching rule dict, or None if no matches.
    """
    protocol = module.params['protocol']
    port_range_min = int(module.params['port_range_min'])
    port_range_max = int(module.params['port_range_max'])
    remote_ip_prefix = module.params['remote_ip_prefix']
    ethertype = module.params['ethertype']
    direction = module.params['direction']

    for rule in secgroup['security_group_rules']:
        # No port, or -1, will be returned from shade as None
        if rule['port_range_min'] is None:
            rule_port_range_min = -1
        else:
            rule_port_range_min = int(rule['port_range_min'])

        if rule['port_range_max'] is None:
            rule_port_range_max = -1
        else:
            rule_port_range_max = int(rule['port_range_max'])


        if (protocol == rule['protocol']
                and port_range_min == rule_port_range_min
                and port_range_max == rule_port_range_max
                and remote_ip_prefix == rule['remote_ip_prefix']
                and ethertype == rule['ethertype']
                and direction == rule['direction']):
            return rule
    return None


def _system_state_change(module, secgroup):
    state = module.params['state']
    if secgroup:
        rule_exists = _find_matching_rule(module, secgroup)
    else:
        return False

    if state == 'present' and not rule_exists:
        return True
    if state == 'absent' and rule_exists:
        return True
    return False


def main():

    argument_spec = openstack_full_argument_spec(
        security_group   = dict(required=True),
        protocol         = dict(default='tcp',
                                choices=['tcp', 'udp', 'icmp']),
        port_range_min   = dict(required=True),
        port_range_max   = dict(required=True),
        remote_ip_prefix = dict(required=False, default=None),
        # TODO(mordred): Make remote_group handle name and id
        remote_group     = dict(required=False, default=None),
        ethertype        = dict(default='IPv4',
                                choices=['IPv4', 'IPv6']),
        direction        = dict(default='ingress',
                                choices=['egress', 'ingress']),
        state            = dict(default='present',
                                choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[
            ['remote_ip_prefix', 'remote_group'],
        ]
    )

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    state = module.params['state']
    security_group = module.params['security_group']
    changed = False

    try:
        cloud = shade.openstack_cloud(**module.params)
        secgroup = cloud.get_security_group(security_group)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, secgroup))

        if state == 'present':
            if not secgroup:
                module.fail_json(msg='Could not find security group %s' %
                                 security_group)

            rule = _find_matching_rule(module, secgroup)
            if not rule:
                rule = cloud.create_security_group_rule(
                    secgroup['id'],
                    port_range_min=module.params['port_range_min'],
                    port_range_max=module.params['port_range_max'],
                    protocol=module.params['protocol'],
                    remote_ip_prefix=module.params['remote_ip_prefix'],
                    remote_group_id=module.params['remote_group'],
                    direction=module.params['direction'],
                    ethertype=module.params['ethertype']
                )
                changed = True
            module.exit_json(changed=changed, rule=rule, id=rule['id'])

        if state == 'absent' and secgroup:
            rule = _find_matching_rule(module, secgroup)
            if rule:
                cloud.delete_security_group_rule(rule['id'])
                changed = True

            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

main()