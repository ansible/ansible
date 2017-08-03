#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Ansible, a Red Hat company
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
module: meta
short_description: Execute Ansible 'actions'
version_added: "1.2"
description:
    - Meta tasks are a special kind of task which can influence Ansible internal execution or state. Prior to Ansible 2.0,
      the only meta option available was `flush_handlers`. As of 2.2, there are five meta tasks which can be used.
      Meta tasks can be used anywhere within your playbook.
    - This module is also supported for Windows targets.
options:
  free_form:
    description:
        - This module takes a free form command, as a string. There's not an actual option named "free form".  See the examples!
        - >
          C(flush_handlers) makes Ansible run any handler tasks which have thus far been notified. Ansible inserts these tasks internally at certain
          points to implicitly trigger handler runs (after pre/post tasks, the final role execution, and the main tasks section of your plays).
        - >
          C(refresh_inventory) (added in 2.0) forces the reload of the inventory, which in the case of dynamic inventory scripts means they will be
          re-executed. This is mainly useful when additional hosts are created and users wish to use them instead of using the `add_host` module."
        - "C(noop) (added in 2.0) This literally does 'nothing'. It is mainly used internally and not recommended for general use."
        - "C(clear_facts) (added in 2.1) causes the gathered facts for the hosts specified in the play's list of hosts to be cleared, including the fact cache."
        - "C(clear_host_errors) (added in 2.1) clears the failed state (if any) from hosts specified in the play's list of hosts."
        - "C(end_play) (added in 2.2) causes the play to end without failing the host."
        - "C(reset_connection) (added in 2.3) interrupts a persistent connection (i.e. ssh + control persist)"
    choices: ['noop', 'flush_handlers', 'refresh_inventory', 'clear_facts', 'clear_host_errors', 'end_play', 'reset_connection']
    required: true
notes:
    - C(meta) is not really a module nor action_plugin as such it cannot be overwritten.
    - This module is also supported for Windows targets.
author:
    - "Ansible Core Team"
'''

EXAMPLES = '''
- template:
    src: new.j2
    dest: /etc/config.txt
  notify: myhandler
- name: force all notified handlers to run at this point, not waiting for normal sync points
  meta: flush_handlers

- name: reload inventory, useful with dynamic inventories when play makes changes to the existing hosts
  cloud_guest:            # this is fake module
    name: newhost
    state: present
- name: Refresh inventory to ensure new instaces exist in inventory
  meta: refresh_inventory

- name: Clear gathered facts from all currently targeted hosts
  meta: clear_facts

- name: bring host back to play after failure
  copy:
    src: file
    dest: /etc/file
  remote_user: imightnothavepermission

- meta: clear_host_errors

- user: name={{ansible_user}} groups=input
- name: reset ssh connection to allow user changes to affect 'current login user'
  meta: reset_connection
'''
