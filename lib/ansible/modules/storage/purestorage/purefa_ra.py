#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_ra
version_added: '2.8'
short_description: Enable or Disable Pure Storage FlashArray Remote Assist
description:
- Enable or Disable Remote Assist for a Pure Storage FlashArray.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Define state of remote assist
    - When set to I(enable) the RA port can be exposed using the
      I(debug) module.
    type: str
    default: enable
    choices: [ enable, disable ]
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Enable Remote Assist port
  purefa_ra:
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
  register: result

- debug:
    msg: "Remote Assist: {{ result['ra_info'] }}"

- name: Disable Remote Assist port
  purefa_ra:
    state: disable
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def enable_ra(module, array):
    """Enable Remote Assist"""
    changed = False
    ra_facts = {}
    if array.get_remote_assist_status()['status'] != 'enabled':
        try:
            ra_data = array.enable_remote_assist()
            ra_facts['fa_ra'] = {'name': ra_data['name'],
                                 'port': ra_data['port']}
            changed = True
        except Exception:
            module.fail_json(msg='Enabling Remote Assist failed')
    else:
        try:
            ra_data = array.get_remote_assist_status()
            ra_facts['fa_ra'] = {'name': ra_data['name'],
                                 'port': ra_data['port']}
        except Exception:
            module.fail_json(msg='Getting Remote Assist failed')
    module.exit_json(changed=changed, ra_info=ra_facts)


def disable_ra(module, array):
    """Disable Remote Assist"""
    changed = False
    if array.get_remote_assist_status()['status'] == 'enabled':
        try:
            array.disable_remote_assist()
            changed = True
        except Exception:
            module.fail_json(msg='Disabling Remote Assist failed')
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='enable', choices=['enable', 'disable']),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=False)

    array = get_system(module)

    if module.params['state'] == 'enable':
        enable_ra(module, array)
    else:
        disable_ra(module, array)
    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
