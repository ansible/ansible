#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Abhijeet Kasurde (akasurde@redhat.com)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: ipa_dnsrecord
author: Abhijeet Kasurde (@Akasurde)
short_description: Manage FreeIPA DNS records
description:
- Add, modify and delete an IPA DNS Record using IPA API.
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
    - The type of DNS record name.
    - Currently, 'A', 'AAAA', 'A6', 'CNAME', 'DNAME', 'PTR', 'TXT', 'SRV' and 'MX' are supported.
    - "'A6', 'CNAME', 'DNAME' and 'TXT' are added in version 2.5."
    - "'SRV' and 'MX' are added in version 2.8."
    required: false
    default: 'A'
    choices: ['A', 'AAAA', 'A6', 'CNAME', 'DNAME', 'PTR', 'TXT', 'SRV', 'MX']
  record_value:
    description:
    - Manage DNS record name with this value.
    - In the case of 'A' or 'AAAA' record types, this will be the IP address.
    - In the case of 'A6' record type, this will be the A6 Record data.
    - In the case of 'CNAME' record type, this will be the hostname.
    - In the case of 'DNAME' record type, this will be the DNAME target.
    - In the case of 'PTR' record type, this will be the hostname.
    - In the case of 'TXT' record type, this will be a text.
    - In the case of 'SRV' record type, this will be a service record.
    - In the case of 'MX' record type, this will be a mail exchanger record.
    required: true
  record_ttl:
    description:
    - Set the TTL for the record.
    - Applies only when adding a new or changing the value of record_value.
    version_added: "2.7"
    required: false
  state:
    description: State to ensure
    required: false
    default: present
    choices: ["present", "absent"]
extends_documentation_fragment: ipa.documentation
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
    record_value: '::1'

# Ensure that dns record exists with a TTL
- ipa_dnsrecord:
    name: host02
    zone_name: example.com
    record_type: 'AAAA'
    record_value: '::1'
    record_ttl: 300
    ipa_host: ipa.example.com
    ipa_pass: topsecret
    state: present

# Ensure a PTR record is present
- ipa_dnsrecord:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    zone_name: 2.168.192.in-addr.arpa
    record_name: 5
    record_type: 'PTR'
    record_value: 'internal.ipa.example.com'

# Ensure a TXT record is present
- ipa_dnsrecord:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    zone_name: example.com
    record_name: _kerberos
    record_type: 'TXT'
    record_value: 'EXAMPLE.COM'

# Ensure an SRV record is present
- ipa_dnsrecord:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    zone_name: example.com
    record_name: _kerberos._udp.example.com
    record_type: 'SRV'
    record_value: '10 50 88 ipa.example.com'

# Ensure an MX record is present
- ipa_dnsrecord:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    zone_name: example.com
    record_name: '@'
    record_type: 'MX'
    record_value: '1 mailserver.example.com'

# Ensure that dns record is removed
- ipa_dnsrecord:
    name: host01
    zone_name: example.com
    record_type: 'AAAA'
    record_value: '::1'
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
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class DNSRecordIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(DNSRecordIPAClient, self).__init__(module, host, port, protocol)

    def dnsrecord_find(self, zone_name, record_name):
        if record_name == '@':
            return self._post_json(method='dnsrecord_show', name=zone_name, item={'idnsname': record_name, 'all': True})
        else:
            return self._post_json(method='dnsrecord_find', name=zone_name, item={'idnsname': record_name, 'all': True})

    def dnsrecord_add(self, zone_name=None, record_name=None, details=None):
        item = dict(idnsname=record_name)
        if details['record_type'] == 'A':
            item.update(a_part_ip_address=details['record_value'])
        elif details['record_type'] == 'AAAA':
            item.update(aaaa_part_ip_address=details['record_value'])
        elif details['record_type'] == 'A6':
            item.update(a6_part_data=details['record_value'])
        elif details['record_type'] == 'CNAME':
            item.update(cname_part_hostname=details['record_value'])
        elif details['record_type'] == 'DNAME':
            item.update(dname_part_target=details['record_value'])
        elif details['record_type'] == 'PTR':
            item.update(ptr_part_hostname=details['record_value'])
        elif details['record_type'] == 'TXT':
            item.update(txtrecord=details['record_value'])
        elif details['record_type'] == 'SRV':
            item.update(srvrecord=details['record_value'])
        elif details['record_type'] == 'MX':
            item.update(mxrecord=details['record_value'])

        if details.get('record_ttl'):
            item.update(dnsttl=details['record_ttl'])

        return self._post_json(method='dnsrecord_add', name=zone_name, item=item)

    def dnsrecord_mod(self, zone_name=None, record_name=None, details=None):
        item = get_dnsrecord_dict(details)
        item.update(idnsname=record_name)
        if details.get('record_ttl'):
            item.update(dnsttl=details['record_ttl'])
        return self._post_json(method='dnsrecord_mod', name=zone_name, item=item)

    def dnsrecord_del(self, zone_name=None, record_name=None, details=None):
        item = get_dnsrecord_dict(details)
        item.update(idnsname=record_name)
        return self._post_json(method='dnsrecord_del', name=zone_name, item=item)


