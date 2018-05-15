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
- Manage flatpak repository remotes.
options:
  name:
    description:
    - When I(state) is set to C(present), I(name) is added as a remote for installing flatpaks.
      When used with I(state=absent) the remote with thet name will be removed.
    required: true
  remote:
    description:
    - When I(state) is set to C(present), I(remote) url is added as a flatpak remote for the
      specified installation C(method).
      When used with I(state=absent), this is not required.
    required: false
  method:
    description:
    - Determines the type of installation to work on. Can be C(user) or C(system) installations.
    choices: [ user, system ]
    required: false
    default: system
  executable:
    description:
    - The path to the C(flatpak) executable to use. The default will look for
      the c(flatpak) executable on the path
    default: flatpak
  state:
    description:
      - Set to C(present) will install the flatpak remote.
      - Set to C(absent) will remove the flatpak remote.
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
    """
    Add a new remote.

    returns:
        result, type: int
            The result status of the operation
            Possible values:
            0 - operation successful
            1 - operation failed
        output, type: str
            Output of the operation
            Especially helpful to know that's wrong when the operation failed
    """
    if module.check_mode:
        # Check if any changes would be made but don't actually make
        # those changes
        module.exit_json(changed=True)
    command = "{0} remote-add --{1} {2} {3}".format(
        binary, method, name, remote)

    return_code, output = _flatpak_command(command)
    if return_code != 0:
        return 1, output

    return 0, output


def remove_remote(module, binary, name, method):
    """
    Remove an existing remote.

    returns:
        result, type: int
            The result status of the operation
            Possible values:
            0 - operation successful
            1 - operation failed
        output, type: str
            Output of the operation
            Especially helpful to know that's wrong when the operation failed
    """
    if module.check_mode:
        # Check if any changes would be made but don't actually make
        # those changes
        module.exit_json(changed=True)

    command = "{0} remote-delete --{1} --force {2} ".format(
        binary, method, name)
    return_code, output = _flatpak_command(command)
    if return_code != 0:
        return 1, output

    return 0, output


def check_remote_status(binary, name, remote, method):
    """
    Check the remote status.

    returns:
        status, type: int
            The status of the queried remote
            Possible values:
            0 - remote with name exists
            1 - remote with name doesn't exist
    """
    command = "{0} remote-list -d --{1}".format(binary, method)
    return_code, output = _flatpak_command(command)
    for line in output.splitlines():
        listed_remote = line.split()
        if listed_remote[0] == name:
            return 0
    return 1


def _flatpak_command(command):
    process = subprocess.Popen(
        command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = process.communicate()[0]

    return process.returncode, output


def main():
    # This module supports check mode
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
        supports_check_mode=True,
    )

    name = module.params['name']
    remote = module.params['remote']
    method = module.params['method']
    state = module.params['state']
    executable = module.params['executable']

    # We want to know if the user provided it or not, so we set default here
    if executable is None:
        executable = 'flatpak'

    binary = module.get_bin_path(executable, None)

    # When executable was provided and binary not found, warn user !
    if module.params['executable'] is not None and not binary:
        module.warn("Executable '%s' is not found on the system." % executable)

    binary = module.get_bin_path(executable, required=True)
    if remote is None:
        remote = ''

    status = check_remote_status(binary, name, remote, method)
    changed = False
    result = 0
    if state == 'present':
        if status == 0:
            changed = False
        else:
            result, output = add_remote(module, binary, name, remote, method)
            changed = True
    else:
        if status == 0:
            result, output = remove_remote(module, binary, name, method)
            changed = True
        else:
            changed = False

    if result == 0:
        module.exit_json(changed=changed)
    else:
        module.fail_json(msg=output, changed=changed)


if __name__ == '__main__':
    main()
