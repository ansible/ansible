#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

# Copyright: (c) 2018, Davide Blasi (@davegarath)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: spacewalk_swchannel_facts
short_description: Gather facts about all channels in spacewalk
description:
  - "Gather facts about all channels in spacewalk"
version_added: "2.8"
author:
  - Davide Blasi (@davegarath)
extends_documentation_fragment: spacewalk.documentation
'''

EXAMPLES = '''
- name: Get all channels in spacewalk
  spacewalk_swchannel_facts:
      url: "{{ spacewalk_url_api }}"
      login: "{{ spacewalk_login }}"
      password: "{{ spacewalk_passowrd }}"
  delegate_to: localhost
  register: channels

- debug: var=channels
'''

RETURN = '''
channels_facts:
  description: Provides all spacewalk channels in ansible_facts
  type: dict
  returned: always
  sample:
    "spacewalk_channels": {
        "centos7-x86_64": {
            "arch_name": "x86_64",
            "id": 101,
            "name": "CentOS 7 (x86_64)",
            "packages": 0,
            "provider_name": "PROVIDER",
            "systems": 0
        }
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.spacewalk import spacewalk_argument_spec, Channel


def main():
    argument_spec = spacewalk_argument_spec()
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    channel = Channel(module)
    ansible_facts = channel.get_all_channels()
    module.exit_json(changed=False, ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
