#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_ca
version_added: "2.8"
short_description: Manage pfSense Certificate Authorities
description:
  >
    Manage pfSense Certificate Authorities
author: Orion Poplawski (@opoplawski)
notes:
options:
  name:
    description: The name of the Certificate Authority
    required: true
  state:
    description: State in which to leave the Certificate Authority
    required: true
    choices: [ "present", "absent" ]
  certificate:
    description: The certificate for the Certificate Authority
    required: true
  crl:
    description: The Certificate Revocation List for the Certificate Authority
    required: false
"""

EXAMPLES = """
- name: Add AD Certificate Authority
  pfsense_ca:
    name: AD CA
    certificate: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tDQpNSUlGcXpDQ0E1T2dB...
    state: present

- name: Remove AD Certificate Authority
  pfsense_ca:
    name: AD CA
    state: absent
"""

RETURN = """

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.networking.pfsense.pfsense import PFSenseModule


class pfSenseCA(object):

    def __init__(self, module):
        self.module = module
        self.pfsense = PFSenseModule(module)
        self.cas = self.pfsense.get_elements('ca')
        self.crls = self.pfsense.get_elements('crl')

    def _find_ca(self, name):
        found = None
        i = 0
        for ca in self.cas:
            i = self.pfsense.get_index(ca)
            if ca.find('descr').text == name:
                found = ca
                break
        return (found, i)

    def _find_crl(self, caref):
        found = None
        i = 0
        for crl in self.crls:
            i = self.pfsense.get_index(crl)
            if crl.find('caref').text == caref:
                found = crl
                break
        return (found, i)

    def add(self, ca):
        ca_elt, i = self._find_ca(ca['descr'])
        changed = False
        crl = {}
        diff = {}
        if 'crl' in ca:
            crl['method'] = 'existing'
            crl['text'] = ca.pop('crl')
        if ca_elt is None:
            diff['before'] = ''
            changed = True
            ca_elt = self.pfsense.new_element('ca')
            ca['refid'] = self.pfsense.uniqid()
            if 'text' in crl:
                crl_elt = self.pfsense.new_element('crl')
                crl['refid'] = self.pfsense.uniqid()
                crl['descr'] = ca['descr'] + ' CRL'
                crl['caref'] = ca['refid']
                self.pfsense.copy_dict_to_element(crl, crl_elt)
                self.pfsense.root.insert(i + 1, crl_elt)
            self.pfsense.copy_dict_to_element(ca, ca_elt)
            self.pfsense.root.insert(i + 1, ca_elt)
            descr = 'ansible pfsense_ca added %s' % (ca['descr'])
        else:
            diff['before'] = self.pfsense.element_to_dict(ca_elt)
            if 'text' in crl:
                crl_elt, crl_index = self._find_crl(ca_elt.find('refid').text)
                if crl_elt is None:
                    changed = True
                    crl_elt = self.pfsense.new_element('crl')
                    crl['refid'] = self.pfsense.uniqid()
                    crl['descr'] = ca['descr'] + ' CRL'
                    crl['caref'] = ca_elt.find('refid').text
                    self.pfsense.copy_dict_to_element(crl, crl_elt)
                    self.pfsense.root.insert(crl_index + 1, crl_elt)
                else:
                    diff['before']['crl'] = crl_elt.find('text').text
                    changed = self.pfsense.copy_dict_to_element(crl, crl_elt)
            if self.pfsense.copy_dict_to_element(ca, ca_elt):
                changed = True
            descr = 'ansible pfsense_ca updated "%s"' % (ca['descr'])
        if changed and not self.module.check_mode:
            self.pfsense.write_config(descr=descr)
        diff['after'] = self.pfsense.element_to_dict(ca_elt)
        if 'text' in crl:
            diff['after']['crl'] = crl['text']
        self.module.exit_json(changed=changed, diff=diff)

    def remove(self, ca):
        ca_elt, _ = self._find_ca(ca['descr'])
        changed = False
        diff = {}
        diff['after'] = {}
        if ca_elt is not None:
            changed = True
            diff['before'] = self.pfsense.element_to_dict(ca_elt)
            crl_elt, _ = self._find_crl(ca_elt.find('refid').text)
            self.cas.remove(ca_elt)
            if crl_elt is not None:
                diff['before']['crl'] = crl_elt.find('text').text
                self.crls.remove(crl_elt)
        else:
            diff['before'] = {}
        if changed and not self.module.check_mode:
            self.pfsense.write_config(descr='ansible pfsense_ca removed "%s"' % (ca['descr']))
        self.module.exit_json(changed=changed, diff=diff)


def main():
    module = AnsibleModule(
        argument_spec={
            'name': {'required': True, 'type': 'str'},
            'state': {
                'required': True,
                'choices': ['present', 'absent']
            },
            'certificate': {'required': False, 'type': 'str'},
            'crl': {'required': False, 'default': None, 'type': 'str'},
        },
        required_if=[
            ["state", "present", ["certificate"]],
        ],
        supports_check_mode=True)

    pfca = pfSenseCA(module)

    ca = dict()
    ca['descr'] = module.params['name']
    state = module.params['state']
    if state == 'absent':
        pfca.remove(ca)
    elif state == 'present':
        ca['crt'] = module.params['certificate']
        ca['crl'] = module.params['crl']
        pfca.add(ca)


if __name__ == '__main__':
    main()
