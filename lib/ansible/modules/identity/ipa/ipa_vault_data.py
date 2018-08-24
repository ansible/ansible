#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Stefan Scheglmann <scheglmann@strato.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt) # noqa: E501

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ipa_vault_data
author: Stefan Scheglmann (@schegi)
short_description: Archive in or retrieve from ipa vaults
description:
    - Archive data in ipa vaults of any type
    - Retrieve data from ipa vaults of any type
    - KRA service should be enabled to use this module.
options:
    cn:
        description:
            - Vault name.
        required: true
        aliases: ["name"]
    ipavaultdata:
        description:
            - Data to archive in vault.
            - Will not appear in log.
        aliases: ["vault_data", "data"]
    ipavaultdatafile:
        description:
            - File containing data to archive in vault.
            - Will not appear in log.
        aliases: ["vault_data_file", "data_file"]
    ipavaultprivatekey:
        description:
            - Private key for decryption.
            - Will not appear in logs.
        aliases: ["vault_private_key", "private_key"]
    ipavaultprivatekeyfile:
        description:
            - File containing the vault private key
            - Will not appear in logs.
        aliases: ["vault_private_key_file", "private_key_file"]
    ipavaultpassword:
        description:
            - The vault password.
            - Will not appear in logs.
        aliases: ["vault_password", "password"]
    ipavaultpasswordfile:
        description:
            - File containing the vault password
            - Will not appear in logs.
        aliases: ["vault_password_file", "password_file"]
    username:
        description:
            - Any user who owns the user vault.
            - Mutually exclusive with service.
        aliases: ["user", "vault_user", "vaultuser"]
    service:
        description:
            - Any service who owns the service vault.
            - Mutually exclusive with user.
        aliases: ["vault_service", "vaultservice"]
    operation:
        description:
            - Mode of operation.
        default: "archive"
        choices: ["archive", "retrieve"]
        aliases: ["op", "mode"]
    validate_certs:
        description:
            - Validate IPA server certificates.
        type: bool
        default: true
extends_documentation_fragment: ipa.documentation
version_added: "2.7"
'''

EXAMPLES = '''
# Archive data in standard vault
- ipa_vault:
    name: vault01
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    data: super_secret_vault_content
    validate_certs: false

# Archive data in symmetric vault,
# password is required.
- ipa_vault:
    name: vault01
    data: super_secret_vault_content
    password: super_secret_vault_password
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Archive data in asymmetric vault,
# private key is required.
- ipa_vault:
    name: vault01
    data: super_secret_vault_content
    private_key_file: mykey.pem
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Retrieve data from standard vault
- ipa_vault:
    name: vault01
    mode: retrieve
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Retrieve data from symmetric ault
- ipa_vault:
    name: vault01
    mode: retrieve
    password: super_secret_vault_password
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false

# Retrieve data from asymmetric vault
- ipa_vault:
    name: vault01
    mode: retrieve
    private_key_file: mykey.pem
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: false
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

def mode(module, client):
    """Archive or retrieve"""
    operation = module.params['operation']
    vault = client.vault_find()
    if not vault:
        module.fail_json(
            msg="Cannot archive in or retrieve from non-existing"
            " vault '%s'." % module.params['cn'])
    if operation == 'archive':
        changed, vault = client.archive_data(vault)
    else:
        changed, vault = client.retrieve_data(vault)
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
        ipavaultprivatekey=dict(
            type='str',
            aliases=['vault_private_key', 'private_key'],
            no_log=True
        ),
        ipavaultprivatekeyfile=dict(
            type='str',
            aliases=['vault_private_key_file', 'private_key_file'],
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
        ipavaultdata=dict(
            type='str',
            aliases=['vault_data', 'data'],
            no_log=True,
        ),
        ipavaultdatafile=dict(
            type='str',
            aliases=['vault_data_file', 'data_file'],
            no_log=True,
        ),
        username=dict(
            type='str',
            aliases=['vaultuser', 'vault_user', 'user']
        ),
        service=dict(
            type='str',
            aliases=['vaultservice', 'vault_service']
        ),
        operation=dict(
            type='str',
            default='archive',
            choices=['archive', 'retrieve'],
            aliases=['op', 'mode']
        ),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[
                               ['username', 'service'],
                               ['ipavaultpassword', 'ipavaultpasswordfile'],
                               ['ipavaultpublickey', 'ipavaultpublickeyfile'],
                               ['ipavaultprivatekey',
                                'ipavaultprivatekeyfile'],
                               ['ipavaultdata', 'ipavaultdatafile'],
                           ])

    client = VaultIPAClient(module=module,
                            host=module.params['ipa_host'],
                            port=module.params['ipa_port'],
                            protocol=module.params['ipa_prot'])
    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, vault = mode(module, client)
        module.exit_json(changed=changed, vault=vault)
    except Exception as exception:
        module.fail_json(
            msg=to_native(exception), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
