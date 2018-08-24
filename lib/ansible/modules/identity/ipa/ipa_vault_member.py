#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Stefan Scheglmann <scheglmann@strato.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt) # noqa: E501

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import ipa_argument_spec
from ansible.module_utils.ipa_vault import VaultIPAClient

# only for method overwrite
from ansible.module_utils._text import to_native

# Set max vault data size to 1MB
MAX_VAULT_DATA_SIZE = 2**20

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ipa_vault_member
author: Stefan Scheglmann (@schegi)
short_description: IPA vault member management
description:
    - Ensure presence/absence of memberusers, membergroups and memberservices
    - KRA service should be enabled to use this module.
options:
    cn:
        description:
            - Vault name.
        required: true
        aliases: ["name"]
    memberusers:
        description:
            - list of users to ensure
        aliases: ['vaultmemberusers', 'vault_member_users', 'member_users']
        type: list
    membergroups:
        description:
            - list of groups to ensure
        aliases: ['vaultmembergroups', 'vault_member_groups', 'member_groups']
        type: list
    memberservices:
        description:
            - list of services to ensure
        aliases: ['vaultmemberservices', 'vault_member_services',
                  'member_services']
        type: list
    username:
        description:
            - Any user who owns the user vault.
            - Mutually exclusive with service.
        aliases: ["user", "vault_user", "vaultuser"]
    service:
        description:
            - Any service who owns the service vault.
            - Mutually exclusive with user.
    state:
        description:
            - State to ensure.
        default: "present"
        choices: ["present", "absent"]
extends_documentation_fragment: ipa.documentation
version_added: "2.7"
'''

EXAMPLES = '''
# Ensure presence of memberusers, membergroups and memberservices on vault
- ipa_vault:
    name: vault01
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    memberusers:
      - memberuser1
      - memberuser2
    memberservices:
      - memberservice1/ipa.example.com
      - memberservice2/ipa.example.com
    membergroup:
      - membergroup1
      - membergroup2
    validate_certs: false

# Ensure absence memberusers, membergroups and memberservices on vault
- ipa_vault:
    name: vault01
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    state: absent
    memberusers:
      - memberuser1
      - memberuser2
    memberservices:
      - memberservice1/ipa.example.com
      - memberservice2/ipa.example.com
    membergroup:
      - membergroup1
      - membergroup2
    validate_certs: false
'''

RETURN = '''
vault:
  description: Vault as returned by IPA API
  returned: always
  type: dict
'''


def ensure(module, client):
    """Ensure membersuser, membergroup or memberservice state"""
    state = module.params['state']
    ipa_vault = client.vault_find()
    if not ipa_vault:
        module.fail_json(msg="Cannot ensure member state on"
                             " non-existing vault '%s'." % module.params['cn'])
    if state == 'present':
        changed, vault = client.add_vault_members(ipa_vault)
    else:
        changed, vault = client.remove_vault_members(ipa_vault)
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
        username=dict(
            type='str',
            aliases=['vaultuser', 'vault_user']
        ),
        service=dict(
            type='str',
            aliases=['vaultservice', 'vault_service']
        ),
        memberusers=dict(
            type='list',
            aliases=['vaultmemberusers', 'vault_member_users', 'member_users']
        ),
        membergroups=dict(
            type='list',
            aliases=['vaultmembergroups', 'vault_member_groups',
                     'member_groups']
        ),
        memberservices=dict(
            type='list',
            aliases=['vaultmemberservices', 'vault_member_services',
                     'member_services']
        ),
        state=dict(
            type='str',
            default='present',
            choices=['absent', 'present']
        ),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[
                               ['username', 'service'],
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
