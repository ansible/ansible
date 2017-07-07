#!/usr/bin/python
# -*- coding: utf-8 -*-

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
"""
Module to manipulate available runc containers.
"""

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview']
}


DOCUMENTATION = '''
---
module: runc_container
short_description: Manage containers via runc
version_added: "2.4"
description:
  - Manage containers via runc
author: Steve Milner @ashcrow
notes:
    - host should support c(runc) command
options:
  state:
    description: The state the container should be in
    required: True
    choices: ['started', 'stopped', 'paused', 'absent']
  name:
    description: The name of the container to manage
    required: True
  root:
    description: Full path to a runc container directory
    required: False
    default: '/run/runc'
  bin:
    description: Full path to a runc binary
    required: False
    default: '/usr/bin/runc'
  working_dir:
    description: Directory to run the runc commands in
    required: False
'''

EXAMPLES = '''
- name: Start MyContainer
  runc_container:
    name: MyContainer
    state: started

- name: Stop AContainer in a nonstandard runc dir
  runc_container:
    name: AContainer
    state: stopped
    root: /run/ourcontainers

- name: Start a container from a specific path
  runc_container:
    name: AnotherContainer
    state: started
    working_dir: /var/lib/containers/atomic/AnotherContainer

- name: Remove MyContainer
  runc_container:
    name: MyContainer
    state: absent
'''

RETURN = '''
cmd:
    description: The executed command
    returned: always
    type: string
    sample: "/usr/bin/runc --root=/run/runc start 'container'"
'''


import json
import os
import time

from ansible.module_utils.basic import AnsibleModule


def _stop_container_before(name, runc_bin, runc_root, module):
    """
    Stops a container before another command.
    """
    args = ['--root {}'.format(runc_root), 'kill', name]
    rc, out, err = module.run_command(args, executable=runc_bin)
    if rc != 0:
        module.exit_json(
            cmd='{} {}'.format(runc_bin, ' '.join(args)),
            stdout=out,
            stderr=err,
            changed=False,
            rc=rc)
    # Sleep is required as kill followed by another command may happen
    # too fast for runc to actually kill the container
    time.sleep(2)


def main():
    """
    Main entry point for runc_container.
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True,
                       choices=['started', 'stopped', 'paused', 'absent']),
            name=dict(required=True),
            root=dict(required=False, default='/run/runc'),
            bin=dict(required=False, default='/usr/bin/runc'),
            working_dir=dict(required=False)))

    # Simplify arguments
    state = module.params['state']
    name = module.params['name']
    runc_root = module.params['root']
    runc_bin = module.params['bin']
    working_dir = module.params['working_dir'] or None

    # Get a list of the containers
    rc, out, err = module.run_command([
        '--root {}'.format(runc_root), 'list', '-f', 'json'],
        executable=runc_bin)
    if rc != 0:
        module.exit_json(
            cmd='{} --root={} list -f json'.format(runc_bin, runc_root),
            stdout='Unable to execute runc list: {}'.format(out),
            stderr=err,
            changed=False,
            rc=rc)

    # Moving to the working directory if requested
    if working_dir:
        os.chdir(working_dir)

    container_state = 'unknown'
    if out != 'null\n':
        for container in json.loads(out):
            if container['id'] == name:
                container_state = container['status']

    # Arguments used in executing the runc command.
    # Built from the argument_spec.
    args = ['--root {}'.format(runc_root)]

    # Create the args baed on the requested state. If the
    # requested state is already in use exit out with no change.
    if state == 'started':
        # Exit early if the container is already started
        if container_state == 'running':
            module.exit_json(
                stdout='Container already running',
                changed=False,
                rc=0)
        # Use resume if the container is paused
        if container_state == 'paused':
            args.append('resume')
        # else use run and detatch
        else:
            args += ['run', '-d']
    elif state == 'stopped':
        # Exit early if the container is already stopped
        if container_state == 'stopped':
            module.exit_json(
                stdout='Container already stopped',
                changed=False,
                rc=0)
        # kill is the command to stop a container
        args.append('kill')
    elif state == 'paused':
        # Exit early if the container is already paused
        if container_state == 'paused':
            module.exit_json(
                stdout='Container already paused',
                changed=False,
                rc=0)
        args.append('pause')
    elif state == 'absent':
        # If the state is unknwon then the container is already absent
        if container_state == 'unknown':
            module.exit_json(
                stdout='Container already absent',
                changed=False,
                rc=0)
        # We must stop the container if it is running
        elif container_state != 'stopped':
            _stop_container_before(name, runc_bin, runc_root, module)
        args.append('delete')

    # End the command with the name as the last argument
    args.append(name)

    # Execute command
    changed = False
    rc, out, err = module.run_command(args, executable=runc_bin)
    if rc == 0:
        changed = True
    module.exit_json(
        cmd='{} {}'.format(runc_bin, ' '.join(args)),
        stdout=out,
        stderr=err,
        changed=changed,
        rc=rc)


if __name__ == '__main__':
    main()
