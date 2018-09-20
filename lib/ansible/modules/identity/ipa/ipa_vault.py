#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Juan Manuel Parrilla <jparrill@redhat.com> and
# Stefan Scheglmann <scheglmann@strato.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt) # noqa: E501

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ipa_vault
author: Juan Manuel Parrilla (@jparrill) and Stefan Scheglmann (@schegi)
short_description: Add, delete vaults in IPA
description:
    - Add, and delete vaults in ipa
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
        default: "standard"
        choices: ["standard", "symmetric", "asymmetric"]
        required: true
        aliases: ["vault_type", "type"]
    ipavaultpublickey:
        description:
            - Public key.
            - Will not appear in logs.
        aliases: ["vault_public_key", "public_key"]
    ipavaultpublickeyfile:
        description:
            - File containing the vault public key
            - Will not appear in logs.
        aliases: ["vault_public_key_file", "public_key_file"]
        version_added: "2.8"
    ipavaultpassword:
        description:
            - The vault password.
            - Will not appear in logs.
        aliases: ["vault_password", "password"]
        version_added: "2.8"
    ipavaultpasswordfile:
        description:
            - File containing the vault password
            - Will not appear in logs.
        aliases: ["vault_password_file", "password_file"]
        version_added: "2.8"
    ipavaultsalt:
        description:
            - Vault Salt.
        aliases: ["vault_salt"]
    username:
        description:
            - Any user can own one or more user vaults.
            - Mutually exclusive with service.
        aliases: ["vaultuser", "vault_user"]
    service:
        description:
            - Any service can own one or more service vaults.
            - Mutually exclusive with user.
        aliases: ["vault_service", "vaultservice"]
    state:
        description:
            - State to ensure.
        default: "present"
        choices: ["present", "absent"]
    validate_certs:
        description:
        - Validate IPA server certificates.
        type: bool
        default: true
extends_documentation_fragment: ipa.documentation
version_added: "2.7"
'''

EXAMPLES = '''
# Ensure standard vault is present
- ipa_vault:
    name: vault01
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Ensure standard vault is present
- ipa_vault:
    name: vault01
    username: testuser1
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Ensure standard vault is present
- ipa_vault:
    name: vault01
    service: test/ipa.example.com
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Ensure symmetric service vault is present
- ipa_vault:
    name: vault01
    type: symmetric
    password: my_secret_vault_password
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Ensure asymmetric user vault is present
- ipa_vault:
    name: vault01
    type: asymmetric
    public_key_file: mykey.pub
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Ensure vault is absent
- ipa_vault:
    name: vault01
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false
    state: absent

# Ensure user vault is absent
- ipa_vault:
    name: vault01
    username: testuser1
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false
    state: absent

# Ensure service vault is absent
- ipa_vault:
    name: vault01
    service: test/ipa.example.com
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false
    state: absent
'''

RETURN = '''
vault:
  description: Vault as returned by IPA API
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import ipa_argument_spec
from ansible.module_utils.ipa_vault import VaultIPAClient

# only for method overwrite
from ansible.module_utils._text import to_native


def ensure(module, client):
    """Ensure vault state"""
    state = module.params['state']
    changed = False
    if state == 'present':
        # Try to get or create vault with the name provided
        changed, vault = client.get_or_create_vault()
        # Initialize new vault with empty data byte string
        if changed:
            client.archive_data_internal(vault, b'')
    else:
        vault = client.vault_find()
        if vault:
            changed = True
            if not module.check_mode:
                client.vault_del(vault)
    return changed, vault


def main():
    """Main module method"""
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        cn=dict(
            type='str',
            required=True,
            aliases=['name']
        ),
        description=dict(type='str'),
        ipavaulttype=dict(
            type='str',
            default='standard',
            choices=['standard', 'symmetric', 'asymmetric'],
            aliases=['vault_type', 'type']
        ),
        ipavaultsalt=dict(
            type='str',
            aliases=['vault_salt']
        ),
        ipavaultpublickey=dict(
            type='str',
            aliases=['vault_public_key', 'public_key'],
            no_log=True
        ),
        ipavaultpublickeyfile=dict(
            type='str',
            aliases=['vault_public_key_file', 'public_key_file'],
            no_log=True
        ),
        ipavaultpassword=dict(
            type='str',
            aliases=['vault_password', 'password'],
            no_log=True
        ),
        ipavaultpasswordfile=dict(
            type='str',
            aliases=['vault_password_file', 'password_file'],
            no_log=True
        ),
        username=dict(
            type='str',
            aliases=['vaultuser', 'vault_user']
        ),
        service=dict(
            type='str',
            aliases=['vaultservice', 'vault_service']
        ),
        state=dict(
            type='str',
            default='present',
            choices=['present', 'absent']
        ),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[
                               ['username', 'service'],
                               ['ipavaultpassword', 'ipavaultpasswordfile'],
                               ['ipavaultpublickey', 'ipavaultpublickeyfile'],
                           ])

    client = VaultIPAClient(module=module,
                            host=module.params['ipa_host'],
                            port=module.params['ipa_port'],
                            protocol=module.params['ipa_prot'])
    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, vault = ensure(module, client)
        module.exit_json(changed=changed, vault=vault)
    except Exception as exception:
        module.fail_json(
            msg=to_native(exception), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
