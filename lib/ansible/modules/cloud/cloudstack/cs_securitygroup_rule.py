#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_securitygroup_rule
short_description: Manages security group rules on Apache CloudStack based clouds.
description:
    - Add and remove security group rules.
version_added: '2.0'
author: René Moser (@resmo)
options:
  security_group:
    description:
      - Name of the security group the rule is related to. The security group must be existing.
    type: str
    required: true
  state:
    description:
      - State of the security group rule.
    type: str
    default: present
    choices: [ present, absent ]
  protocol:
    description:
      - Protocol of the security group rule.
    type: str
    default: tcp
    choices: [ tcp, udp, icmp, ah, esp, gre ]
  type:
    description:
      - Ingress or egress security group rule.
    type: str
    default: ingress
    choices: [ ingress, egress ]
  cidr:
    description:
      - CIDR (full notation) to be used for security group rule.
    type: str
    default: 0.0.0.0/0
  user_security_group:
    description:
      - Security group this rule is based of.
    type: str
  start_port:
    description:
      - Start port for this rule. Required if I(protocol=tcp) or I(protocol=udp).
    type: int
    aliases: [ port ]
  end_port:
    description:
      - End port for this rule. Required if I(protocol=tcp) or I(protocol=udp), but I(start_port) will be used if not set.
    type: int
  icmp_type:
    description:
      - Type of the icmp message being sent. Required if I(protocol=icmp).
    type: int
  icmp_code:
    description:
      - Error code for this icmp message. Required if I(protocol=icmp).
    type: int
  project:
    description:
      - Name of the project the security group to be created in.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
---
- name: allow inbound port 80/tcp from 1.2.3.4 added to security group 'default'
  cs_securitygroup_rule:
    security_group: default
    port: 80
    cidr: 1.2.3.4/32
  delegate_to: localhost

- name: allow tcp/udp outbound added to security group 'default'
  cs_securitygroup_rule:
    security_group: default
    type: egress
    start_port: 1
    end_port: 65535
    protocol: '{{ item }}'
  with_items:
  - tcp
  - udp
  delegate_to: localhost

- name: allow inbound icmp from 0.0.0.0/0 added to security group 'default'
  cs_securitygroup_rule:
    security_group: default
    protocol: icmp
    icmp_code: -1
    icmp_type: -1
  delegate_to: localhost

- name: remove rule inbound port 80/tcp from 0.0.0.0/0 from security group 'default'
  cs_securitygroup_rule:
    security_group: default
    port: 80
    state: absent
  delegate_to: localhost

- name: allow inbound port 80/tcp from security group web added to security group 'default'
  cs_securitygroup_rule:
    security_group: default
    port: 80
    user_security_group: web
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the of the rule.
  returned: success
  type: str
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
security_group:
  description: security group of the rule.
  returned: success
  type: str
  sample: default
type:
  description: type of the rule.
  returned: success
  type: str
  sample: ingress
cidr:
  description: CIDR of the rule.
  returned: success and cidr is defined
  type: str
  sample: 0.0.0.0/0
user_security_group:
  description: user security group of the rule.
  returned: success and user_security_group is defined
  type: str
  sample: default
protocol:
  description: protocol of the rule.
  returned: success
  type: str
  sample: tcp
start_port:
  description: start port of the rule.
  returned: success
  type: int
  sample: 80
end_port:
  description: end port of the rule.
  returned: success
  type: int
  sample: 80
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import AnsibleCloudStack, cs_argument_spec, cs_required_together


