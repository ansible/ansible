#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Abhijeet Kasurde (akasurde@redhat.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: ipa_dnsrecord
author: Abhijeet Kasurde (@akasurde)
short_description: Manage FreeIPA DNS records
description:
- Add, modify and delete an IPA DNS Record using IPA API
options:
  zone_name:
    description:
    - The DNS zone name to which DNS record needs to be managed.
    required: true
  record_name:
    description:
    - The DNS record name to manage.
    required: true
    aliases: ["name"]
  record_type:
    description:
    - The type of DNS record name
    - Currently, 'A', 'AAAA' is supported
    required: false
    default: 'A'
    choices: ['A', 'AAAA']
  record_ip:
    description:
    - Manage DNS record name with this IP address.
    required: true
  state:
    description: State to ensure
    required: false
    default: present
    choices: ["present", "absent"]
  ipa_port:
    description: Port of IPA server
    required: false
    default: 443
  ipa_host:
    description: IP or hostname of IPA server
    required: false
    default: ipa.example.com
  ipa_user:
    description: Administrative account used on IPA server
    required: false
    default: admin
  ipa_pass:
    description: Password of administrative user
    required: true
  ipa_prot:
    description: Protocol used by IPA server
    required: false
    default: https
    choices: ["http", "https"]
  validate_certs:
    description:
    - This only applies if C(ipa_prot) is I(https).
    - If set to C(no), the SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    required: false
    default: true
version_added: "2.4"
'''

EXAMPLES = '''
# Ensure dns record is present
- ipa_dnsrecord:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    zone_name: example.com
    record_name: vm-001
    record_type: 'AAAA'
    record_ip: '::1'

# Ensure that dns record is removed
- ipa_dnsrecord:
    name: host01
    zone_name: example.com
    record_type: 'AAAA'
    record_ip: '::1'
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    state: absent
'''

RETURN = '''
dnsrecord:
  description: DNS record as returned by IPA API.
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient
from ansible.module_utils._text import to_native


class DNSRecordIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(DNSRecordIPAClient, self).__init__(module, host, port, protocol)

    def dnsrecord_find(self, zone_name, record_name):
        return self._post_json(method='dnsrecord_find', name=zone_name, item={'idnsname': record_name})

    def dnsrecord_add(self, zone_name=None, record_name=None, details=None):
        item = dict(idnsname=record_name)
        if details['record_type'] == 'A':
            item.update(a_part_ip_address=details['record_ip'])
        elif details['record_type'] == 'AAAA':
            item.update(aaaa_part_ip_address=details['record_ip'])

        return self._post_json(method='dnsrecord_add', name=zone_name, item=item)

    def dnsrecord_mod(self, zone_name=None, record_name=None, details=None):
        item = get_dnsrecord_dict(details)
        item.update(idnsname=record_name)
        return self._post_json(method='dnsrecord_mod', name=zone_name, item=item)

    def dnsrecord_del(self, zone_name=None, record_name=None, details=None):
        item = get_dnsrecord_dict(details)
        item.update(idnsname=record_name)
        return self._post_json(method='dnsrecord_del', name=zone_name, item=item)


def get_dnsrecord_dict(details=None):
    module_dnsrecord = dict()
    if details['record_type'] == 'A' and details['record_ip']:
        module_dnsrecord.update(arecord=details['record_ip'])
    elif details['record_type'] == 'AAAA' and details['record_ip']:
        module_dnsrecord.update(aaaarecord=details['record_ip'])
    return module_dnsrecord


def get_dnsrecord_diff(client, ipa_dnsrecord, module_dnsrecord):
    details = get_dnsrecord_dict(module_dnsrecord)
    return client.get_diff(ipa_data=ipa_dnsrecord, module_data=details)


def ensure(module, client):
    zone_name = module.params['zone_name']
    record_name = module.params['record_name']
    state = module.params['state']

    ipa_dnsrecord = client.dnsrecord_find(zone_name, record_name)
    module_dnsrecord = dict(record_type=module.params['record_type'],
                            record_ip=module.params['record_ip'])

    changed = False
    if state == 'present':
        if not ipa_dnsrecord:
            changed = True
            if not module.check_mode:
                client.dnsrecord_add(zone_name=zone_name,
                                     record_name=record_name,
                                     details=module_dnsrecord)
        else:
            diff = get_dnsrecord_diff(client, ipa_dnsrecord, module_dnsrecord)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    client.dnsrecord_mod(zone_name=zone_name,
                                         record_name=record_name,
                                         details=module_dnsrecord)
    else:
        if ipa_dnsrecord:
            changed = True
            if not module.check_mode:
                client.dnsrecord_del(zone_name=zone_name,
                                     record_name=record_name,
                                     details=module_dnsrecord)

    return changed, client.dnsrecord_find(zone_name, record_name)


def main():
    record_types = ['A', 'AAAA']
    module = AnsibleModule(
        argument_spec=dict(
            zone_name=dict(type='str', required=True),
            record_name=dict(type='str', required=True, aliases=['name']),
            record_type=dict(type='str', required=False, default='A', choices=record_types),
            record_ip=dict(type='str', required=True),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
            ipa_prot=dict(type='str', required=False, default='https', choices=['http', 'https']),
            ipa_host=dict(type='str', required=False, default='ipa.example.com'),
            ipa_port=dict(type='int', required=False, default=443),
            ipa_user=dict(type='str', required=False, default='admin'),
            ipa_pass=dict(type='str', required=True, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
        ),
        supports_check_mode=True,
    )

    client = DNSRecordIPAClient(module=module,
                                host=module.params['ipa_host'],
                                port=module.params['ipa_port'],
                                protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, record = ensure(module, client)
        module.exit_json(changed=changed, record=record)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
