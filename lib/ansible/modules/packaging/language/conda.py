#!/usr/bin/python

# Copyright: (c) 2018, Data to Decisions CRC
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: conda
short_description: Manage conda packages
description: >
  Manage packages via conda.
  Can install, update, and remove packages.
version_added: "2.6"
author: Terry Moschou (@tmoschou)
notes:
  - Requires the conda executable to already be installed.
requirements:
  - conda
options:
  name:
    description: >
      A list of package to install like C(foo). A package specification may be used
      for C(state: present) or C(state: latest) such as C(foo=1.0|1.2*).
    required: false

  state:
    description: >
      State in which to leave the conda package. Note that packages with
      a specification such as C(numpy=1.11*=*nomkl*) are always passed to the
      conda install command when C(state: present) in addition to C(state: latest),
      regardless if the current specification requirements are already met.
    required: false
    default: present
    choices:
      - present
      - absent
      - latest

  channels:
    description: >
      List of extra channels to use when installing packages. Specified
      in priority order
    required: false

  executable:
    description: >
      Path to the conda executable to use. Default is to search C(PATH) environment.
    required: false

  update_dependencies:
    description: >
      Whether to update dependencies when installing/updating. The default is to
      update dependencies if C(state: latest), otherwise not to if C(state: present)
    required: false
    type: bool

  prefix:
    description: >
      The full path to the conda environment to manage. Mutually exclusive to
      I(env_name).
    required: false

  env_name:
    description: >
      The conda environment name to manage. Mutually exclusive to I(prefix).
    required: false

  force:
    description: >
      Force install (even when package already installed) or forces removal of a
      package without removing packages that depend on it.
    required: false
    type: bool
"""

EXAMPLES = """
- name: install packages
  conda:
    name:
      - numpy=1.11*
      - matplotlib
    state: present
    update_dependencies: yes

- name: update conda itself
  conda:
    name: conda
    state: latest
    executable: "{{ conda_path }}/bin/conda"
    update_dependencies: yes

- name: uninstall packages
  conda:
    name: numpy
    state: absent
"""

RETURN = """
packages:
  description: a list of packages requested to be installed, updated or removed
  type: list
  returned: when the conda command line utility is called
  sample:
    - package1=1.2.*
    - package2

cmd:
  description: the conda command used to execute the state changing task
  type: list
  returned: when packages list is non-empty
  sample:
    - /usr/local/conda/bin/conda
    - install
    - --json
    - --yes
    - --quiet
    - --no-update-dependencies
    - install
    - conda
    - anaconda-client

stdout_json:
  description: the json result from the conda command line utility
  type: dict
  returned: when cmd is present
  sample:

stderr:
  description: error output from conda
  type: string
  returned: when cmd is present
