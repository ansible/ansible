#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_security_group_rule
short_description: Add/Delete rule from an existing security group
author: "Benno Joy (@bennojoy)"
extends_documentation_fragment: openstack
version_added: "2.0"
description:
   - Add or Remove rule from an existing security group
options:
   security_group:
     description:
        - Name or ID of the security group
     required: true
   protocol:
      description:
        - IP protocols TCP UDP ICMP 112 (VRRP)
      choices: ['tcp', 'udp', 'icmp', '112', None]
      default: None
   port_range_min:
      description:
        - Starting port
      required: false
      default: None
   port_range_max:
      description:
        - Ending port
      required: false
      default: None
   remote_ip_prefix:
      description:
        - Source IP address(es) in CIDR notation (exclusive with remote_group)
      required: false
   remote_group:
      description:
        - Name or ID of the Security group to link (exclusive with
          remote_ip_prefix)
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
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements: ["shade"]
'''

EXAMPLES = '''
# Create a security group rule
- os_security_group_rule:
    cloud: mordred
    security_group: foo
    protocol: tcp
    port_range_min: 80
    port_range_max: 80
    remote_ip_prefix: 0.0.0.0/0

# Create a security group rule for ping
- os_security_group_rule:
    cloud: mordred
    security_group: foo
    protocol: icmp
    remote_ip_prefix: 0.0.0.0/0

# Another way to create the ping rule
- os_security_group_rule:
    cloud: mordred
    security_group: foo
    protocol: icmp
    port_range_min: -1
    port_range_max: -1
    remote_ip_prefix: 0.0.0.0/0

# Create a TCP rule covering all ports
- os_security_group_rule:
    cloud: mordred
    security_group: foo
    protocol: tcp
    port_range_min: 1
    port_range_max: 65535
    remote_ip_prefix: 0.0.0.0/0

# Another way to create the TCP rule above (defaults to all ports)
- os_security_group_rule:
    cloud: mordred
    security_group: foo
    protocol: tcp
    remote_ip_prefix: 0.0.0.0/0

# Create a rule for VRRP with numbered protocol 112
- os_security_group_rule:
    security_group: loadbalancer_sg
    protocol: 112
    remote_group: loadbalancer-node_sg
'''

RETURN = '''
id:
  description: Unique rule UUID.
  type: string
  returned: state == present
direction:
  description: The direction in which the security group rule is applied.
  type: string
  sample: 'egress'
  returned: state == present
ethertype:
  description: One of IPv4 or IPv6.
  type: string
  sample: 'IPv4'
  returned: state == present
port_range_min:
  description: The minimum port number in the range that is matched by
               the security group rule.
  type: int
  sample: 8000
  returned: state == present
port_range_max:
  description: The maximum port number in the range that is matched by
               the security group rule.
  type: int
  sample: 8000
  returned: state == present
protocol:
  description: The protocol that is matched by the security group rule.
  type: string
  sample: 'tcp'
  returned: state == present
remote_ip_prefix:
  description: The remote IP prefix to be associated with this security group rule.
  type: string
  sample: '0.0.0.0/0'
  returned: state == present
security_group_id:
  description: The security group ID to associate with this security group rule.
  type: string
  returned: state == present
'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs


