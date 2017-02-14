#!/usr/bin/python

# Empty module to serve as frontend for running the action plugin

DOCUMENTATION = '''
---
module: reset_ssh_session
short_description: Remove the CP handle file forcing Ansible to reconnect on next task
description: Should be used when you make a change that requires relogin to apply and you want to utilize that change
during the exeuction. The module (action) will make ansible reconnect to the host thus relogin.
author: Dan Hirsch (@hackndoes)
options:
  control_persist_path:
    description:
      - Sets the path to the ControlPersist handle file if it was set in ansible configuration
      - Leave empty if using the default ansible configuration
    choices:
      - None/Undefined
      - String of Path to location of the file as configuration in ansible.cfg
    default:
      - {{ ansible_user_dir }}/.ansible/cp/ansible-ssh-{{ inventory_hostname }}-22-{{ ansible_user_id }}
'''

EXAMPLES = '''
- name: Reset the ssh connection with default configuration
  reset_ssh_connection:

#ansible.cfg configuration
[ssh_connection]
control_path = "/tmp/my-file-%%r-%%h-22"

- name: Reset the ssh connection with this configured ansible.cfg
  reset_ssh_connection:
    control_persist_path: "{{ ansible_user_dir }}/.ansible/cp/ansible-ssh-{{ inventory_hostname }}-22-{{ ansible_user_id }}"
'''

RETURN = '''
changed:
  description: Specifies wether the control_persist_path points to a file and had it removed
  returned: always
  type: bool
  sample: False
'''