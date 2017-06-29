#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: net_banner
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage multiline banners on network devices
description:
  - This will configure both login and motd banners on network devices.
    It allows playbooks to add or remote
    banner text from the active running configuration.
options:
  banner:
    description:
      - Specifies which banner that should be
        configured on the remote device.
    required: true
    choices: ['login', 'motd']
  text:
    description:
      - The banner text that should be
        present in the remote device running configuration.  This argument
        accepts a multiline string, with no empty lines. Requires I(state=present).
    default: null
  state:
    description:
      - Specifies whether or not the configuration is
        present in the current devices active running configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure the login banner
  net_banner:
    banner: login
    text: |
      this is my login banner
      that contains a multiline
      string
    state: present

- name: remove the motd banner
  net_banner:
    banner: motd
    state: absent

- name: Configure banner from file
  net_banner:
    banner:  motd
    text: "{{ lookup('file', './config_partial/raw_banner.cfg') }}"
    state: present

"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - banner login
    - this is my login banner
    - that contains a multiline
    - string

rpc:
  description: load-configuration RPC send to the device
  returned: when configuration is changed on device
  type: string
  sample: >
          <system>
            <login>
                <message>this is my login banner</message>
            </login>
          </system>"
"""
