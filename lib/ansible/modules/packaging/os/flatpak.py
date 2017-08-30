#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017 John Kwiatkoski
# Copyright: (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: flatpak
short_description: Install and remove flatpaks
description:
    - The flatpak module allows users to manage installation and removal of flatpaks.
version_added: '2.4'
author:
- John Kwiatkoski (@jaykayy)
requirements:
- flatpak
options:
  name:
    description:
    - When I(state) is set to C(present), I(name) is best used as `http(s)` url format.
      When set to C(absent) the same `http(s)` will try to remove it using the
      name of the flatpakref. However, there is no naming standard between
      names of flatpakrefs and what the reverse DNS name of the installed flatpak
      will be. Given that, it is best to use the http(s) url for I(state=present)
      and the reverse DNS I(state=absent). Alternatively reverse dns format can optimally
      be used with I(state=absent), ex. I(name=org.gnome.gedit).
    required: true
  executable:
    description:
    - The path to the C(flatpak) executable to use.
    default: flatpak
  state:
    description:
    - Set to C(present) will install the flatpak and/or I(remote).
    - Set to C(absent) will remove the flatpak and/or I(remote).
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

- name: Remove the gedit flatpak package
  flatpak:
    name: org.gnome.gedit
    state: absent

- name: Remove the gedit package
  flatpak:
    name: org.gnome.gedit
    state: absent
'''

RETURN = r'''
reason:
  description: On failure, the output for the failure
  returned: failed
  type: string
  sample: error while installing...
name:
  description: Name of flatpak given for the operation
  returned: always
  type: string
  sample: https://git.gnome.org/.../gnome-apps/gedit.flatpakref
remote:
  description: Remote of flatpak given for the operation
  returned: always
  type: string
  sample: https://sdk.gnome.org/gnome-apps.flatpakrepo
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
#from urlparse import urlparse


def install_flat(module, binary, flat):
    installed = is_present_flat(module, binary, flat)
    # Check if any changes would be made but don't actually make
    # those changes
    if installed:
        module.exit_json(changed=False)
    else:
        if module.check_mode:
            module.exit_json(changed=True)

        command = "{} install -y --from {}".format(binary, flat)

        output = flatpak_command(module, command)
        return 0, output


def uninstall_flat(module, binary, flat):
    # This is a difficult function because it seems there
    # is no naming convention for the flatpakref to what
    # the installed flatpak will be named.
    installed = is_present_flat(module, binary, flat)
    # Check if any changes would be made but don't actually make
    # those changes
    if not installed:
        module.exit_json(changed=False)
    else:
        if module.check_mode:
            module.exit_json(changed=True)

    command = "{} list --app".format(binary)
    result = module.run_command(command.split())
    for row in result[1].split('\n'):
        if parse_flat(flat) in row:
            installed_flat_name = row.split(' ')[0]
    command = "{} uninstall {}".format(binary, installed_flat_name)
    output = flatpak_command(module, command)
    return 0, output


def parse_flat(name):
    if 'http://' in name or 'https://' in name:
        common_name = name.split('/')[-1].split('.')[0]
        # common_name = urlparse(name).path.split('/')[-1].split('.')[0]
    else:
        common_name = name

    return common_name


def is_present_flat(module, binary, name):
    command = "{} list --app".format(binary)
    flat = parse_flat(name).lower()
    output = flatpak_command(module, command)
    if flat in output.lower():
        return True
    return False


def flatpak_command(module, command):
    result = module.run_command(command.split())
    return result[1]


def main():
    # This module supports check mode
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present',
                       choices=['absent', 'present']),
            executable=dict(type='path'),  # No default on purpose
        ),
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']
    executable = module.params['executable']

    # We want to know if the user provided it or not, so we set default here
    if executable is None:
        executable = 'flatpak'

    binary = module.get_bin_path(executable, None)

    # When executable was provided and binary not found, warn user !
    if module.params['executable'] is not None and not binary:
        module.warn("Executable '%s' is not found on the system." % executable)

    if state == 'present':
        result = install_flat(module, binary, name)
    elif state == 'absent':
        result = uninstall_flat(module, binary, name)
    module.exit_json(changed=True, msg=result[1])


if __name__ == '__main__':
    main()
