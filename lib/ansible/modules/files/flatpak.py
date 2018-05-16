#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017 John Kwiatkoski (@JayKayy) <jkwiat40@gmail.com>
# Copyright: (c) 2018 Alexander Bethke (@oolongbrothers) <oolongbrothers@gmx.net>
# Copyright: (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: flatpak
short_description: Manage flatpaks
description:
    - Allows users to add or remove flatpaks.
    - See the M(flatpak_remote) module for managing flatpak remotes.
version_added: '2.6'
author:
- John Kwiatkoski (@jaykayy)
- Alexander Bethke Kwiatkoski (@oolongbrothers)
requirements:
- flatpak
notes:
- The C(flatpak_remote) requires the C(flatpak) binary the be installed on the managed host.
options:
  name:
    description:
    - The name of the flatpak to manage
    - When I(state) is set to C(present), I(name) can be specified as an C(http(s)) URL to a
      C(flatpakref)-file or the unique reverse DNS name that identifies a flatpak.
    - An example for a reverse DNS name is I(org.gnome.gedit).
    - When set to C(absent), it is recommended to specify the name in the reverse DNS format.
    - When supplying an C(http(s)) URL with C(state=absent), the module will try to match the
      installed flatpak based on the name of the flatpakref to remove it. However, there is no
      guarantee that the names of the flatpakref file and the reverse DNS name of the installed
      flatpak do match.
    required: true
  executable:
    description:
    - The path to the C(flatpak) executable to use
    default: flatpak
  state:
    description:
    - Set to C(present) will install the flatpak and/or I(remote).
    - Set to C(absent) will remove the flatpak and/or I(remote).
    choices: [ absent, present ]
    default: present
  remote:
    description:
    - The repository remote to install the flatpak from
      See the M(flatpak_remote) module for managing flatpak remotes.
    default: flathub
  method:
    description:
    - The installation method to use
    - Defines if the I(flatpak) is supposed to be installed globally for the whole C(system)
      or for the current C(user) only.
    choices: [ system, user ]
    default: system
'''

EXAMPLES = r'''
- name: Install the spotify flatpak
  flatpak:
    name:  https://s3.amazonaws.com/alexlarsson/spotify-repo/spotify.flatpakref
    state: present

- name: Install the gedit flatpak package
  flatpak:
    name: https://git.gnome.org/browse/gnome-apps-nightly/plain/gedit.flatpakref
    state: present

- name: Remove the gedit flatpak package
  flatpak:
    name: org.gnome.gedit
    state: absent

- name: Install the gedit package from flathub for current user
  flatpak:
    name: org.gnome.gedit
    state: present
    remote: flathub
  method: user

- name: Install a flatpack stored in another remote
  flatpak:
    name: org.test.myapp
    state: present
    remote: myrepository
'''

RETURN = r'''
reason:
  description: On failure, the output for the failure
  returned: failed
  type: string
  sample: error while installing...
'''

import subprocess
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.basic import AnsibleModule


def install_flat(module, binary, remote, name, method):
    """Add a new flatpak."""
    global result
    if 'http://' in name or 'https://' in name:
        command = "{0} install --{1} -y {2}".format(binary, method, name)
    else:
        command = "{0} install --{1} -y {2} {3}".format(binary, method, remote, name)
    _flatpak_command(module, module.check_mode, command)
    result['changed'] = True


def uninstall_flat(module, binary, name, method):
    """Remove an existing flatpak."""
    global result
    installed_flat_name = _match_installed_flat_name(module, binary, name, method)
    command = "{0} uninstall --{1} {2}".format(binary, method, installed_flat_name)
    _flatpak_command(module, module.check_mode, command)
    result['changed'] = True


def flatpak_exists(module, binary, name, method):
    """Check if the flatpak is installed."""
    command = "{0} list --{1} --app".format(binary, method)
    output = _flatpak_command(module, False, command)
    name = _parse_flatpak_name(name).lower()
    if name in output.lower():
        return True
    return False


def _match_installed_flat_name(module, binary, name, method):
    # This is a difficult function because it seems there
    # is no naming convention for the flatpakref to what
    # the installed flatpak will be named.
    global result
    command = "{0} list --{1} --app".format(binary, method)
    output = _flatpak_command(module, False, command)
    parsed_name = _parse_flatpak_name(name)
    for row in output.split('\n'):
        if parsed_name.lower() in row.lower():
            return row.split()[0]

    result['msg'] = "Flatpak removal failed: Could not match any installed flatpaks to " +\
        "the name `{0}`. ".format(_parse_flatpak_name(name)) +\
        "If you used a URL, try using the reverse DNS name of the flatpak"
    module.fail_json(**result)


def _parse_flatpak_name(name):
    if 'http://' in name or 'https://' in name:
        file_name = urlparse(name).path.split('/')[-1]
        file_name_without_extension = file_name.split('.')[0:-1]
        common_name = ".".join(file_name_without_extension)
    else:
        common_name = name
    return common_name


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
    # This module supports check mode
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            remote=dict(type='str', default='flathub'),
            method=dict(type='str', default='system',
                        choices=['user', 'system']),
            state=dict(type='str', default='present',
                       choices=['absent', 'present']),
            executable=dict(type='path', default='flatpak')
        ),
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']
    remote = module.params['remote']
    method = module.params['method']
    executable = module.params['executable']
    binary = module.get_bin_path(executable, None)

    global result
    result = dict(
        changed=False
    )

    # If the binary was not found, fail the operation
    if not binary:
        module.fail_json(msg="Executable '%s' was not found on the system." % executable, **result)

    if state == 'present' and not flatpak_exists(module, binary, name, method):
        install_flat(module, binary, remote, name, method)
    elif state == 'absent' and flatpak_exists(module, binary, name, method):
        uninstall_flat(module, binary, name, method)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
