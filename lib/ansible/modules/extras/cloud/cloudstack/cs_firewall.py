#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_firewall
short_description: Manages firewall rules on Apache CloudStack based clouds.
description: Creates and removes firewall rules.
version_added: '2.0'
author: '"René Moser (@resmo)" <mail@renemoser.net>'
options:
  ip_address:
    description:
      - Public IP address the rule is assigned to.
    required: true
  state:
    description:
      - State of the firewall rule.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  protocol:
    description:
      - Protocol of the firewall rule.
    required: false
    default: 'tcp'
    choices: [ 'tcp', 'udp', 'icmp' ]
  cidr:
    description:
      - CIDR (full notation) to be used for firewall rule.
    required: false
    default: '0.0.0.0/0'
  start_port:
    description:
      - Start port for this rule. Considered if C(protocol=tcp) or C(protocol=udp).
    required: false
    default: null
    aliases: [ 'port' ]
  end_port:
    description:
      - End port for this rule. Considered if C(protocol=tcp) or C(protocol=udp). If not specified, equal C(start_port).
    required: false
    default: null
  icmp_type:
    description:
      - Type of the icmp message being sent. Considered if C(protocol=icmp).
    required: false
    default: null
  icmp_code:
    description:
      - Error code for this icmp message. Considered if C(protocol=icmp).
    required: false
    default: null
  domain:
    description:
      - Domain the firewall rule is related to.
    required: false
    default: null
  account:
    description:
      - Account the firewall rule is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the firewall rule is related to.
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
---
# Allow inbound port 80/tcp from 1.2.3.4 to 4.3.2.1
- local_action:
    module: cs_firewall
    ip_address: 4.3.2.1
    port: 80
    cidr: 1.2.3.4/32


# Allow inbound tcp/udp port 53 to 4.3.2.1
- local_action:
    module: cs_firewall
    ip_address: 4.3.2.1
    port: 53
    protocol: '{{ item }}'
  with_items:
  - tcp
  - udp


# Ensure firewall rule is removed
- local_action:
    module: cs_firewall
    ip_address: 4.3.2.1
    start_port: 8000
    end_port: 8888
    cidr: 17.0.0.0/8
    state: absent
'''

RETURN = '''
---
ip_address:
  description: IP address of the rule.
  returned: success
  type: string
  sample: 10.100.212.10
cidr:
  description: CIDR of the rule.
  returned: success
  type: string
  sample: 0.0.0.0/0
protocol:
  description: Protocol of the rule.
  returned: success
  type: string
  sample: tcp
start_port:
  description: Start port of the rule.
  returned: success
  type: int
  sample: 80
end_port:
  description: End port of the rule.
  returned: success
  type: int
  sample: 80
icmp_code:
  description: ICMP code of the rule.
  returned: success
  type: int
  sample: 1
