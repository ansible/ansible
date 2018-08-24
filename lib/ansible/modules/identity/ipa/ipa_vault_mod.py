#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Juan Manuel Parrilla <jparrill@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt) # noqa: E501

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import ipa_argument_spec
from ansible.module_utils.ipa_vault import VaultIPAClient

# only for method overwrite
from ansible.module_utils._text import to_native

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ipa_vault_mod
author: Stefan Scheglmann (@schegi)
short_description: Modify IPA Vaults
description:
    - Change IPA vault type
    - Change symmetric IPA vault password
    - Change asymmetric IPA vault keypair
    - Change vault owner
    - Change vault description
options:
    cn:
        description:
            - Vault name.
            - Can not be changed as it is the unique identifier.
        required: true
        aliases: ["name"]
    ipavaultnewtype:
        description:
            - New vault type.
        choices: ["standard", "symmetric", "asymmetric"]
        aliases: ["vault_new_type", "new_type"]
    ipavaultnewpublickey:
        description:
            - New public key.
            - Will not appear in logs.
        aliases: ["vault_new_public_key", "new_public_key"]
    ipavaultnewpublickeyfile:
        description:
            - File containing the new vault public key
            - Will not appear in logs.
        aliases: ["vault_new_public_key_file", "new_public_key_file"]
    ipavaultprivatekey:
        description:
            - Vault private key.
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
    ipavaultnewpassword:
        description:
            - The new vault password.
            - Will not appear in logs.
        aliases: ["vault_new_password", "new_password", "newpassword"]
    ipavaultnewpasswordfile:
        description:
            - File containing the new vault password
            - Will not appear in logs.
        aliases: ["vault_new_password_file", "new_password_file",
                  "newpasswordfile"]
    ipavaultsalt:
        description:
            - Vault Salt.
        aliases: ["vault_salt"]
    username:
        description:
            - Any user can own one or more user vaults.
            - Mutually exclusive with service.
        aliases: ["user", "vault_user", vaultuser"]
    service:
        description:
            - Any service can own one or more service vaults.
            - Mutually exclusive with user.
        aliases: ["vault_service", "vaultservice"]
extends_documentation_fragment: ipa.documentation
version_added: "2.7"
'''

EXAMPLES = '''
'''

RETURN = '''
vault:
  description: Vault as returned by IPA API
  returned: always
  type: dict
'''


def modify(module, client):
    """Update password, keypair or vaulttype."""
    vault = client.vault_find()
    if not vault:
        module.fail_json(msg="Cannot find vault '%s', cannot update"
                             " non-existing vault!" % module.params['cn'])
    return client.update_vault(vault)


def main():
    """Main module method"""
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        cn=dict(
            type='str',
            required=True,
            aliases=['name']
        ),
        description=dict(
            type='str'
        ),
        ipavaultnewtype=dict(
            type='str',
            choices=['standard', 'symmetric', 'asymmetric'],
            aliases=['new_vault_type', 'new_type', 'newtype',
                     'newvaulttype']
        ),
        ipavaultsalt=dict(
            type='str',
            aliases=['vault_salt']
        ),
        ipavaultnewpublickey=dict(
            type='str',
            aliases=['vault_new_public_key', 'new_public_key'],
            no_log=True
        ),
        ipavaultnewpublickeyfile=dict(
            type='str',
            aliases=['vault_new_public_key_file', 'new_public_key_file'],
            no_log=True
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
        ipavaultnewpassword=dict(
            type='str',
            aliases=['vault_new_password', 'new_password', 'newpassword'],
            no_log=True
        ),
        ipavaultnewpasswordfile=dict(
            type='str',
            aliases=['vault_new_password_file', 'new_password_file',
                     'newpasswordfile'],
            no_log=True
        ),
        username=dict(
            type='str',
            aliases=['vaultuser', 'vault_user', 'user']
        ),
        service=dict(
            type='str',
            aliases=['vaultservice', 'vault_service']
        ),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           # Currently no checkmode supported.
                           supports_check_mode=False,
                           mutually_exclusive=[
                               ['username', 'service'],
                               ['ipavaultpassword', 'ipavaultpasswordfile'],
                               ['ipavaultnewpassword',
                                'ipavaultnewpasswordfile'],
                               ['ipavaultnewpublickey',
                                'ipavaultnewpublickeyfile'],
                               ['ipavaultprivatekey',
                                'ipavaultprivatekeyfile'],
                           ])

    client = VaultIPAClient(module=module,
                            host=module.params['ipa_host'],
                            port=module.params['ipa_port'],
                            protocol=module.params['ipa_prot'])
    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, vault = modify(module, client)
        module.exit_json(changed=changed, vault=vault)
    except Exception as exception:
        module.fail_json(
            msg=to_native(exception), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
