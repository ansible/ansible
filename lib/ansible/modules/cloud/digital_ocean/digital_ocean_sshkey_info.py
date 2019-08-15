#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: digital_ocean_sshkey_info
short_description: Gather information about DigitalOcean SSH keys
description:
  - This module can be used to gather information about DigitalOcean SSH keys.
  - This module replaces the C(digital_ocean_sshkey_facts) module.
version_added: "2.9"
author: "Patrick Marques (@pmarques)"
extends_documentation_fragment: digital_ocean.documentation
notes:
  - Version 2 of DigitalOcean API is used.
requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- digital_ocean_sshkey_info:
    oauth_token: "{{ my_do_key }}"
  register: ssh_keys

- set_fact:
    pubkey: "{{ item.public_key }}"
  loop: "{{ ssh_keys.data|json_query(ssh_pubkey) }}"
  vars:
    ssh_pubkey: "[?name=='ansible_ctrl']"

- debug:
    msg: "{{ pubkey }}"
'''


RETURN = '''
# Digital Ocean API info https://developers.digitalocean.com/documentation/v2/#list-all-keys
data:
    description: List of SSH keys on DigitalOcean
    returned: success and no resource constraint
    type: dict
    sample: [
      {
        "id": 512189,
        "fingerprint": "3b:16:bf:e4:8b:00:8b:b8:59:8c:a9:d3:f0:19:45:fa",
        "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAQQDDHr/jh2Jy4yALcK4JyWbVkPRaWmhck3IgCoeOO3z1e2dBowLh64QAM+Qb72pxekALga2oi4GvT+TlWNhzPH4V example",
        "name": "My SSH Public Key"
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper


def core(module):
    rest = DigitalOceanHelper(module)

    response = rest.get("account/keys")
    status_code = response.status_code
    json = response.json
    if status_code == 200:
        module.exit_json(changed=False, data=json['ssh_keys'])
    else:
        module.fail_json(msg='Error fetching SSH Key information [{0}: {1}]'.format(
            status_code, response.json['message']))


def main():
    module = AnsibleModule(
        argument_spec=DigitalOceanHelper.digital_ocean_argument_spec(),
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
