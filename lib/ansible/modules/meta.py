#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ansible, a Red Hat company
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: meta
short_description: Execute Ansible 'actions'
version_added: '1.2'
description:
    - Meta tasks are a special kind of task which can influence Ansible internal execution or state.
    - Meta tasks can be used anywhere within your playbook.
    - This module is also supported for Windows targets.
options:
  free_form:
    description:
        - This module takes a free form command, as a string. There is not an actual option named "free form".  See the examples!
        - C(flush_handlers) makes Ansible run any handler tasks which have thus far been notified. Ansible inserts these tasks internally at certain
          points to implicitly trigger handler runs (after pre/post tasks, the final role execution, and the main tasks section of your plays).
        - C(refresh_inventory) (added in Ansible 2.0) forces the reload of the inventory, which in the case of dynamic inventory scripts means they will be
          re-executed. If the dynamic inventory script is using a cache, Ansible cannot know this and has no way of refreshing it (you can disable the cache
          or, if available for your specific inventory datasource (e.g. aws), you can use the an inventory plugin instead of an inventory script).
          This is mainly useful when additional hosts are created and users wish to use them instead of using the M(ansible.builtin.add_host) module.
        - C(noop) (added in Ansible 2.0) This literally does 'nothing'. It is mainly used internally and not recommended for general use.
        - C(clear_facts) (added in Ansible 2.1) causes the gathered facts for the hosts specified in the play's list of hosts to be cleared,
          including the fact cache.
        - C(clear_host_errors) (added in Ansible 2.1) clears the failed state (if any) from hosts specified in the play's list of hosts.
        - C(end_play) (added in Ansible 2.2) causes the play to end without failing the host(s). Note that this affects all hosts.
        - C(reset_connection) (added in Ansible 2.3) interrupts a persistent connection (i.e. ssh + control persist)
        - C(end_host) (added in Ansible 2.8) is a per-host variation of C(end_play). Causes the play to end for the current host without failing it.
        - C(end_batch) (added in Ansible 2.12) causes the current batch (see C(serial)) to end without failing the host(s).
          Note that with C(serial=0) or undefined this behaves the same as C(end_play).
    choices: [ clear_facts, clear_host_errors, end_host, end_play, flush_handlers, noop, refresh_inventory, reset_connection, end_batch ]
    required: true
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.conn
    - action_common_attributes.flow
    - action_core
attributes:
    action:
      support: none
    bypass_host_loop:
      details: Some of the subactions ignore the host loop, see the description above for each specific action for the exceptions
      support: partial
    bypass_task_loop:
      details: Most of the subactions ignore the task loop, see the description above for each specific action for the exceptions
      support: partial
    check_mode:
      details: While these actions don't modify the targets directly they do change possible states of the target within the run
      support: partial
    delegation:
      support: none
    diff_mode:
      support: none
    ignore_conditional:
      details: Only some options support conditionals and when they do they act 'bypassing the host loop', taking the values from first available host
      support: partial
    connection:
      details: Most options in this action do not use a connection, except C(reset_connection) which still does not connect to the remote
      support: partial
notes:
    - C(clear_facts) will remove the persistent facts from M(ansible.builtin.set_fact) using C(cacheable=True),
      but not the current host variable it creates for the current run.
    - Skipping C(meta) tasks with tags is not supported before Ansible 2.11.
seealso:
- module: ansible.builtin.assert
- module: ansible.builtin.fail
author:
    - Ansible Core Team
'''

EXAMPLES = r'''
# Example showing flushing handlers on demand, not at end of play
- template:
    src: new.j2
    dest: /etc/config.txt
  notify: myhandler

- name: Force all notified handlers to run at this point, not waiting for normal sync points
  meta: flush_handlers

# Example showing how to refresh inventory during play
- name: Reload inventory, useful with dynamic inventories when play makes changes to the existing hosts
  cloud_guest:            # this is fake module
    name: newhost
    state: present

- name: Refresh inventory to ensure new instances exist in inventory
  meta: refresh_inventory

# Example showing how to clear all existing facts of targetted hosts
- name: Clear gathered facts from all currently targeted hosts
  meta: clear_facts

# Example showing how to continue using a failed target
- name: Bring host back to play after failure
  copy:
    src: file
    dest: /etc/file
  remote_user: imightnothavepermission

- meta: clear_host_errors

# Example showing how to reset an existing connection
- user:
    name: '{{ ansible_user }}'
    groups: input

- name: Reset ssh connection to allow user changes to affect 'current login user'
  meta: reset_connection

# Example showing how to end the play for specific targets
- name: End the play for hosts that run CentOS 6
  meta: end_host
  when:
  - ansible_distribution == 'CentOS'
  - ansible_distribution_major_version == '6'
'''