class AnsibleCloudStackSecurityGroupRule(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackSecurityGroupRule, self).__init__(module)
        self.returns = {
            'icmptype': 'icmp_type',
            'icmpcode': 'icmp_code',
            'endport': 'end_port',
            'startport': 'start_port',
            'protocol': 'protocol',
            'cidr': 'cidr',
            'securitygroupname': 'user_security_group',
        }

    def _tcp_udp_match(self, rule, protocol, start_port, end_port):
        return (protocol in ['tcp', 'udp'] and
                protocol == rule['protocol'] and
                start_port == int(rule['startport']) and
                end_port == int(rule['endport']))

    def _icmp_match(self, rule, protocol, icmp_code, icmp_type):
        return (protocol == 'icmp' and
                protocol == rule['protocol'] and
                icmp_code == int(rule['icmpcode']) and
                icmp_type == int(rule['icmptype']))

    def _ah_esp_gre_match(self, rule, protocol):
        return (protocol in ['ah', 'esp', 'gre'] and
                protocol == rule['protocol'])

    def _type_security_group_match(self, rule, security_group_name):
        return (security_group_name and
                'securitygroupname' in rule and
                security_group_name == rule['securitygroupname'])

    def _type_cidr_match(self, rule, cidr):
        return ('cidr' in rule and
                cidr == rule['cidr'])

    def _get_rule(self, rules):
        user_security_group_name = self.module.params.get('user_security_group')
        cidr = self.module.params.get('cidr')
        protocol = self.module.params.get('protocol')
        start_port = self.module.params.get('start_port')
        end_port = self.get_or_fallback('end_port', 'start_port')
        icmp_code = self.module.params.get('icmp_code')
        icmp_type = self.module.params.get('icmp_type')

        if protocol in ['tcp', 'udp'] and (start_port is None or end_port is None):
            self.module.fail_json(msg="no start_port or end_port set for protocol '%s'" % protocol)

        if protocol == 'icmp' and (icmp_type is None or icmp_code is None):
            self.module.fail_json(msg="no icmp_type or icmp_code set for protocol '%s'" % protocol)

        for rule in rules:
            if user_security_group_name:
                type_match = self._type_security_group_match(rule, user_security_group_name)
            else:
                type_match = self._type_cidr_match(rule, cidr)

            protocol_match = (self._tcp_udp_match(rule, protocol, start_port, end_port) or
                              self._icmp_match(rule, protocol, icmp_code, icmp_type) or
                              self._ah_esp_gre_match(rule, protocol))

            if type_match and protocol_match:
                return rule
        return None

    def get_security_group(self, security_group_name=None):
        if not security_group_name:
            security_group_name = self.module.params.get('security_group')
        args = {
            'securitygroupname': security_group_name,
            'projectid': self.get_project('id'),
        }
        sgs = self.query_api('listSecurityGroups', **args)
        if not sgs or 'securitygroup' not in sgs:
            self.module.fail_json(msg="security group '%s' not found" % security_group_name)
        return sgs['securitygroup'][0]

    def add_rule(self):
        security_group = self.get_security_group()

        args = {}
        user_security_group_name = self.module.params.get('user_security_group')

        # the user_security_group and cidr are mutually_exclusive, but cidr is defaulted to 0.0.0.0/0.
        # that is why we ignore if we have a user_security_group.
        if user_security_group_name:
            args['usersecuritygrouplist'] = []
            user_security_group = self.get_security_group(user_security_group_name)
            args['usersecuritygrouplist'].append({
                'group': user_security_group['name'],
                'account': user_security_group['account'],
            })
        else:
            args['cidrlist'] = self.module.params.get('cidr')

        args['protocol'] = self.module.params.get('protocol')
        args['startport'] = self.module.params.get('start_port')
        args['endport'] = self.get_or_fallback('end_port', 'start_port')
        args['icmptype'] = self.module.params.get('icmp_type')
        args['icmpcode'] = self.module.params.get('icmp_code')
        args['projectid'] = self.get_project('id')
        args['securitygroupid'] = security_group['id']

        rule = None
        res = None
        sg_type = self.module.params.get('type')
        if sg_type == 'ingress':
            if 'ingressrule' in security_group:
                rule = self._get_rule(security_group['ingressrule'])
            if not rule:
                self.result['changed'] = True
                if not self.module.check_mode:
                    res = self.query_api('authorizeSecurityGroupIngress', **args)

        elif sg_type == 'egress':
            if 'egressrule' in security_group:
                rule = self._get_rule(security_group['egressrule'])
            if not rule:
                self.result['changed'] = True
                if not self.module.check_mode:
                    res = self.query_api('authorizeSecurityGroupEgress', **args)

        poll_async = self.module.params.get('poll_async')
        if res and poll_async:
            security_group = self.poll_job(res, 'securitygroup')
            key = sg_type + "rule"  # ingressrule / egressrule
            if key in security_group:
                rule = security_group[key][0]
        return rule

    def remove_rule(self):
        security_group = self.get_security_group()
        rule = None
        res = None
        sg_type = self.module.params.get('type')
        if sg_type == 'ingress':
            rule = self._get_rule(security_group['ingressrule'])
            if rule:
                self.result['changed'] = True
                if not self.module.check_mode:
                    res = self.query_api('revokeSecurityGroupIngress', id=rule['ruleid'])

        elif sg_type == 'egress':
            rule = self._get_rule(security_group['egressrule'])
            if rule:
                self.result['changed'] = True
                if not self.module.check_mode:
                    res = self.query_api('revokeSecurityGroupEgress', id=rule['ruleid'])

        poll_async = self.module.params.get('poll_async')
        if res and poll_async:
            res = self.poll_job(res, 'securitygroup')
        return rule

    def get_result(self, security_group_rule):
        super(AnsibleCloudStackSecurityGroupRule, self).get_result(security_group_rule)
        self.result['type'] = self.module.params.get('type')
        self.result['security_group'] = self.module.params.get('security_group')
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        security_group=dict(required=True),
        type=dict(choices=['ingress', 'egress'], default='ingress'),
        cidr=dict(default='0.0.0.0/0'),
        user_security_group=dict(),
        protocol=dict(choices=['tcp', 'udp', 'icmp', 'ah', 'esp', 'gre'], default='tcp'),
        icmp_type=dict(type='int'),
        icmp_code=dict(type='int'),
        start_port=dict(type='int', aliases=['port']),
        end_port=dict(type='int'),
        state=dict(choices=['present', 'absent'], default='present'),
        project=dict(),
        poll_async=dict(type='bool', default=True),
    ))
    required_together = cs_required_together()
    required_together.extend([
        ['icmp_type', 'icmp_code'],
    ])

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        mutually_exclusive=(
            ['icmp_type', 'start_port'],
            ['icmp_type', 'end_port'],
            ['icmp_code', 'start_port'],
            ['icmp_code', 'end_port'],
        ),
        supports_check_mode=True
    )

    acs_sg_rule = AnsibleCloudStackSecurityGroupRule(module)

    state = module.params.get('state')
    if state in ['absent']:
        sg_rule = acs_sg_rule.remove_rule()
    else:
        sg_rule = acs_sg_rule.add_rule()

    result = acs_sg_rule.get_result(sg_rule)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
