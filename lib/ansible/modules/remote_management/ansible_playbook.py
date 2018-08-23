#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Fabien Dupont <fdupont@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ansible_playbook
short_description: Launch Ansible playbook on remote host
description:
  - This module launches an Ansible playbook. It is mainly a
    wrapper for the ansible-playbook command, so the options
    match the ansible-playbook options.
author:
  - Fabien Dupont (@fdupont-redhat)
version_added: "2.7"
options:
  path:
    description:
      - Path of the playbook to run
    required: true
    aliases: [name]
  inventory_hosts:
    description:
      - Specify inventory as a comma separated host list
      - Either `inventory_hosts` or `inventory_path` is required.
  inventory_path:
    description:
      - Specify inventory path (file or directory)
      - Either `inventory_hosts` or `inventory_path` is required.
  limit:
    description:
      - Further limit selected hosts to an additional pattern
    required: false
  extra_vars:
    description:
      - Set additional variables as key=value
    required: false
  extra_vars_files:
    description:
      - Set additional variables from files
    required: false
  tags:
    description:
      - Only run plays and tasks tagged with these values
    required: false
  skip_tags:
    description:
      - Do not run plays and tasks tagged with these values
    required: false
  connection_method:
    description:
      - Connection type to use.
      - List of connection plugins is available using 'ansible-doc -t connection -l'.
      - Ansible connection plugins documentation is also available at https://docs.ansible.com/ansible/latest/plugins/connection.html
    required: false
    default: 'smart'
  connection_user:
    description:
      - Connect as this user
    required: false
  connection_timeout:
    description:
      - Override the connection timeout in seconds
    required: false
    default: 10
  become:
    description:
      - Run operations with become
    type: bool
    required: false
    default: false
  become_method:
    description:
      - Privilege escalation method to use
    choices:
      - 'sudo'
      - 'su'
      - 'pbrun'
      - 'pfexec'
      - 'doas'
      - 'dzdo'
      - 'ksu'
      - 'runas'
      - 'pmrun'
      - 'enable'
      - 'machinectl'
    required: false
    default: 'sudo'
  become_user:
    description:
      - Run operations as this user
    required: false
    default: 'root'
  ssh_private_key_file:
    description:
      - Use this file to authenticate the connection
    required: false
  ssh_common_args:
    description:
      - Specify common arguments to pass to sftp/scp/ssh (e.g. ProxyCommand)
    required: false
  ssh_extra_args:
    description:
      - Specify extra arguments to pass to ssh only (e.g. -R)
    required: false
  scp_extra_args:
    description:
      - Specify extra arguments to pass to scp only (e.g. -l)
    required: false
  sftp_extra_args:
    description:
      - Specify extra arguments to pass to sftp only (e.g. -f, -l)
    required: false
  module_path:
    description:
      - prepend colon-separated path(s) to module library
    required: false
  vault_id:
    description:
      - The vault identity to use
    required: false
  vault_password_file:
    description:
      - Vault password file
    required: false
  flush_cache:
    description:
      - Clear the fact cache for every host in inventory
    type: bool
    required: false
    default: false
  force_handlers:
    description:
      - Run handlers even if a task fails
    type: bool
    required: false
    default: false
  start_at_task:
    description:
      - Start the playbook at the task matching this name
    required: false
  forks:
    description:
      - Specify number of parallel processes to use
    required: false
    default: 5
'''

EXAMPLES = '''
- name: Run a playbook on group
  ansible_playbook:
    path: ./subplaybook.yml
    inventory_hosts:
      - "{{ groups['my_group']) }}"
    limit:
      - "{{ groups['other_group'] }}"

- name: Run a playbook with extra vars
  ansible_playbook:
    path: ./playbook_with_vars.yml
    inventory_path: /tmp/inventory.yml
    extra_vars:
      var1: value1
      var2: value2

- name: Run tagged tasks of a playbook
  ansible_playbook:
    path: ./playbook_with_tags.yml
    inventory_path: /tmp/inventory.yml
    tags:
      - do_it
'''

RETURN = '''
cmd:
  description: the cmd that was run on the remote machine
  returned: always
  type: string
  sample: ansible-playbook -i /tmp/inventory.yml ./playbook.yml
rc:
  description: the status of the ansible-playbook launch
  returned: always
  type: int
stdout:
  description: the standard output of the playbook
  returned: always
  type: string
stderr:
  description: the standard error of the playbook
  returned: always
  type: string
delta:
  description: playbook end time - playbook start time
  returned: always
  type: string
  sample: 0:00:00.001529
end:
  description: playbook end time
  returned: always
  type: string
  sample: '2017-09-29 22:03:48.084657'
start:
  description: playbook start time
  returned: always
  type: string
  sample: '2017-09-29 22:03:48.083128'
