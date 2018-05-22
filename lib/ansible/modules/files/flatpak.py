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
version_added: '2.6'
short_description: Manage flatpaks
description:
- Allows users to add or remove flatpaks.
- See the M(flatpak_remote) module for managing flatpak remotes.
author:
- John Kwiatkoski (@jaykayy)
- Alexander Bethke (@oolongbrothers)
requirements:
- flatpak
options:
  executable:
    description:
    - The path to the C(flatpak) executable to use.
    - By default, this module looks for the C(flatpak) executable on the path.
    default: flatpak
  method:
    description:
    - The installation method to use.
    - Defines if the I(flatpak) is supposed to be installed globally for the whole C(system)
      or only for the current C(user).
    choices: [ system, user ]
    default: system
  name:
    description:
    - The name of the flatpak to manage.
    - When used with I(state=present), I(name) can be specified as an C(http(s)) URL to a
      C(flatpakref) file or the unique reverse DNS name that identifies a flatpak.
    - When suppying a reverse DNS name, you can use the I(remote) option to specify on what remote
      to look for the flatpak. An example for a reverse DNS name is C(org.gnome.gedit).
    - When used with I(state=absent), it is recommended to specify the name in the reverse DNS
      format.
    - When supplying an C(http(s)) URL with I(state=absent), the module will try to match the
      installed flatpak based on the name of the flatpakref to remove it. However, there is no
      guarantee that the names of the flatpakref file and the reverse DNS name of the installed
      flatpak do match.
    required: true
  remote:
    description:
    - The flatpak remote (repository) to install the flatpak from.
    - By default, C(flathub) is assumed, but you do need to add the flathub flatpak_remote before
      you can use this.
    - See the M(flatpak_remote) module for managing flatpak remotes.
    default: flathub
  state:
    description:
    - Indicates the desired package state.
    choices: [ absent, present ]
    default: present
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

- name: Install the gedit package from flathub for current user
  flatpak:
    name: org.gnome.gedit
    state: present
  method: user

- name: Install the Gnome Calendar flatpak from the gnome remote system-wide
  flatpak:
    name: org.gnome.Calendar
    state: present
    remote: gnome

- name: Remove the gedit flatpak
  flatpak:
    name: org.gnome.gedit
    state: absent
'''

RETURN = r'''
command:
  description: The exact flatpak command that was executed
  returned: When a flatpak command has been executed
  type: string
  sample: "/usr/bin/flatpak install --user -y flathub org.gnome.Calculator"
msg:
  description: Module error message
  returned: failure
  type: string
  sample: "Executable '/usr/local/bin/flatpak' was not found on the system."
rc:
  description: Return code from flatpak binary
  returned: When a flatpak command has been executed
  type: int
  sample: 0
stderr:
  description: Error output from flatpak binary
  returned: When a flatpak command has been executed
  type: string
  sample: "error: Error searching remote flathub: Can't find ref org.gnome.KDE"
stdout:
  description: Output from flatpak binary
  returned: When a flatpak command has been executed
  type: string
  sample: "org.gnome.Calendar/x86_64/stable\tcurrent\norg.gnome.gitg/x86_64/stable\tcurrent\n"
'''

import subprocess
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.basic import AnsibleModule


def install_flat(module, binary, remote, name, method):
    """Add a new flatpak."""
    global result
    if name.startswith('http://') or name.startswith('https://'):
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
    if name.startswith('http://') or name.startswith('https://'):
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