icmp_type:
  description: ICMP type of the rule.
  returned: success
  type: int
  sample: 1
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackFirewall(AnsibleCloudStack):

    def __init__(self, module):
        AnsibleCloudStack.__init__(self, module)
        self.result = {
            'changed': False,
        }
        self.firewall_rule = None


    def get_end_port(self):
        if self.module.params.get('end_port'):
            return self.module.params.get('end_port')
        return self.module.params.get('start_port')


    def get_firewall_rule(self):
        if not self.firewall_rule:
            cidr = self.module.params.get('cidr')
            protocol = self.module.params.get('protocol')
            start_port = self.module.params.get('start_port')
            end_port = self.get_end_port()
            icmp_code = self.module.params.get('icmp_code')
            icmp_type = self.module.params.get('icmp_type')

            if protocol in ['tcp', 'udp'] and not (start_port and end_port):
                self.module.fail_json(msg="no start_port or end_port set for protocol '%s'" % protocol)

            if protocol == 'icmp' and not icmp_type:
                self.module.fail_json(msg="no icmp_type set")

            args                = {}
            args['ipaddressid'] = self.get_ip_address('id')
            args['account']     = self.get_account('name')
            args['domainid']    = self.get_domain('id')
            args['projectid']   = self.get_project('id')

            firewall_rules = self.cs.listFirewallRules(**args)
            if firewall_rules and 'firewallrule' in firewall_rules:
                for rule in firewall_rules['firewallrule']:
                    type_match = self._type_cidr_match(rule, cidr)

                    protocol_match = self._tcp_udp_match(rule, protocol, start_port, end_port) \
                        or self._icmp_match(rule, protocol, icmp_code, icmp_type)

                    if type_match and protocol_match:
                        self.firewall_rule = rule
                        break
        return self.firewall_rule


    def _tcp_udp_match(self, rule, protocol, start_port, end_port):
        return protocol in ['tcp', 'udp'] \
            and protocol == rule['protocol'] \
            and start_port == int(rule['startport']) \
            and end_port == int(rule['endport'])


    def _icmp_match(self, rule, protocol, icmp_code, icmp_type):
        return protocol == 'icmp' \
           and protocol == rule['protocol'] \
           and icmp_code == rule['icmpcode'] \
           and icmp_type == rule['icmptype']


    def _type_cidr_match(self, rule, cidr):
        return cidr == rule['cidrlist']


    def create_firewall_rule(self):
        firewall_rule = self.get_firewall_rule()
        if not firewall_rule:
            self.result['changed'] = True

            args                = {}
            args['cidrlist']    = self.module.params.get('cidr')
            args['protocol']    = self.module.params.get('protocol')
            args['startport']   = self.module.params.get('start_port')
            args['endport']     = self.get_end_port()
            args['icmptype']    = self.module.params.get('icmp_type')
            args['icmpcode']    = self.module.params.get('icmp_code')
            args['ipaddressid'] = self.get_ip_address('id')

            if not self.module.check_mode:
                firewall_rule = self.cs.createFirewallRule(**args)

        return firewall_rule


    def remove_firewall_rule(self):
        firewall_rule = self.get_firewall_rule()
        if firewall_rule:
            self.result['changed'] = True
            args = {}
            args['id'] = firewall_rule['id']

            if not self.module.check_mode:
                res = self.cs.deleteFirewallRule(**args)

        return firewall_rule


    def get_result(self, firewall_rule):
        if firewall_rule:
            if 'cidrlist' in firewall_rule:
                self.result['cidr'] = firewall_rule['cidrlist']
            if 'startport' in firewall_rule:
                self.result['start_port'] = int(firewall_rule['startport'])
            if 'endport' in firewall_rule:
                self.result['end_port'] = int(firewall_rule['endport'])
            if 'protocol' in firewall_rule:
                self.result['protocol'] = firewall_rule['protocol']
            if 'ipaddress' in firewall_rule:
                self.result['ip_address'] = firewall_rule['ipaddress']
            if 'icmpcode' in firewall_rule:
                self.result['icmp_code'] = int(firewall_rule['icmpcode'])
            if 'icmptype' in firewall_rule:
                self.result['icmp_type'] = int(firewall_rule['icmptype'])
        return self.result


def main():
    module = AnsibleModule(
        argument_spec = dict(
            ip_address = dict(required=True),
            cidr = dict(default='0.0.0.0/0'),
            protocol = dict(choices=['tcp', 'udp', 'icmp'], default='tcp'),
            icmp_type = dict(type='int', default=None),
            icmp_code = dict(type='int', default=None),
            start_port = dict(type='int', aliases=['port'], default=None),
            end_port = dict(type='int', default=None),
            state = dict(choices=['present', 'absent'], default='present'),
            domain = dict(default=None),
            account = dict(default=None),
            project = dict(default=None),
            api_key = dict(default=None),
            api_secret = dict(default=None, no_log=True),
            api_url = dict(default=None),
            api_http_method = dict(default='get'),
        ),
        mutually_exclusive = (
            ['icmp_type', 'start_port'],
            ['icmp_type', 'end_port'],
        ),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_fw = AnsibleCloudStackFirewall(module)

        state = module.params.get('state')
        if state in ['absent']:
            fw_rule = acs_fw.remove_firewall_rule()
        else:
            fw_rule = acs_fw.create_firewall_rule()

        result = acs_fw.get_result(fw_rule)

    except CloudStackException, e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