'''

import datetime
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.six import b


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, type='path', aliases=['name']),
            inventory_hosts=dict(type='list'),
            inventory_path=dict(type='path'),
            limit=dict(type='list'),
            extra_vars=dict(type='dict'),
            extra_vars_files=dict(type='list'),
            tags=dict(type='list'),
            skip_tags=dict(type='list'),
            connection_method=dict(type='str', default='smart'),
            connection_user=dict(type='str'),
            connection_timeout=dict(type='int', default=10),
            become=dict(type='bool', default=False),
            become_method=dict(
                type='str',
                choices=[
                    'sudo',
                    'su',
                    'pbrun',
                    'pfexec',
                    'doas',
                    'dzdo',
                    'ksu',
                    'runas',
                    'pmrun',
                    'enable'
                ],
                default='sudo'),
            become_user=dict(type='str', default='root'),
            ssh_private_key_file=dict(type='path'),
            ssh_common_args=dict(type='dict'),
            ssh_extra_args=dict(type='dict'),
            scp_extra_args=dict(type='dict'),
            sftp_extra_args=dict(type='dict'),
            module_path=dict(type='list'),
            vault_id=dict(type='str'),
            vault_password_file=dict(type='path'),
            flush_cache=dict(type='bool', default=False),
            force_handlers=dict(type='bool', default=False),
            start_at_task=dict(type='str'),
            forks=dict(type='int', default=5)
        ),
        mutually_exclusive=[['inventory_hosts', 'inventory_path']],
        required_if=dict(),
        supports_check_mode=True
    )

    path = module.params['path']
    inventory_hosts = module.params['inventory_hosts']
    inventory_path = module.params['inventory_path']
    limit = module.params['limit']
    extra_vars = module.params['extra_vars']
    extra_vars_files = module.params['extra_vars_files']
    tags = module.params['tags']
    skip_tags = module.params['skip_tags']
    connection_method = module.params['connection_method']
    connection_user = module.params['connection_user']
    connection_timeout = module.params['connection_timeout']
    become = module.params['become']
    become_method = module.params['become_method']
    become_user = module.params['become_user']
    ssh_private_key_file = module.params['ssh_private_key_file']
    ssh_common_args = module.params['ssh_common_args']
    ssh_extra_args = module.params['ssh_extra_args']
    scp_extra_args = module.params['scp_extra_args']
    sftp_extra_args = module.params['sftp_extra_args']
    module_path = module.params['module_path']
    vault_id = module.params['vault_id']
    vault_password_file = module.params['vault_password_file']
    flush_cache = module.params['flush_cache']
    force_handlers = module.params['force_handlers']
    start_at_task = module.params['start_at_task']
    forks = module.params['forks']

    if not os.path.exists(path):
        module.fail_json(rc=256, msg="Playbook '%s' does not exist." % path)

    command = 'ansible-playbook ' + path

    if inventory_hosts:
        command += ' --inventory ' + ','.join(inventory_hosts) + ','

    if inventory_path:
        if os.path.exists(inventory_path):
            command += ' --inventory ' + inventory_path
        else:
            module.fail_json(rc=256, msg="Inventory path is not a valid path.")

    if limit:
        command += ' --limit ' + ','.join(limit)

    if extra_vars:
        for k, v in extra_vars.items():
            command += " --extra-vars '%s=%s'" % (str(k), str(v))

    if extra_vars_files:
        for evfile in extra_vars_files:
            command += " --extra-vars @%s" % evfile

    if tags:
        command += " --tags " + ','.join(tags)

    if skip_tags:
        command += " --skip-tags " + ','.join(skip_tags)

    if connection_method:
        command += " --connection %s" % connection_method

    if connection_user:
        command += " --user %s" % connection_user

    if connection_timeout:
        command += " --timeout %s" % connection_timeout

    if become:
        command += " --become --become-method %s --become-user %s" % (become_method, become_user)

    if ssh_private_key_file:
        command += " --private-key %s" % ssh_private_key_file

    if ssh_common_args:
        args = ""
        for k, v in ssh_common_args.items():
            args += '-o %s="%s"' % (k, v)
        command += " --ssh-common-args %s" % args

    if ssh_extra_args:
        args = ""
        for k, v in ssh_extra_args.items():
            args += '-o %s="%s"' % (k, v)
        command += " --ssh-extra-args %s" % args

    if scp_extra_args:
        args = ""
        for k, v in ssh_common_args.items():
            args += '-o %s="%s"' % (k, v)
        command += " --ssh-common-args %s" % args

    if sftp_extra_args:
        args = ""
        for k, v in ssh_common_args.items():
            args += '-o %s="%s"' % (k, v)
        command += " --ssh-common-args %s" % args

    if module_path:
        command += " --module-path %s" % ','.join(module_path)

    if vault_id:
        command += " --vault-id %s" % vault_id

    if vault_password_file:
        command += " --vault-password-file %s" % vault_password_file

    if flush_cache:
        command += " --flush-cache"

    if force_handlers:
        command += " --force-handlers"

    if start_at_task:
        command += " --start-at-task '%s'" % start_at_task

    if forks:
        command += " --fork %s" % str(forks)

    os.chdir(os.path.dirname(os.path.realpath(path)))

    startd = datetime.datetime.now()

    rc, out, err = module.run_command(command)

    endd = datetime.datetime.now()
    delta = endd - startd

    if out is None:
        out = b('')
    if err is None:
        err = b('')

    module.exit_json(
        cmd=command,
        stdout=out.rstrip(b("\r\n")),
        stderr=err.rstrip(b("\r\n")),
        rc=rc,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
