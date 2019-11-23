#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017 David Gunter <david.gunter@tivix.com>
# Copyright (c) 2017 Chris Hoffman <christopher.hoffman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: yarn
short_description: Manage node.js packages with Yarn
description:
  - Manage node.js packages with the Yarn package manager (https://yarnpkg.com/)
version_added: "2.6"
author:
  - "David Gunter (@verkaufer)"
  - "Chris Hoffman (@chrishoffman), creator of NPM Ansible module)"
options:
  name:
    description:
      - The name of a node.js library to install
      - If omitted all packages in package.json are installed.
    required: false
  path:
    description:
      - The base path where Node.js libraries will be installed.
      - This is where the node_modules folder lives.
    required: false
  version:
    description:
      - The version of the library to be installed.
      - Must be in semver format. If "latest" is desired, use "state" arg instead
    required: false
  global:
    description:
      - Install the node.js library globally
    required: false
    default: no
    type: bool
  executable:
    description:
      - The executable location for yarn.
    required: false
  ignore_scripts:
    description:
      - Use the --ignore-scripts flag when installing.
    required: false
    type: bool
    default: no
  production:
    description:
      - Install dependencies in production mode.
      - Yarn will ignore any dependencies under devDependencies in package.json
    required: false
    type: bool
    default: no
  registry:
    description:
      - The registry to install modules from.
    required: false
  state:
    description:
      - Installation state of the named node.js library
      - If absent is selected, a name option must be provided
    required: false
    default: present
    choices: [ "present", "absent", "latest" ]
requirements:
    - Yarn installed in bin path (typically /usr/local/bin)
'''

EXAMPLES = '''
- name: Install "imagemin" node.js package.
  yarn:
    name: imagemin
    path: /app/location

- name: Install "imagemin" node.js package on version 5.3.1
  yarn:
    name: imagemin
    version: '5.3.1'
    path: /app/location

- name: Install "imagemin" node.js package globally.
  yarn:
    name: imagemin
    global: yes

- name: Remove the globally-installed package "imagemin".
  yarn:
    name: imagemin
    global: yes
    state: absent

- name: Install "imagemin" node.js package from custom registry.
  yarn:
    name: imagemin
    registry: 'http://registry.mysite.com'

- name: Install packages based on package.json.
  yarn:
    path: /app/location

- name: Update all packages in package.json to their latest version.
  yarn:
    path: /app/location
    state: latest
'''

RETURN = '''
changed:
    description: Whether Yarn changed any package data
    returned: always
    type: bool
    sample: true
msg:
    description: Provides an error message if Yarn syntax was incorrect
    returned: failure
    type: str
    sample: "Package must be explicitly named when uninstalling."
invocation:
    description: Parameters and values used during execution
    returned: success
    type: dict
    sample: {
            "module_args": {
                "executable": null,
                "globally": false,
                "ignore_scripts": false,
                "name": null,
                "path": "/some/path/folder",
                "production": false,
                "registry": null,
                "state": "present",
                "version": null
            }
        }
out:
    description: Output generated from Yarn with emojis removed.
    returned: always
    type: str
    sample: "yarn add v0.16.1[1/4] Resolving packages...[2/4] Fetching packages...[3/4] Linking dependencies...[4/4]
    Building fresh packages...success Saved lockfile.success Saved 1 new dependency..left-pad@1.1.3 Done in 0.59s."
'''

import os
import re
import json

from ansible.module_utils.basic import AnsibleModule


class Yarn(object):

    DEFAULT_GLOBAL_INSTALLATION_PATH = '~/.config/yarn/global'

    def __init__(self, module, **kwargs):
        self.module = module
        self.globally = kwargs['globally']
        self.name = kwargs['name']
        self.version = kwargs['version']
        self.path = kwargs['path']
        self.registry = kwargs['registry']
        self.production = kwargs['production']
        self.ignore_scripts = kwargs['ignore_scripts']

        # Specify a version of package if version arg passed in
        self.name_version = None

        if kwargs['executable']:
            self.executable = kwargs['executable'].split(' ')
        else:
            self.executable = [module.get_bin_path('yarn', True)]

        if kwargs['version'] and self.name is not None:
            self.name_version = self.name + '@' + str(self.version)
        elif self.name is not None:
            self.name_version = self.name

    def _exec(self, args, run_in_check_mode=False, check_rc=True):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):

            if self.globally:
                # Yarn global arg is inserted before the command (e.g. `yarn global {some-command}`)
                args.insert(0, 'global')

            cmd = self.executable + args

            if self.production:
                cmd.append('--production')
            if self.ignore_scripts:
                cmd.append('--ignore-scripts')
            if self.registry:
                cmd.append('--registry')
                cmd.append(self.registry)

            # always run Yarn without emojis when called via Ansible
            cmd.append('--no-emoji')

            # If path is specified, cd into that path and run the command.
            cwd = None
            if self.path and not self.globally:
                if not os.path.exists(self.path):
                    # Module will make directory if not exists.
                    os.makedirs(self.path)
                if not os.path.isdir(self.path):
                    self.module.fail_json(msg="Path provided %s is not a directory" % self.path)
                cwd = self.path

                if not os.path.isfile(os.path.join(self.path, 'package.json')):
                    self.module.fail_json(msg="Package.json does not exist in provided path.")

            rc, out, err = self.module.run_command(cmd, check_rc=check_rc, cwd=cwd)
            return out, err

        return ''

    def list(self):
        cmd = ['list', '--depth=0', '--json']

        installed = list()
        missing = list()

        if not os.path.isfile(os.path.join(self.path, 'yarn.lock')):
            missing.append(self.name)
            return installed, missing

        result, error = self._exec(cmd, True, False)

        if error:
            self.module.fail_json(msg=error)

        data = json.loads(result)
        try:
            dependencies = data['data']['trees']
        except KeyError:
            missing.append(self.name)
            return installed, missing

        for dep in dependencies:
            name, version = dep['name'].split('@')
            installed.append(name)

        if self.name not in installed:
            missing.append(self.name)

        return installed, missing

    def install(self):
        if self.name_version:
            # Yarn has a separate command for installing packages by name...
            return self._exec(['add', self.name_version])
        # And one for installing all packages in package.json
        return self._exec(['install', '--non-interactive'])

    def update(self):
        return self._exec(['upgrade', '--latest'])

    def uninstall(self):
        return self._exec(['remove', self.name])

    def list_outdated(self):
        outdated = list()

        if not os.path.isfile(os.path.join(self.path, 'yarn.lock')):
            return outdated

        cmd_result, err = self._exec(['outdated', '--json'], True, False)
        if err:
            self.module.fail_json(msg=err)

        outdated_packages_data = cmd_result.splitlines()[1]

        data = json.loads(outdated_packages_data)

        try:
            outdated_dependencies = data['data']['body']
        except KeyError:
            return outdated

        for dep in outdated_dependencies:
            # Outdated dependencies returned as a list of lists, where
            # item at index 0 is the name of the dependency
            outdated.append(dep[0])
        return outdated


def main():
    arg_spec = dict(
        name=dict(default=None),
        path=dict(default=None, type='path'),
        version=dict(default=None),
        production=dict(default='no', type='bool'),
        executable=dict(default=None, type='path'),
        registry=dict(default=None),
        state=dict(default='present', choices=['present', 'absent', 'latest']),
        ignore_scripts=dict(default=False, type='bool'),
    )
    arg_spec['global'] = dict(default='no', type='bool')
    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    name = module.params['name']
    path = module.params['path']
    version = module.params['version']
    globally = module.params['global']
    production = module.params['production']
    executable = module.params['executable']
    registry = module.params['registry']
    state = module.params['state']
    ignore_scripts = module.params['ignore_scripts']

    # When installing globally, users should not be able to define a path for installation.
    # Require a path if global is False, though!
    if path is None and globally is False:
        module.fail_json(msg='Path must be specified when not using global arg')
    elif path and globally is True:
        module.fail_json(msg='Cannot specify path if doing global installation')

    if state == 'absent' and not name:
        module.fail_json(msg='Package must be explicitly named when uninstalling.')
    if state == 'latest':
        version = 'latest'

    # When installing globally, use the defined path for global node_modules
    if globally:
        path = Yarn.DEFAULT_GLOBAL_INSTALLATION_PATH

    yarn = Yarn(module,
                name=name,
                path=path,
                version=version,
                globally=globally,
                production=production,
                executable=executable,
                registry=registry,
                ignore_scripts=ignore_scripts)

    changed = False
    out = ''
    err = ''
    if state == 'present':

        if not name:
            changed = True
            out, err = yarn.install()
        else:
            installed, missing = yarn.list()
            if len(missing):
                changed = True
                out, err = yarn.install()

    elif state == 'latest':

        if not name:
            changed = True
            out, err = yarn.install()
        else:
            installed, missing = yarn.list()
            outdated = yarn.list_outdated()
            if len(missing):
                changed = True
                out, err = yarn.install()
            if len(outdated):
                changed = True
                out, err = yarn.update()
    else:
        # state == absent
        installed, missing = yarn.list()
        if name in installed:
            changed = True
            out, err = yarn.uninstall()

    module.exit_json(changed=changed, out=out, err=err)


if __name__ == '__main__':
    main()
