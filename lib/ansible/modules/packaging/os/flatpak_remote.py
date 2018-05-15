#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017 John Kwiatkoski
# Copyright: (c) 2018 Alexander Bethke
# Copyright: (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: flatpak_remote
version_added: '2.6'
requirements:
- flatpak
author:
- John Kwiatkoski (@jaykayy)
- Alexander Bethke (@oolongbrothers)
short_description: Manage flatpak repository remotes
description:
- The C(flatpak_remote) module adds or removes flatpak repository remotes.
notes:
- The C(flatpak_remote) requires the C(flatpak) binary the be installed on the managed host.
options:
  name:
    description:
    - The name of the flatpak repository to manage
    - When I(state) is set to C(present), I(name) is added as a remote for installing flatpaks.
    - When used with I(state=absent) the remote with that name will be removed.
    required: true
  remote:
    description:
    - The URL of the flatpak remote to add
    - When I(state) is set to C(present), I(remote) URL is added as a flatpak remote for the
      specified installation C(method).
    - When used with I(state=absent), this is not required.
  method:
    description:
    - The installation method to use
    - Defines if the I(flatpak_remote) is to installed for the globally for the whole C(system)
      or for the current C(user) only.
    choices: [ system, user ]
    default: system
  executable:
    description:
    - The path to the C(flatpak) executable to use
    - By defaultm the C(flatpak_remote) module looks for the C(flatpak) executable on the path.
    default: flatpak
  state:
    description:
      - Wether the flatpak_remote should be present on the managed host or not
      - Setting this to C(present) will install the flatpak remote.
      - Setting this to C(absent) will remove the flatpak remote.
    choices: [ absent, present ]
    default: present
'''

EXAMPLES = r'''
- name: Add the Gnome flatpak remote to the system installation under the name 'gnome'.
  flatpak_remote:
    name: gnome
    state: present
    remote: https://sdk.gnome.org/gnome-apps.flatpakrepo
    method: system

- name: Remove the Gnome flatpak remote  from the user installation.
  flatpak_remote:
    name: gnome
    state: absent

- name: Add the flathub flatpak repository remote to the user installation.
  flatpak_remote:
    name: flathub
    state: present
    remote:  https://dl.flathub.org/repo/flathub.flatpakrepo
    method: user

- name: Remove the flathub flatpak repository remote from the system installtion.
  flatpak_remote:
    name: flathub
    state: absent
    method: system
'''

RETURN = r'''
reason:
  description: On failure, the output for the failure
  returned: failed
  type: string
  sample: error while installing...
name:
  description: Remote of flatpak given for the operation
  returned: always
  type: string
  sample: https://sdk.gnome.org/gnome-apps.flatpakrepo
'''

import subprocess
from ansible.module_utils.basic import AnsibleModule


def add_remote(module, binary, name, remote, method):
    """Add a new remote."""
    global result
    command = "{0} remote-add --{1} {2} {3}".format(
        binary, method, name, remote)
    _flatpak_command(module, module.check_mode, command)
    result['changed'] = True


def remove_remote(module, binary, name, method):
    """Remove an existing remote."""
    global result
    command = "{0} remote-delete --{1} --force {2} ".format(
        binary, method, name)
    _flatpak_command(module, module.check_mode, command)
    result['changed'] = True


def remote_exists(module, binary, name, remote, method):
    """Check if the remote exists."""
    command = "{0} remote-list -d --{1}".format(binary, method)
    # The query operation for the remote needs to be run even in check mode
    output = _flatpak_command(module, False, command)
    for line in output.splitlines():
        listed_remote = line.split()
        if listed_remote[0] == name:
            return True
    return False


def _flatpak_command(module, noop, command):
    global result
    if noop:
        result['rc'] = 0
        result['command'] = command
        return ""

    process = subprocess.Popen(
        command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = process.communicate()
    result['rc'] = process.returncode
    result['command'] = command
    result['stdout'] = stdout_data
    result['stderr'] = stderr_data
    if result['rc'] != 0:
        module.fail_json(msg="Failed to execute flatpak command", **result)
    return stdout_data


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            remote=dict(type='str'),
            method=dict(type='str', default='system',
                        choices=['user', 'system']),
            state=dict(type='str', default="present",
                       choices=['absent', 'present']),
            executable=dict(type='str', default="flatpak")
        ),
        # This module supports check mode
        supports_check_mode=True,
    )

    name = module.params['name']
    remote = module.params['remote']
    method = module.params['method']
    state = module.params['state']
    executable = module.params['executable']
    binary = module.get_bin_path(executable, None)

    if remote is None:
        remote = ''

    global result
    result = dict(
        changed=False
    )

    # If the binary was not found, fail the operation
    if not binary:
        module.fail_json(msg="Executable '%s' was not found on the system." % executable, **result)

    if state == 'present' and not remote_exists(module, binary, name, remote, method):
        add_remote(module, binary, name, remote, method)
    elif state == 'absent' and remote_exists(module, binary, name, remote, method):
        remove_remote(module, binary, name, method)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
