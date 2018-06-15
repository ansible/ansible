#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Fran Fitzpatrick (francis.x.fitzpatrick@gmail.com)
# Borrowed heavily from other work by Abhijeet Kasurde (akasurde@redhat.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_dnszone
author: Fran Fitzpatrick (@fxfitz)
short_description: Manage FreeIPA DNS Zones
description:
- Add and delete an IPA DNS Zones using IPA API
options:
  zone_name:
    description:
    - The DNS zone name to which needs to be managed.
    required: true
  state:
    description: State to ensure
    required: false
    default: present
    choices: ["present", "absent"]
extends_documentation_fragment: ipa.documentation
version_added: "2.5"
'''

EXAMPLES = '''
# Ensure dns zone is present
- ipa_dnszone:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    zone_name: example.com

# Ensure that dns zone is removed
- ipa_dnszone:
    zone_name: example.com
    ipa_host: localhost
    ipa_user: admin
    ipa_pass: topsecret
    state: absent
'''

RETURN = '''
zone:
  description: DNS zone as returned by IPA API.
  returned: always
  type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class DNSZoneIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(DNSZoneIPAClient, self).__init__(module, host, port, protocol)

    def dnszone_find(self, zone_name):
        return self._post_json(
            method='dnszone_find',
            name=zone_name,
            item={'idnsname': zone_name}
        )

    def dnszone_add(self, zone_name=None, details=None):
        return self._post_json(
            method='dnszone_add',
            name=zone_name,
            item={}
        )

    def dnszone_del(self, zone_name=None, record_name=None, details=None):
        return self._post_json(
            method='dnszone_del', name=zone_name, item={})


def ensure(module, client):
    zone_name = module.params['zone_name']
    state = module.params['state']

    ipa_dnszone = client.dnszone_find(zone_name)

    changed = False
    if state == 'present':
        if not ipa_dnszone:
            changed = True
            if not module.check_mode:
                client.dnszone_add(zone_name=zone_name)
        else:
            changed = False
    else:
        if ipa_dnszone:
            changed = True
            if not module.check_mode:
                client.dnszone_del(zone_name=zone_name)

    return changed, client.dnszone_find(zone_name)


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(zone_name=dict(type='str', required=True),
                         state=dict(type='str', default='present', choices=['present', 'absent']),
                         )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )

    client = DNSZoneIPAClient(
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
        changed, zone = ensure(module, client)
        module.exit_json(changed=changed, zone=zone)
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