def get_dnsrecord_dict(details=None):
    module_dnsrecord = dict()
    if details['record_type'] == 'A' and details['record_value']:
        module_dnsrecord.update(arecord=details['record_value'])
    elif details['record_type'] == 'AAAA' and details['record_value']:
        module_dnsrecord.update(aaaarecord=details['record_value'])
    elif details['record_type'] == 'A6' and details['record_value']:
        module_dnsrecord.update(a6record=details['record_value'])
    elif details['record_type'] == 'CNAME' and details['record_value']:
        module_dnsrecord.update(cnamerecord=details['record_value'])
    elif details['record_type'] == 'DNAME' and details['record_value']:
        module_dnsrecord.update(dnamerecord=details['record_value'])
    elif details['record_type'] == 'PTR' and details['record_value']:
        module_dnsrecord.update(ptrrecord=details['record_value'])
    elif details['record_type'] == 'TXT' and details['record_value']:
        module_dnsrecord.update(txtrecord=details['record_value'])
    elif details['record_type'] == 'SRV' and details['record_value']:
        module_dnsrecord.update(srvrecord=details['record_value'])
    elif details['record_type'] == 'MX' and details['record_value']:
        module_dnsrecord.update(mxrecord=details['record_value'])

    if details.get('record_ttl'):
        module_dnsrecord.update(dnsttl=details['record_ttl'])

    return module_dnsrecord


def get_dnsrecord_diff(client, ipa_dnsrecord, module_dnsrecord):
    details = get_dnsrecord_dict(module_dnsrecord)
    return client.get_diff(ipa_data=ipa_dnsrecord, module_data=details)


def ensure(module, client):
    zone_name = module.params['zone_name']
    record_name = module.params['record_name']
    record_ttl = module.params.get('record_ttl')
    state = module.params['state']

    ipa_dnsrecord = client.dnsrecord_find(zone_name, record_name)

    module_dnsrecord = dict(
        record_type=module.params['record_type'],
        record_value=module.params['record_value'],
        record_ttl=to_native(record_ttl, nonstring='passthru'),
    )

    # ttl is not required to change records
    if module_dnsrecord['record_ttl'] is None:
        module_dnsrecord.pop('record_ttl')

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
    record_types = ['A', 'AAAA', 'A6', 'CNAME', 'DNAME', 'PTR', 'TXT', 'SRV', 'MX']
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        zone_name=dict(type='str', required=True),
        record_name=dict(type='str', aliases=['name'], required=True),
        record_type=dict(type='str', default='A', choices=record_types),
        record_value=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        record_ttl=dict(type='int', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = DNSRecordIPAClient(
        module=module,
        host=module.params['ipa_host'],
        port=module.params['ipa_port'],
        protocol=module.params['ipa_prot']
    )

    try:
        client.login(
            username=module.params['ipa_user'],
            password=module.params['ipa_pass']
        )
        changed, record = ensure(module, client)
        module.exit_json(changed=changed, record=record)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
