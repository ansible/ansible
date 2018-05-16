#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017, Abhijeet Kasurde (akasurde@redhat.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_subca
author: Abhijeet Kasurde (@Akasurde)
short_description: Manage FreeIPA Lightweight Sub Certificate Authorities.
description:
- Add, modify, enable, disable and delete an IPA Lightweight Sub Certificate Authorities using IPA API.
version_added: "2.5"
options:
  subca_name:
    description:
    - The Sub Certificate Authority name which needs to be managed.
    required: true
  subca_subject:
    description:
    - The Sub Certificate Authority's Subject. e.g., 'CN=SampleSubCA1,O=testrelm.test'
    required: true
  subca_desc:
    description:
    - The Sub Certificate Authority's description.
    required: true
  state:
    description:
    - State to ensure
    - State 'disable' and 'enable' is available for FreeIPA 4.4.2 version and onwards
    required: false
    default: present
    choices: ["present", "absent", "enable", "disable"]
extends_documentation_fragment: ipa.documentation
'''

EXAMPLES = '''
# Ensure IPA Sub CA is present
- ipa_subca:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: present
    subca_name: AnsibleSubCA1
    subca_subject: 'CN=AnsibleSubCA1,O=example.com'
    subca_desc: Ansible Sub CA

# Ensure that IPA Sub CA is removed
- ipa_subca:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: absent
    subca_name: AnsibleSubCA1

# Ensure that IPA Sub CA is disabled
- ipa_subca:
    ipa_host: spider.example.com
    ipa_pass: Passw0rd!
    state: disable
    subca_name: AnsibleSubCA1
'''

RETURN = '''
subca:
  description: IPA Sub CA record as returned by IPA API.
  returned: always
  type: dict
'''

from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class SubCAIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(SubCAIPAClient, self).__init__(module, host, port, protocol)

    def subca_find(self, subca_name):
        return self._post_json(method='ca_find', name=subca_name, item=None)

    def subca_add(self, subca_name=None, subject_dn=None, details=None):
        item = dict(ipacasubjectdn=subject_dn)
        subca_desc = details.get('description', None)
        if subca_desc is not None:
            item.update(description=subca_desc)
        return self._post_json(method='ca_add', name=subca_name, item=item)

    def subca_mod(self, subca_name=None, diff=None, details=None):
        item = get_subca_dict(details)
        for change in diff:
            update_detail = dict()
            if item[change] is not None:
                update_detail.update(setattr="{0}={1}".format(change, item[change]))
                self._post_json(method='ca_mod', name=subca_name, item=update_detail)

    def subca_del(self, subca_name=None):
        return self._post_json(method='ca_del', name=subca_name)

    def subca_disable(self, subca_name=None):
        return self._post_json(method='ca_disable', name=subca_name)

    def subca_enable(self, subca_name=None):
        return self._post_json(method='ca_enable', name=subca_name)


def get_subca_dict(details=None):
    module_subca = dict()
    if details['description'] is not None:
        module_subca['description'] = details['description']
    if details['subca_subject'] is not None:
        module_subca['ipacasubjectdn'] = details['subca_subject']
    return module_subca


def get_subca_diff(client, ipa_subca, module_subca):
    details = get_subca_dict(module_subca)
    return client.get_diff(ipa_data=ipa_subca, module_data=details)


def ensure(module, client):
    subca_name = module.params['subca_name']
    subca_subject_dn = module.params['subca_subject']
    subca_desc = module.params['subca_desc']

    state = module.params['state']

    ipa_subca = client.subca_find(subca_name)
    module_subca = dict(description=subca_desc,
                        subca_subject=subca_subject_dn)

    changed = False
    if state == 'present':
        if not ipa_subca:
            changed = True
            if not module.check_mode:
                client.subca_add(subca_name=subca_name, subject_dn=subca_subject_dn, details=module_subca)
        else:
            diff = get_subca_diff(client, ipa_subca, module_subca)
            # IPA does not allow to modify Sub CA's subject DN
            # So skip it for now.
            if 'ipacasubjectdn' in diff:
                diff.remove('ipacasubjectdn')
                del module_subca['subca_subject']

            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    client.subca_mod(subca_name=subca_name, diff=diff, details=module_subca)
    elif state == 'absent':
        if ipa_subca:
            changed = True
            if not module.check_mode:
                client.subca_del(subca_name=subca_name)
    elif state == 'disable':
        ipa_version = client.get_ipa_version()
        if LooseVersion(ipa_version) < LooseVersion('4.4.2'):
            module.fail_json(msg="Current version of IPA server [%s] does not support 'CA disable' option. Please upgrade to "
                                 "version greater than 4.4.2")
        if ipa_subca:
            changed = True
            if not module.check_mode:
                client.subca_disable(subca_name=subca_name)
    elif state == 'enable':
        ipa_version = client.get_ipa_version()
        if LooseVersion(ipa_version) < LooseVersion('4.4.2'):
            module.fail_json(msg="Current version of IPA server [%s] does not support 'CA enable' option. Please upgrade to "
                                 "version greater than 4.4.2")
        if ipa_subca:
            changed = True
            if not module.check_mode:
                client.subca_enable(subca_name=subca_name)

    return changed, client.subca_find(subca_name)


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(subca_name=dict(type='str', required=True, aliases=['name']),
                         subca_subject=dict(type='str', required=True),
                         subca_desc=dict(type='str'),
                         state=dict(type='str', default='present',
                                    choices=['present', 'absent', 'enabled', 'disabled']),)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,)

    client = SubCAIPAClient(module=module,
                            host=module.params['ipa_host'],
                            port=module.params['ipa_port'],
                            protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, record = ensure(module, client)
        module.exit_json(changed=changed, record=record)
    except Exception as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == '__main__':
    main()
