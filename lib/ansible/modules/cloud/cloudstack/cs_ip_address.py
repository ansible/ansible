#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, Darren Worrall <darren@iweb.co.uk>
# Copyright (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_ip_address
short_description: Manages public IP address associations on Apache CloudStack based clouds.
description:
    - Acquires and associates a public IP to an account or project.
    - Due to API limitations this is not an idempotent call, so be sure to only
      conditionally call this when I(state=present).
    - Tagging the IP address can also make the call idempotent.
version_added: '2.0'
author:
    - Darren Worrall (@dazworrall)
    - René Moser (@resmo)
options:
  ip_address:
    description:
      - Public IP address.
      - Required if I(state=absent) and I(tags) is not set.
    type: str
  domain:
    description:
      - Domain the IP address is related to.
    type: str
  network:
    description:
      - Network the IP address is related to.
      - Mutually exclusive with I(vpc).
    type: str
  vpc:
    description:
      - VPC the IP address is related to.
      - Mutually exclusive with I(network).
    type: str
    version_added: '2.2'
  account:
    description:
      - Account the IP address is related to.
    type: str
  project:
    description:
      - Name of the project the IP address is related to.
    type: str
  zone:
    description:
      - Name of the zone in which the IP address is in.
      - If not set, default zone is used.
    type: str
  state:
    description:
      - State of the IP address.
    type: str
    default: present
    choices: [ present, absent ]
  tags:
    description:
      - List of tags. Tags are a list of dictionaries having keys I(key) and I(value).
      - Tags can be used as an unique identifier for the IP Addresses.
      - In this case, at least one of them must be unique to ensure idempontency.
    type: list
    aliases: [ tag ]
    version_added: '2.6'
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Associate an IP address conditonally
  cs_ip_address:
    network: My Network
  register: ip_address
  when: instance.public_ip is undefined
  delegate_to: localhost

- name: Disassociate an IP address
  cs_ip_address:
    ip_address: 1.2.3.4
    state: absent
  delegate_to: localhost

- name: Associate an IP address with tags
  cs_ip_address:
    network: My Network
    tags:
      - key: myCustomID
      - value: 5510c31a-416e-11e8-9013-02000a6b00bf
  register: ip_address
  delegate_to: localhost

- name: Disassociate an IP address with tags
  cs_ip_address:
    state: absent
    tags:
      - key: myCustomID
      - value: 5510c31a-416e-11e8-9013-02000a6b00bf
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the Public IP address.
  returned: success
  type: str
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
ip_address:
  description: Public IP address.
  returned: success
  type: str
  sample: 1.2.3.4
zone:
  description: Name of zone the IP address is related to.
  returned: success
  type: str
  sample: ch-gva-2
project:
  description: Name of project the IP address is related to.
  returned: success
  type: str
  sample: Production
account:
  description: Account the IP address is related to.
  returned: success
  type: str
  sample: example account
domain:
  description: Domain the IP address is related to.
  returned: success
  type: str
  sample: example domain
tags:
  description: List of resource tags associated with the IP address.
  returned: success
  type: dict
  sample: '[ { "key": "myCustomID", "value": "5510c31a-416e-11e8-9013-02000a6b00bf" } ]'
  version_added: '2.6'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackIPAddress(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackIPAddress, self).__init__(module)
        self.returns = {
            'ipaddress': 'ip_address',
        }

    def get_ip_address(self, key=None):
        if self.ip_address:
            return self._get_by_key(key, self.ip_address)
        args = {
            'ipaddress': self.module.params.get('ip_address'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'vpcid': self.get_vpc(key='id'),
        }
        ip_addresses = self.query_api('listPublicIpAddresses', **args)

        if ip_addresses:
            tags = self.module.params.get('tags')
            for ip_addr in ip_addresses['publicipaddress']:
                if ip_addr['ipaddress'] == args['ipaddress'] != '':
                    self.ip_address = ip_addresses['publicipaddress'][0]
                elif tags:
                    if sorted([tag for tag in tags if tag in ip_addr['tags']]) == sorted(tags):
                        self.ip_address = ip_addr
        return self._get_by_key(key, self.ip_address)

    def present_ip_address(self):
        ip_address = self.get_ip_address()

        if not ip_address:
            ip_address = self.associate_ip_address(ip_address)

        if ip_address:
            ip_address = self.ensure_tags(resource=ip_address, resource_type='publicipaddress')

        return ip_address

    def associate_ip_address(self, ip_address):
        self.result['changed'] = True
        args = {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            # For the VPC case networkid is irrelevant, special case and we have to ignore it here.
            'networkid': self.get_network(key='id') if not self.module.params.get('vpc') else None,
            'zoneid': self.get_zone(key='id'),
            'vpcid': self.get_vpc(key='id'),
        }
        ip_address = None
        if not self.module.check_mode:
            res = self.query_api('associateIpAddress', **args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                ip_address = self.poll_job(res, 'ipaddress')
        return ip_address

    def disassociate_ip_address(self):
        ip_address = self.get_ip_address()
        if not ip_address:
            return None
        if ip_address['isstaticnat']:
            self.module.fail_json(msg="IP address is allocated via static nat")

        self.result['changed'] = True
        if not self.module.check_mode:
            self.module.params['tags'] = []
            ip_address = self.ensure_tags(resource=ip_address, resource_type='publicipaddress')

            res = self.query_api('disassociateIpAddress', id=ip_address['id'])

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                self.poll_job(res, 'ipaddress')
        return ip_address


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        ip_address=dict(required=False),
        state=dict(choices=['present', 'absent'], default='present'),
        vpc=dict(),
        network=dict(),
        zone=dict(),
        domain=dict(),
        account=dict(),
        project=dict(),
        tags=dict(type='list', aliases=['tag']),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        required_if=[
            ('state', 'absent', ['ip_address', 'tags'], True),
        ],
        mutually_exclusive=(
            ['vpc', 'network'],
        ),
        supports_check_mode=True
    )

    acs_ip_address = AnsibleCloudStackIPAddress(module)

    state = module.params.get('state')
    if state in ['absent']:
        ip_address = acs_ip_address.disassociate_ip_address()
    else:
        ip_address = acs_ip_address.present_ip_address()

    result = acs_ip_address.get_result(ip_address)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
