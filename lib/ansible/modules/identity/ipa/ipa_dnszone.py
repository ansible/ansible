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


DOCUMENTATION = r'''
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
    type: str
  state:
    description: State to ensure
    required: false
    default: present
    choices: ["absent", "present"]
    type: str
  dynamicupdate:
    description: Apply dynamic update to zone
    required: false
    default: false
    type: bool
    version_added: "2.9"
  ptrsync:
    description: Allow ptr sync on zone
    required: false
    default: false
    type: bool
    version_added: "2.10"
extends_documentation_fragment: ipa.documentation
version_added: "2.5"
'''

EXAMPLES = r'''
- name: Ensure dns zone is present
  ipa_dnszone:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    zone_name: example.com

- name: Ensure dns zone is present and is dynamic update
  ipa_dnszone:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    zone_name: example.com
    dynamicupdate: true

- name: Ensure dns zone is present and allows ptr sync
  ipa_dnszone:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    zone_name: example.com
    ptrsync: true

- name: Ensure that dns zone is removed
  ipa_dnszone:
    zone_name: example.com
    ipa_host: localhost
    ipa_user: admin
    ipa_pass: topsecret
    state: absent
'''

RETURN = r'''
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

    def dnszone_find(self, zone_name, details=None):
        itens = {'all': True, 'idnsname': zone_name}
        if details is not None:
            itens.update(details)

        return self._post_json(
            method='dnszone_find',
            name=zone_name,
            item=itens
        )

    def dnszone_add(self, zone_name=None, details=None):
        itens = {}
        if details is not None:
            itens.update(details)

        return self._post_json(
            method='dnszone_add',
            name=zone_name,
            item=itens
        )

    def dnszone_mod(self, zone_name=None, details=None):
        itens = {}
        if details is not None:
            itens.update(details)

        return self._post_json(
            method='dnszone_mod',
            name=zone_name,
            item=itens
        )

    def dnszone_del(self, zone_name=None, record_name=None, details=None):
        return self._post_json(
            method='dnszone_del', name=zone_name, item={})


def get_dnszone_dict(idnsallowdynupdate=None, idnsallowsyncptr=None):
    dnszone = {}
    if idnsallowdynupdate is not None:
        dnszone['idnsallowdynupdate'] = idnsallowdynupdate
    if idnsallowsyncptr is not None:
        dnszone['idnsallowsyncptr'] = idnsallowsyncptr

    return dnszone


def get_dnszone_diff(client, ipa_dnszone, module_dnszone):
    if 'idnsallowdynupdate' in ipa_dnszone:
        ipa_dnszone['idnsallowdynupdate'] = (ipa_dnszone['idnsallowdynupdate'][0].lower() == 'true')
    if 'idnsallowsyncptr' in ipa_dnszone:
        ipa_dnszone['idnsallowsyncptr'] = (ipa_dnszone['idnsallowsyncptr'][0].lower() == 'true')

    result = client.get_diff(ipa_data=ipa_dnszone, module_data=module_dnszone)
    return result


def ensure(module, client):
    zone_name = module.params['zone_name']
    state = module.params['state']

    module_dnszone = get_dnszone_dict(idnsallowdynupdate=module.params['dynamicupdate'],
                                      idnsallowsyncptr=module.params['ptrsync'])

    ipa_dnszone = client.dnszone_find(zone_name)

    changed = False
    if state == 'present':
        if not ipa_dnszone:
            changed = True
            if not module.check_mode:
                ipa_dnszone = client.dnszone_add(zone_name=zone_name, details=module_dnszone)
        else:
            diff = get_dnszone_diff(client, ipa_dnszone, module_dnszone)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    ipa_dnszone = client.dnszone_mod(zone_name=zone_name, details=module_dnszone)
    else:
        if ipa_dnszone:
            changed = True
            if not module.check_mode:
                ipa_dnszone = client.dnszone_del(zone_name=zone_name)

    return changed, ipa_dnszone


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(zone_name=dict(type='str', required=True),
                         state=dict(type='str', default='present', choices=['present', 'absent']),
                         dynamicupdate=dict(type='bool', required=False, default=False),
                         ptrsync=dict(type='bool', required=False, default=False),
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
