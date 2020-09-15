#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vultr_firewall_rule
short_description: Manages firewall rules on Vultr.
description:
  - Create and remove firewall rules.
version_added: "2.5"
author: "René Moser (@resmo)"
options:
  group:
    description:
      - Name of the firewall group.
    required: true
  ip_version:
    description:
      - IP address version
    choices: [ v4, v6 ]
    default: v4
    aliases: [ ip_type ]
  protocol:
    description:
      - Protocol of the firewall rule.
    choices: [ icmp, tcp, udp, gre ]
    default: tcp
  cidr:
    description:
      - Network in CIDR format
      - The CIDR format must match with the C(ip_version) value.
      - Required if C(state=present).
      - Defaulted to 0.0.0.0/0 or ::/0 depending on C(ip_version).
  start_port:
    description:
      - Start port for the firewall rule.
      - Required if C(protocol) is tcp or udp and I(state=present).
    aliases: [ port ]
  end_port:
    description:
      - End port for the firewall rule.
      - Only considered if C(protocol) is tcp or udp and I(state=present).
  state:
    description:
      - State of the firewall rule.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = '''
- name: ensure a firewall rule is present
  local_action:
    module: vultr_firewall_rule
    group: application
    protocol: tcp
    start_port: 8000
    end_port: 9000
    cidr: 17.17.17.0/24

- name: open DNS port for all ipv4 and ipv6
  local_action:
    module: vultr_firewall_rule
    group: dns
    protocol: udp
    port: 53
    ip_version: "{{ item }}"
  with_items: [ v4, v6 ]

- name: allow ping
  local_action:
    module: vultr_firewall_rule
    group: web
    protocol: icmp

- name: ensure a firewall rule is absent
  local_action:
    module: vultr_firewall_rule
    group: application
    protocol: tcp
    start_port: 8000
    end_port: 9000
    cidr: 17.17.17.0/24
    state: absent
'''

