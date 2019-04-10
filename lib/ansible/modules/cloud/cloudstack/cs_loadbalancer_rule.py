#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Darren Worrall <darren@iweb.co.uk>
# (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_loadbalancer_rule
short_description: Manages load balancer rules on Apache CloudStack based clouds.
description:
    - Add, update and remove load balancer rules.
version_added: '2.0'
author:
    - Darren Worrall (@dazworrall)
    - René Moser (@resmo)
options:
  name:
    description:
      - The name of the load balancer rule.
    type: str
    required: true
  description:
    description:
      - The description of the load balancer rule.
    type: str
  algorithm:
    description:
      - Load balancer algorithm
      - Required when using I(state=present).
    type: str
    choices: [ source, roundrobin, leastconn ]
    default: source
  private_port:
    description:
      - The private port of the private ip address/virtual machine where the network traffic will be load balanced to.
      - Required when using I(state=present).
      - Can not be changed once the rule exists due API limitation.
    type: int
  public_port:
    description:
      - The public port from where the network traffic will be load balanced from.
      - Required when using I(state=present).
      - Can not be changed once the rule exists due API limitation.
    type: int
    required: true
  ip_address:
    description:
      - Public IP address from where the network traffic will be load balanced from.
    type: str
    required: true
    aliases: [ public_ip ]
  open_firewall:
    description:
      - Whether the firewall rule for public port should be created, while creating the new rule.
      - Use M(cs_firewall) for managing firewall rules.
    type: bool
    default: no
  cidr:
    description:
      - CIDR (full notation) to be used for firewall rule if required.
    type: str
  protocol:
    description:
      - The protocol to be used on the load balancer
    type: str
  project:
    description:
      - Name of the project the load balancer IP address is related to.
    type: str
  state:
    description:
      - State of the rule.
    type: str
    default: present
    choices: [ present, absent ]
  domain:
    description:
      - Domain the rule is related to.
    type: str
  account:
    description:
      - Account the rule is related to.
    type: str
  zone:
    description:
      - Name of the zone in which the rule should be created.
      - If not set, default zone is used.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
  tags:
    description:
      - List of tags. Tags are a list of dictionaries having keys I(key) and I(value).
      - "To delete all tags, set a empty list e.g. I(tags: [])."
    type: list
    aliases: [ tag ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a load balancer rule
  cs_loadbalancer_rule:
    name: balance_http
    public_ip: 1.2.3.4
    algorithm: leastconn
    public_port: 80
    private_port: 8080
  delegate_to: localhost

- name: Update algorithm of an existing load balancer rule
  cs_loadbalancer_rule:
    name: balance_http
    public_ip: 1.2.3.4
    algorithm: roundrobin
    public_port: 80
    private_port: 8080
  delegate_to: localhost

- name: Delete a load balancer rule
  cs_loadbalancer_rule:
    name: balance_http
    public_ip: 1.2.3.4
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the rule.
  returned: success
  type: str
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
zone:
  description: Name of zone the rule is related to.
  returned: success
  type: str
  sample: ch-gva-2
project:
  description: Name of project the rule is related to.
  returned: success
  type: str
  sample: Production
account:
  description: Account the rule is related to.
  returned: success
  type: str
  sample: example account
domain:
  description: Domain the rule is related to.
  returned: success
  type: str
  sample: example domain
algorithm:
  description: Load balancer algorithm used.
  returned: success
  type: str
  sample: source
cidr:
  description: CIDR to forward traffic from.
  returned: success
  type: str
  sample: 0.0.0.0/0
name:
  description: Name of the rule.
  returned: success
  type: str
  sample: http-lb
description:
  description: Description of the rule.
  returned: success
  type: str
  sample: http load balancer rule
protocol:
  description: Protocol of the rule.
  returned: success
  type: str
  sample: tcp
public_port:
  description: Public port.
  returned: success
  type: int
  sample: 80
private_port:
  description: Private IP address.
  returned: success
  type: int
  sample: 80
public_ip:
  description: Public IP address.
  returned: success
  type: str
  sample: 1.2.3.4
tags:
  description: List of resource tags associated with the rule.
  returned: success
  type: list
  sample: '[ { "key": "foo", "value": "bar" } ]'
state:
  description: State of the rule.
  returned: success
  type: str
  sample: Add
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackLBRule(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackLBRule, self).__init__(module)
        self.returns = {
            'publicip': 'public_ip',
            'algorithm': 'algorithm',
            'cidrlist': 'cidr',
            'protocol': 'protocol',
        }
        # these values will be casted to int
        self.returns_to_int = {
            'publicport': 'public_port',
            'privateport': 'private_port',
        }

    def get_rule(self, **kwargs):
        rules = self.query_api('listLoadBalancerRules', **kwargs)
        if rules:
            return rules['loadbalancerrule'][0]

    def _get_common_args(self):
        return {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'zoneid': self.get_zone(key='id') if self.module.params.get('zone') else None,
            'publicipid': self.get_ip_address(key='id'),
            'name': self.module.params.get('name'),
        }

    def present_lb_rule(self):
        required_params = [
            'algorithm',
            'private_port',
            'public_port',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        args = self._get_common_args()
        rule = self.get_rule(**args)
        if rule:
            rule = self._update_lb_rule(rule)
        else:
            rule = self._create_lb_rule(rule)

        if rule:
            rule = self.ensure_tags(resource=rule, resource_type='LoadBalancer')
        return rule

    def _create_lb_rule(self, rule):
        self.result['changed'] = True
        if not self.module.check_mode:
            args = self._get_common_args()
            args.update({
                'algorithm': self.module.params.get('algorithm'),
                'privateport': self.module.params.get('private_port'),
                'publicport': self.module.params.get('public_port'),
                'cidrlist': self.module.params.get('cidr'),
                'description': self.module.params.get('description'),
                'protocol': self.module.params.get('protocol'),
            })
            res = self.query_api('createLoadBalancerRule', **args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                rule = self.poll_job(res, 'loadbalancer')
        return rule

    def _update_lb_rule(self, rule):
        args = {
            'id': rule['id'],
            'algorithm': self.module.params.get('algorithm'),
            'description': self.module.params.get('description'),
        }
        if self.has_changed(args, rule):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('updateLoadBalancerRule', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    rule = self.poll_job(res, 'loadbalancer')
        return rule

    def absent_lb_rule(self):
        args = self._get_common_args()
        rule = self.get_rule(**args)
        if rule:
            self.result['changed'] = True
        if rule and not self.module.check_mode:
            res = self.query_api('deleteLoadBalancerRule', id=rule['id'])

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                self.poll_job(res, 'loadbalancer')
        return rule


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        description=dict(),
        algorithm=dict(choices=['source', 'roundrobin', 'leastconn'], default='source'),
        private_port=dict(type='int'),
        public_port=dict(type='int'),
        protocol=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        ip_address=dict(required=True, aliases=['public_ip']),
        cidr=dict(),
        project=dict(),
        open_firewall=dict(type='bool', default=False),
        tags=dict(type='list', aliases=['tag']),
        zone=dict(),
        domain=dict(),
        account=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_lb_rule = AnsibleCloudStackLBRule(module)

    state = module.params.get('state')
    if state in ['absent']:
        rule = acs_lb_rule.absent_lb_rule()
    else:
        rule = acs_lb_rule.present_lb_rule()

    result = acs_lb_rule.get_result(rule)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
