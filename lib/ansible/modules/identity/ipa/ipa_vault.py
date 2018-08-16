#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Juan Manuel Parrilla <jparrill@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ipa_vault
author: Juan Manuel Parrilla (@jparrill)
short_description: Manage FreeIPA vaults
description:
- Add, modify and delete vaults and secret vaults.
- KRA service should be enabled to use this module.
options:
    cn:
        description:
        - Vault name.
        - Can not be changed as it is the unique identifier.
        required: true
        aliases: ["name"]
    description:
        description:
        - Description.
    ipavaulttype:
        description:
        - Vault types are based on security level.
        default: "symmetric"
        choices: ["standard", "symmetric", "asymmetric"]
        required: true
        aliases: ["vault_type"]
    ipavaultpublickey:
        description:
        - Public key.
        aliases: ["vault_public_key"]
    ipavaultsalt:
        description:
        - Vault Salt.
        aliases: ["vault_salt"]
    username:
        description:
        - Any user can own one or more user vaults.
        - Mutually exclusive with service.
        aliases: ["user"]
    service:
        description:
        - Any service can own one or more service vaults.
        - Mutually exclusive with user.
    state:
        description:
        - State to ensure.
        default: "present"
        choices: ["present", "absent"]
    replace:
        description:
        - Force replace the existant vault on IPA server.
        type: bool
        default: False
        choices: ["True", "False"]
    validate_certs:
        description:
        - Validate IPA server certificates.
        type: bool
        default: true
extends_documentation_fragment: ipa.documentation
version_added: "2.7"
'''

EXAMPLES = '''
# Ensure vault is present
- ipa_vault:
    name: vault01
    vault_type: standard
    user: user01
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Ensure vault is present for Admin user
- ipa_vault:
    name: vault01
    vault_type: standard
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure vault is absent
- ipa_vault:
    name: vault01
    vault_type: standard
    user: user01
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Modify vault if already exists
- ipa_vault:
    name: vault01
    vault_type: standard
    description: "Vault for test"
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    replace: True

# Get vault info if already exists
- ipa_vault:
    name: vault01
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
vault:
  description: Vault as returned by IPA API
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class VaultIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(VaultIPAClient, self).__init__(module, host, port, protocol)

    def vault_find(self, name):
        return self._post_json(method='vault_find', name=None, item={'all': True, 'cn': name})

    def vault_add_internal(self, name, item):
        return self._post_json(method='vault_add_internal', name=name, item=item)

    def vault_mod_internal(self, name, item):
        return self._post_json(method='vault_mod_internal', name=name, item=item)

    def vault_del(self, name):
        return self._post_json(method='vault_del', name=name)


def get_vault_dict(description=None, vault_type=None, vault_salt=None, vault_public_key=None, service=None):
    vault = {}

    if description is not None:
        vault['description'] = description
    if vault_type is not None:
        vault['ipavaulttype'] = vault_type
    if vault_salt is not None:
        vault['ipavaultsalt'] = vault_salt
    if vault_public_key is not None:
        vault['ipavaultpublickey'] = vault_public_key
    if service is not None:
        vault['service'] = service
    return vault


def get_vault_diff(client, ipa_vault, module_vault, module):
    return client.get_diff(ipa_data=ipa_vault, module_data=module_vault)


def ensure(module, client):
    state = module.params['state']
    name = module.params['cn']
    user = module.params['username']
    replace = module.params['replace']

    module_vault = get_vault_dict(description=module.params['description'], vault_type=module.params['ipavaulttype'],
                                  vault_salt=module.params['ipavaultsalt'],
                                  vault_public_key=module.params['ipavaultpublickey'],
                                  service=module.params['service'])
    ipa_vault = client.vault_find(name=name)

    changed = False
    if state == 'present':
        if not ipa_vault:
            # New vault
            changed = True
            if not module.check_mode:
                ipa_vault = client.vault_add_internal(name, item=module_vault)
        else:
            # Already exists
            if replace:
                diff = get_vault_diff(client, ipa_vault, module_vault, module)
                if len(diff) > 0:
                    changed = True
                    if not module.check_mode:
                        data = {}
                        for key in diff:
                            data[key] = module_vault.get(key)
                        client.vault_mod_internal(name=name, item=data)

    else:
        if ipa_vault:
            changed = True
            if not module.check_mode:
                client.vault_del(name)

    return changed, client.vault_find(name=name)


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(cn=dict(type='str', required=True, aliases=['name']),
                         description=dict(type='str'),
                         ipavaulttype=dict(type='str', default='symmetric',
                                           choices=['standard', 'symmetric', 'asymmetric'], aliases=['vault_type']),
                         ipavaultsalt=dict(type='str', aliases=['vault_salt']),
                         ipavaultpublickey=dict(type='str', aliases=['vault_public_key']),
                         service=dict(type='str'),
                         replace=dict(type='bool', default=False, choices=[True, False]),
                         state=dict(type='str', default='present', choices=['present', 'absent']),
                         username=dict(type='list', aliases=['user']))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[['username', 'service']])

    client = VaultIPAClient(module=module,
                            host=module.params['ipa_host'],
                            port=module.params['ipa_port'],
                            protocol=module.params['ipa_prot'])
    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, vault = ensure(module, client)
        module.exit_json(changed=changed, vault=vault)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