RETURN = '''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: str
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
    api_retries:
      description: Amount of max retries for the API requests
      returned: success
      type: int
      sample: 5
    api_retry_max_delay:
      description: Exponential backoff delay in seconds between retries up to this max delay value.
      returned: success
      type: int
      sample: 12
      version_added: '2.9'
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: str
      sample: "https://api.vultr.com"
vultr_firewall_rule:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    rule_number:
      description: Rule number of the firewall rule
      returned: success
      type: int
      sample: 2
    action:
      description: Action of the firewall rule
      returned: success
      type: str
      sample: accept
    protocol:
      description: Protocol of the firewall rule
      returned: success
      type: str
      sample: tcp
    start_port:
      description: Start port of the firewall rule
      returned: success and protocol is tcp or udp
      type: int
      sample: 80
    end_port:
      description: End port of the firewall rule
      returned: success and when port range and protocol is tcp or udp
      type: int
      sample: 8080
    cidr:
      description: CIDR of the firewall rule (IPv4 or IPv6)
      returned: success and when port range
      type: str
      sample: 0.0.0.0/0
    group:
      description: Firewall group the rule is into.
      returned: success
      type: str
      sample: web
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrFirewallRule(Vultr):

    def __init__(self, module):
        super(AnsibleVultrFirewallRule, self).__init__(module, "vultr_firewall_rule")

        self.returns = {
            'rulenumber': dict(key='rule_number'),
            'action': dict(),
            'protocol': dict(),
            'start_port': dict(convert_to='int'),
            'end_port': dict(convert_to='int'),
            'cidr': dict(),
            'group': dict(),
        }
        self.firewall_group = None

    def get_firewall_group(self):
        if self.firewall_group is not None:
            return self.firewall_group

        firewall_groups = self.api_query(path="/v1/firewall/group_list")
        if firewall_groups:
            for firewall_group_id, firewall_group_data in firewall_groups.items():
                if firewall_group_data.get('description') == self.module.params.get('group'):
                    self.firewall_group = firewall_group_data
                    return self.firewall_group
        self.fail_json(msg="Firewall group not found: %s" % self.module.params.get('group'))

    def _transform_cidr(self):
        cidr = self.module.params.get('cidr')
        ip_version = self.module.params.get('ip_version')
        if cidr is None:
            if ip_version == "v6":
                cidr = "::/0"
            else:
                cidr = "0.0.0.0/0"
        elif cidr.count('/') != 1:
            self.fail_json(msg="CIDR has an invalid format: %s" % cidr)

        return cidr.split('/')

    def get_firewall_rule(self):
        ip_version = self.module.params.get('ip_version')
        firewall_group_id = self.get_firewall_group()['FIREWALLGROUPID']

        firewall_rules = self.api_query(
            path="/v1/firewall/rule_list"
                 "?FIREWALLGROUPID=%s"
                 "&direction=in"
                 "&ip_type=%s"
                 % (firewall_group_id, ip_version))

        if firewall_rules:
            subnet, subnet_size = self._transform_cidr()

            for firewall_rule_id, firewall_rule_data in firewall_rules.items():
                if firewall_rule_data.get('protocol') != self.module.params.get('protocol'):
                    continue

                if ip_version == 'v4' and (firewall_rule_data.get('subnet') or "0.0.0.0") != subnet:
                    continue

                if ip_version == 'v6' and (firewall_rule_data.get('subnet') or "::") != subnet:
                    continue

                if int(firewall_rule_data.get('subnet_size')) != int(subnet_size):
                    continue

                if firewall_rule_data.get('protocol') in ['tcp', 'udp']:
                    rule_port = firewall_rule_data.get('port')

                    end_port = self.module.params.get('end_port')
                    start_port = self.module.params.get('start_port')

                    # Port range "8000 - 8080" from the API
                    if ' - ' in rule_port:
                        if end_port is None:
                            continue

                        port_range = "%s - %s" % (start_port, end_port)
                        if rule_port == port_range:
                            return firewall_rule_data

                    # Single port
                    elif int(rule_port) == start_port:
                        return firewall_rule_data

                else:
                    return firewall_rule_data

        return {}

    def present_firewall_rule(self):
        firewall_rule = self.get_firewall_rule()
        if not firewall_rule:
            firewall_rule = self._create_firewall_rule(firewall_rule)
        return firewall_rule

    def _create_firewall_rule(self, firewall_rule):
        protocol = self.module.params.get('protocol')
        if protocol in ['tcp', 'udp']:
            start_port = self.module.params.get('start_port')

            if start_port is None:
                self.module.fail_on_missing_params(['start_port'])

            end_port = self.module.params.get('end_port')
            if end_port is not None:

                if start_port >= end_port:
                    self.module.fail_json(msg="end_port must be higher than start_port")

                port_range = "%s:%s" % (start_port, end_port)
            else:
                port_range = start_port
        else:
            port_range = None

        self.result['changed'] = True

        subnet, subnet_size = self._transform_cidr()

        data = {
            'FIREWALLGROUPID': self.get_firewall_group()['FIREWALLGROUPID'],
            'direction': 'in',  # currently the only option
            'ip_type': self.module.params.get('ip_version'),
            'protocol': protocol,
            'subnet': subnet,
            'subnet_size': subnet_size,
            'port': port_range
        }

        self.result['diff']['after'] = data

        if not self.module.check_mode:
            self.api_query(
                path="/v1/firewall/rule_create",
                method="POST",
                data=data
            )
            firewall_rule = self.get_firewall_rule()
        return firewall_rule

    def absent_firewall_rule(self):
        firewall_rule = self.get_firewall_rule()
        if firewall_rule:
            self.result['changed'] = True

            data = {
                'FIREWALLGROUPID': self.get_firewall_group()['FIREWALLGROUPID'],
                'rulenumber': firewall_rule['rulenumber']
            }

            self.result['diff']['before'] = firewall_rule

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/firewall/rule_delete",
                    method="POST",
                    data=data
                )
        return firewall_rule

    def get_result(self, resource):
        if resource:
            if 'port' in resource and resource['protocol'] in ['tcp', 'udp']:
                if ' - ' in resource['port']:
                    resource['start_port'], resource['end_port'] = resource['port'].split(' - ')
                else:
                    resource['start_port'] = resource['port']
            if 'subnet' in resource:
                resource['cidr'] = "%s/%s" % (resource['subnet'], resource['subnet_size'])
            resource['group'] = self.get_firewall_group()['description']
        return super(AnsibleVultrFirewallRule, self).get_result(resource)


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        group=dict(required=True),
        start_port=dict(type='int', aliases=['port']),
        end_port=dict(type='int'),
        protocol=dict(choices=['tcp', 'udp', 'gre', 'icmp'], default='tcp'),
        cidr=dict(),
        ip_version=dict(choices=['v4', 'v6'], default='v4', aliases=['ip_type']),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vultr_firewall_rule = AnsibleVultrFirewallRule(module)
    if module.params.get('state') == "absent":
        firewall_rule = vultr_firewall_rule.absent_firewall_rule()
    else:
        firewall_rule = vultr_firewall_rule.present_firewall_rule()

    result = vultr_firewall_rule.get_result(firewall_rule)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
