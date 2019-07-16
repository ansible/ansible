#!/usr/bin/python
#
# Scaleway SSH keys management module
#
# Copyright (C) 2018 Online SAS.
# https://www.scaleway.com
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
module: scaleway_sshkey
short_description: Scaleway SSH keys management module
version_added: "2.6"
author: Remy Leone (@sieben)
description:
    - This module manages SSH keys on Scaleway account
      U(https://developer.scaleway.com)
extends_documentation_fragment: scaleway

options:
  state:
    description:
     - Indicate desired state of the SSH key.
    default: present
    choices:
      - present
      - absent
  ssh_pub_key:
    description:
     - The public SSH key as a string to add.
    required: true
  api_url:
    description:
      - Scaleway API URL
    default: 'https://account.scaleway.com'
    aliases: ['base_url']
'''

EXAMPLES = '''
- name: "Add SSH key"
  scaleway_sshkey:
    ssh_pub_key: "ssh-rsa AAAA..."
    state: "present"

- name: "Delete SSH key"
  scaleway_sshkey:
    ssh_pub_key: "ssh-rsa AAAA..."
    state: "absent"

- name: "Add SSH key with explicit token"
  scaleway_sshkey:
    ssh_pub_key: "ssh-rsa AAAA..."
    state: "present"
    oauth_token: "6ecd2c9b-6f4f-44d4-a187-61a92078d08c"
'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
        "ssh_public_keys": [
            {"key": "ssh-rsa AAAA...."}
        ]
    }
'''

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.scaleway import scaleway_argument_spec, Scaleway


def extract_present_sshkeys(raw_organization_dict):
    ssh_key_list = raw_organization_dict["organizations"][0]["users"][0]["ssh_public_keys"]
    ssh_key_lookup = [ssh_key["key"] for ssh_key in ssh_key_list]
    return ssh_key_lookup


def extract_user_id(raw_organization_dict):
    return raw_organization_dict["organizations"][0]["users"][0]["id"]


def sshkey_user_patch(ssh_lookup):
    ssh_list = {"ssh_public_keys": [{"key": key}
                                    for key in ssh_lookup]}
    return ssh_list


def core(module):
    ssh_pub_key = module.params['ssh_pub_key']
    state = module.params["state"]
    account_api = Scaleway(module)
    response = account_api.get('organizations')

    status_code = response.status_code
    organization_json = response.json

    if not response.ok:
        module.fail_json(msg='Error getting ssh key [{0}: {1}]'.format(
            status_code, response.json['message']))

    user_id = extract_user_id(organization_json)
    present_sshkeys = []
    try:
        present_sshkeys = extract_present_sshkeys(organization_json)
    except (KeyError, IndexError) as e:
        module.fail_json(changed=False, data="Error while extracting present SSH keys from API")

    if state in ('present',):
        if ssh_pub_key in present_sshkeys:
            module.exit_json(changed=False)

        # If key not found create it!
        if module.check_mode:
            module.exit_json(changed=True)

        present_sshkeys.append(ssh_pub_key)
        payload = sshkey_user_patch(present_sshkeys)

        response = account_api.patch('/users/%s' % user_id, data=payload)

        if response.ok:
            module.exit_json(changed=True, data=response.json)

        module.fail_json(msg='Error creating ssh key [{0}: {1}]'.format(
            response.status_code, response.json))

    elif state in ('absent',):
        if ssh_pub_key not in present_sshkeys:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        present_sshkeys.remove(ssh_pub_key)
        payload = sshkey_user_patch(present_sshkeys)

        response = account_api.patch('/users/%s' % user_id, data=payload)

        if response.ok:
            module.exit_json(changed=True, data=response.json)

        module.fail_json(msg='Error deleting ssh key [{0}: {1}]'.format(
            response.status_code, response.json))


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['absent', 'present']),
        ssh_pub_key=dict(required=True),
        api_url=dict(fallback=(env_fallback, ['SCW_API_URL']), default='https://account.scaleway.com', aliases=['base_url']),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
