# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r'''
module: display
short_description: Display a message
description:
  - This action displays messages during execution either using normal callback semantics or bypassing them
    and printing directly to the terminal.
version_added: '2.21'
options:
  msg:
    description:
    - The message to display.
    type: str
    required: yes
  channel:
    description:
    - How to display the message, it allows you to use existing display channels in Ansible core.
      This will format and color and prefix the messages as Ansible itself would.
    choices:
        display: normal text
        error: Show an error message
        warning: Emit a warning
        deprecation: Present a deprecation message
        verbose: Emulate C(-v) output
        callback: normal task output via the callback framework
        log: send message to the ansible log, if it is enabled
    default: callback
extends_documentation_fragment:
  - action_common_attributes
  - action_common_attributes.conn
  - action_common_attributes.flow
attributes:
    action:
        support: full
    async:
        support: none
    bypass_host_loop:
        support: none
    become:
        support: none
    check_mode:
        support: full
    diff_mode:
        support: none
    connection:
        support: none
    delegation:
        details: Aside from C(register) and/or in combination with C(delegate_facts), it has little effect.
        support:  partial
    platform:
        support: full
        platforms: all
seealso:
  - module: ansible.builtin.assert
  - module: ansible.builtin.fail
author:
  - Ansible Core Team
'''

EXAMPLES = r'''
- name: Print the gateway for each host when defined
  ansible.builtin.display:
    msg: System {{ inventory_hostname }} has gateway {{ ansible_default_ipv4.gateway }}
  when: ansible_default_ipv4.gateway is defined

- name: Get uptime information
  ansible.builtin.shell: /usr/bin/uptime
  register: result

- name: Print return information from the previous task, if very verbose
  ansible.builtin.display:
    msg: '{{result}}'
  when: ansible_verbosity >= 2

- name: Display all variables/facts known for a host, if very very very verbose
  ansible.builtin.display:
    msg: '{{hostvars[inventory_hostname]}}'
  when: ansible_verbosity >= 4

- name: Assert a value is what we expect
  ansible.builtin.display:
      msg: "'X': {{x|default('UNDEFINED')}}.  'X' is {{(x|default(None) in [1,2,3])|ternary('','not')}} in the array"
  failed_when:
    - x is not defined or x not in [1,2,3]
'''