"""

import json
import re
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import text_type
from ansible.module_utils._text import to_native


def run_conda_command(module, command):
    """Runs conda command line executable and parses the json response.

    :return: rc, stdout_json, stderr
    """

    rc, stdout, stderr = module.run_command(command)

    # Bug in 4.4.10 at least where --quiet is ignored when --json is present
    # and conda emits progress json blobs delimited by '\0'. E.g
    # {"fetch":"openssl 1.0.2n","finished":false,"maxval":1,"progress":0.9955}
    # Simply grab the last blob (if any), which is what we want
    stdout = stdout.split("\0")[-1]

    stdout_json = None
    try:
        stdout_json = json.loads(stdout)
    except Exception as e:
        module.fail_json(
            msg="Could not parse JSON {0}".format(to_native(e)),
            exception=traceback.format_exc(),
            cmd=command,
            rc=rc,
            stdout=stdout,
            stderr=stderr
        )

    return rc, stdout_json, stderr


def get_lookup_func(module, conda, conda_args):
    """Returns a function that accepts a single package name argument are
    returns a dictionary of 'installed' boolean status and 'version',
    'channel' details if installed.
    """

    list_command_prefix = [conda, 'list', '--full-name'] + conda_args
    pattern = re.compile(r"(?P<channel>.*::)?(?P<name>.*)-(?P<version>[^-]*)-(?P<revision>[^-]*)")

    def lookup(package):

        result = {'name': package}

        list_command = list_command_prefix + [package]
        rc, stdout_json, stderr = run_conda_command(module, list_command)

        # since we specified --full-name we only expect there to be one or zero hits
        if len(stdout_json) == 1:
            pkg = stdout_json[0]
            if isinstance(pkg, text_type):
                # Conda 4.2 format returns list of strings
                match = pattern.match(pkg)
                if match:
                    result['channel'] = match.group('channel')
                    result['version'] = match.group('version')
            else:
                # Conda 4.3+ format returns list of dictionaries
                result['channel'] = pkg['channel']
                result['version'] = pkg['version']

            result['installed'] = True
        elif len(stdout_json) == 0:
            result['installed'] = False
        else:
            module.fail_json(
                msg="Unexpected format of command result",
                cmd=list_command,
                rc=rc,
                stdout_json=stdout_json,
                stderr=stderr
            )

        return result

    return lookup


def add_mutable_command_args(module, conda_args):
    """Adds common command line args for install/remove sub-commands"""

    conda_args.extend(['--yes', '--quiet'])

    if module.params.get('force'):
        conda_args.append('--force')

    if module.check_mode:
        conda_args.append('--dry-run')

    channels = module.params['channels']
    if channels:
        for channel in channels:
            conda_args.append('--channel')
            conda_args.append(channel)


def did_change(result):
    """Determines if the conda command was state changing, or would
    have cause change if for not running in check mode.

    :param result:
        the json dictionary returned from the conda command
    :return:
        true if a package was installed/updated/uninstalled etc, false otherwise
    """

    actions = result.get('actions', {})

    # Bug in certain versions of conda. in dry-run mode, actions is wrapped in a singleton list
    if isinstance(actions, list):
        if actions:  # if not empty
            actions = actions[0]

    link = actions.get('LINK')  # packages installed or updated (new version/channel)
    unlink = actions.get('UNLINK')  # packages uninstalled or updated (old version/channel)
    symlink_conda = actions.get('SYMLINK_CONDA')

    return bool(link) or bool(unlink) or bool(symlink_conda)


def remove_package(module, conda, conda_args, to_remove):
    """Use conda to remove list of packages if they are installed."""

    if len(to_remove) == 0:
        module.exit_json(changed=False, msg="No packages to remove")

    add_mutable_command_args(module, conda_args)

    remove_command = [conda, 'remove'] + conda_args + to_remove
    rc, stdout_json, stderr = run_conda_command(module, remove_command)

    if rc != 0 or not stdout_json.get('success', False):
        module.fail_json(
            msg='failed to remove packages',
            packages=to_remove,
            rc=rc,
            cmd=remove_command,
            stdout_json=stdout_json,
            stderr=stderr
        )

    changed = did_change(stdout_json)
    module.exit_json(
        changed=changed,
        packages=to_remove,
        cmd=remove_command,
        stdout_json=stdout_json,
        stderr=stderr
    )


def install_package(module, conda, conda_args, to_install):
    """Install a packages consistent with its version specification, or install missing packages at
    the latest version if no version is specified.
    """
    if len(to_install) == 0:
        module.exit_json(changed=False, msg="no packages to install")

    add_mutable_command_args(module, conda_args)

    if module.params['update_dependencies'] is not None:
        if module.params['update_dependencies']:
            conda_args.append('--update-dependencies')
        else:
            conda_args.append('--no-update-dependencies')
    else:
        if module.params['state'] == 'latest':
            conda_args.append('--update-dependencies')
        else:  # state: present
            conda_args.append('--no-update-dependencies')

    install_command = [conda, 'install'] + conda_args + to_install
    rc, stdout_json, stderr = run_conda_command(module, install_command)

    if rc != 0 or not stdout_json.get('success', False):
        module.fail_json(
            msg='failed to install packages',
            packages=to_install,
            rc=rc,
            cmd=install_command,
            stdout_json=stdout_json,
            stderr=stderr
        )

    changed = did_change(stdout_json)
    module.exit_json(
        changed=changed,
        packages=to_install,
        cmd=install_command,
        stdout_json=stdout_json,
        stderr=stderr
    )


def main():

    module = AnsibleModule(
        argument_spec={
            'channels': {
                'default': None,
                'required': False,
                'type': 'list'
            },
            'env_name': {
                'required': False,
                'type': 'str'
            },
            'executable': {
                'default': None,
                'type': 'path'
            },
            'force': {
                'default': False,
                'type': 'bool'
            },
            'name': {
                'required': True,
                'type': 'list'
            },
            'prefix': {
                'required': False,
                'type': 'path'
            },
            'state': {
                'default': 'present',
                'required': False,
                'choices': [
                    'present',
                    'absent',
                    'latest'
                ]
            },
            'update_dependencies': {
                'required': False,
                'type': 'bool',
                'default': None
            }
        },
        mutually_exclusive=[
            ['prefix', 'env_name']
        ],
        supports_check_mode=True
    )

    conda = module.params['executable'] or module.get_bin_path("conda", required=True)

    packages = module.params['name']
    state = module.params['state']

    conda_args = ['--json']

    if module.params.get('prefix'):
        conda_args.extend(['--prefix', module.params['prefix']])
    elif module.params.get('env_name'):
        conda_args.extend(['--name', module.params['env_name']])

    get_package_status = get_lookup_func(module, conda, conda_args)

    if state == 'absent':

        lookups = [get_package_status(x) for x in packages]
        to_remove = [package['name'] for package in lookups if package['installed']]
        remove_package(module, conda, conda_args, to_remove)

    elif state == 'present':

        spec_chars_regex = re.compile(r'[ =<>!]')

        to_install = []
        for package in packages:
            # if a user specifies a spec, E.g. 'pkgname=1.2.*' we will always add it
            if spec_chars_regex.match(package):
                to_install.append(package)
            else:
                meta = get_package_status(package)
                if not meta['installed']:
                    to_install.append(package)

        install_package(module, conda, conda_args, to_install)

    elif state == 'latest':

        install_package(module, conda, conda_args, packages)


if __name__ == '__main__':
    main()