def _ports_match(protocol, module_min, module_max, rule_min, rule_max):
    """
    Capture the complex port matching logic.

    The port values coming in for the module might be -1 (for ICMP),
    which will work only for Nova, but this is handled by shade. Likewise,
    they might be None, which works for Neutron, but not Nova. This too is
    handled by shade. Since shade will consistently return these port
    values as None, we need to convert any -1 values input to the module
    to None here for comparison.

    For TCP and UDP protocols, None values for both min and max are
    represented as the range 1-65535 for Nova, but remain None for
    Neutron. Shade returns the full range when Nova is the backend (since
    that is how Nova stores them), and None values for Neutron. If None
    values are input to the module for both values, then we need to adjust
    for comparison.
    """

    # Check if the user is supplying -1 for ICMP.
    if protocol == 'icmp':
        if module_min and int(module_min) == -1:
            module_min = None
        if module_max and int(module_max) == -1:
            module_max = None

    # Check if the user is supplying -1 or None values for full TPC/UDP port range.
    if protocol in ['tcp', 'udp'] or protocol is None:
        if module_min and module_max and int(module_min) == int(module_max) == -1:
            module_min = None
            module_max = None

        if ((module_min is None and module_max is None) and
                (rule_min and int(rule_min) == 1 and
                    rule_max and int(rule_max) == 65535)):
            # (None, None) == (1, 65535)
            return True

    # Sanity check to make sure we don't have type comparison issues.
    if module_min:
        module_min = int(module_min)
    if module_max:
        module_max = int(module_max)
    if rule_min:
        rule_min = int(rule_min)
    if rule_max:
        rule_max = int(rule_max)

    return module_min == rule_min and module_max == rule_max


def _find_matching_rule(module, secgroup, remotegroup):
    """
    Find a rule in the group that matches the module parameters.
    :returns: The matching rule dict, or None if no matches.
    """
    protocol = module.params['protocol']
    remote_ip_prefix = module.params['remote_ip_prefix']
    ethertype = module.params['ethertype']
    direction = module.params['direction']
    remote_group_id = remotegroup['id']

    for rule in secgroup['security_group_rules']:
        if (protocol == rule['protocol']
                and remote_ip_prefix == rule['remote_ip_prefix']
                and ethertype == rule['ethertype']
                and direction == rule['direction']
                and remote_group_id == rule['remote_group_id']
                and _ports_match(protocol,
                                 module.params['port_range_min'],
                                 module.params['port_range_max'],
                                 rule['port_range_min'],
                                 rule['port_range_max'])):
            return rule
    return None


def _system_state_change(module, secgroup, remotegroup):
    state = module.params['state']
    if secgroup:
        rule_exists = _find_matching_rule(module, secgroup, remotegroup)
    else:
        return False

    if state == 'present' and not rule_exists:
        return True
    if state == 'absent' and rule_exists:
        return True
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        security_group=dict(required=True),
        # NOTE(Shrews): None is an acceptable protocol value for
        # Neutron, but Nova will balk at this.
        protocol=dict(default=None,
                      choices=[None, 'tcp', 'udp', 'icmp', '112']),
        port_range_min=dict(required=False, type='int'),
        port_range_max=dict(required=False, type='int'),
        remote_ip_prefix=dict(required=False, default=None),
        remote_group=dict(required=False, default=None),
        ethertype=dict(default='IPv4',
                       choices=['IPv4', 'IPv6']),
        direction=dict(default='ingress',
                       choices=['egress', 'ingress']),
        state=dict(default='present',
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

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    security_group = module.params['security_group']
    remote_group = module.params['remote_group']
    changed = False

    try:
        cloud = shade.openstack_cloud(**module.params)
        secgroup = cloud.get_security_group(security_group)

        if remote_group:
            remotegroup = cloud.get_security_group(remote_group)
        else:
            remotegroup = {'id': None}

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, secgroup, remotegroup))

        if state == 'present':
            if not secgroup:
                module.fail_json(msg='Could not find security group %s' %
                                 security_group)

            rule = _find_matching_rule(module, secgroup, remotegroup)
            if not rule:
                rule = cloud.create_security_group_rule(
                    secgroup['id'],
                    port_range_min=module.params['port_range_min'],
                    port_range_max=module.params['port_range_max'],
                    protocol=module.params['protocol'],
                    remote_ip_prefix=module.params['remote_ip_prefix'],
                    remote_group_id=remotegroup['id'],
                    direction=module.params['direction'],
                    ethertype=module.params['ethertype']
                )
                changed = True
            module.exit_json(changed=changed, rule=rule, id=rule['id'])

        if state == 'absent' and secgroup:
            rule = _find_matching_rule(module, secgroup, remotegroup)
            if rule:
                cloud.delete_security_group_rule(rule['id'])
                changed = True

            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
