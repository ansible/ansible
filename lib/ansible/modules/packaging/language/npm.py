#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Chris Hoffman <christopher.hoffman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: npm
short_description: Manage node.js packages with npm
description:
  - Manage node.js packages with Node Package Manager (npm)
version_added: 1.2
author: "Chris Hoffman (@chrishoffman)"
options:
  name:
    description:
      - The name of a node.js library to install
    required: false
  path:
    description:
      - The base path where to install the node.js libraries
    required: false
  version:
    description:
      - The version to be installed
    required: false
  global:
    description:
      - Install the node.js library globally
    required: false
    default: no
    type: bool
  executable:
    description:
      - The executable location for npm.
      - This is useful if you are using a version manager, such as nvm
    required: false
  ignore_scripts:
    description:
      - Use the C(--ignore-scripts) flag when installing.
    required: false
    type: bool
    default: no
    version_added: "1.8"
  unsafe_perm:
    description:
      - Use the C(--unsafe-perm) flag when installing.
    type: bool
    default: no
    version_added: "2.8"
  ci:
    description:
      - Install packages based on package-lock file, same as running npm ci
    type: bool
    default: no
    version_added: "2.8"
  production:
    description:
      - Install dependencies in production mode, excluding devDependencies
    required: false
    type: bool
    default: no
  registry:
    description:
      - The registry to install modules from.
    required: false
    version_added: "1.6"
  state:
    description:
      - The state of the node.js library
    required: false
    default: present
    choices: [ "present", "absent", "latest" ]
requirements:
    - npm installed in bin path (recommended /usr/local/bin)
'''

EXAMPLES = '''
- name: Install "coffee-script" node.js package.
  npm:
    name: coffee-script
    path: /app/location

- name: Install "coffee-script" node.js package on version 1.6.1.
  npm:
    name: coffee-script
    version: '1.6.1'
    path: /app/location

- name: Install "coffee-script" node.js package globally.
  npm:
    name: coffee-script
    global: yes

- name: Remove the globally package "coffee-script".
  npm:
    name: coffee-script
    global: yes
    state: absent

- name: Install "coffee-script" node.js package from custom registry.
  npm:
    name: coffee-script
    registry: 'http://registry.mysite.com'

- name: Install packages based on package.json.
  npm:
    path: /app/location

- name: Update packages based on package.json to their latest version.
  npm:
    path: /app/location
    state: latest

- name: Install packages based on package.json using the npm installed with nvm v0.10.1.
  npm:
    path: /app/location
    executable: /opt/nvm/v0.10.1/bin/npm
    state: present
'''

import os
import re

from ansible.module_utils.basic import AnsibleModule

import json


class Npm(object):
    def __init__(self, module, **kwargs):
        self.module = module
        self.glbl = kwargs['glbl']
        self.name = kwargs['name']
        self.version = kwargs['version']
        self.path = kwargs['path']
        self.registry = kwargs['registry']
        self.production = kwargs['production']
        self.ignore_scripts = kwargs['ignore_scripts']
        self.unsafe_perm = kwargs['unsafe_perm']
        self.state = kwargs['state']

        if kwargs['executable']:
            self.executable = kwargs['executable'].split(' ')
        else:
            self.executable = [module.get_bin_path('npm', True)]

        if kwargs['version'] and self.state != 'absent':
            self.name_version = self.name + '@' + str(self.version)
        else:
            self.name_version = self.name

    def _exec(self, args, run_in_check_mode=False, check_rc=True):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = self.executable + args

            if self.glbl:
                cmd.append('--global')
            if self.production and ('install' in cmd or 'update' in cmd):
                cmd.append('--production')
            if self.ignore_scripts:
                cmd.append('--ignore-scripts')
            if self.unsafe_perm:
                cmd.append('--unsafe-perm')
            if self.name:
                cmd.append(self.name_version)
            if self.registry:
                cmd.append('--registry')
                cmd.append(self.registry)

            # If path is specified, cd into that path and run the command.
            cwd = None
            if self.path:
                if not os.path.exists(self.path):
                    os.makedirs(self.path)
                if not os.path.isdir(self.path):
                    self.module.fail_json(msg="path %s is not a directory" % self.path)
                cwd = self.path

            rc, out, err = self.module.run_command(cmd, check_rc=check_rc, cwd=cwd)
            return out
        return ''

    def list(self):
        cmd = ['list', '--json', '--long']

        installed = list()
        missing = list()
        data = json.loads(self._exec(cmd, True, False))
        if 'dependencies' in data:
            for dep in data['dependencies']:
                if 'missing' in data['dependencies'][dep] and data['dependencies'][dep]['missing']:
                    missing.append(dep)
                elif 'invalid' in data['dependencies'][dep] and data['dependencies'][dep]['invalid']:
                    missing.append(dep)
                else:
                    installed.append(dep)
            if self.name and self.name not in installed:
                missing.append(self.name)
        # Named dependency not installed
        else:
            missing.append(self.name)

        return installed, missing

    def install(self):
        return self._exec(['install'])

    def ci_install(self):
        return self._exec(['ci'])

    def update(self):
        return self._exec(['update'])

    def uninstall(self):
        return self._exec(['uninstall'])

    def list_outdated(self):
        outdated = list()
        data = self._exec(['outdated'], True, False)
        for dep in data.splitlines():
            if dep:
                # node.js v0.10.22 changed the `npm outdated` module separator
                # from "@" to " ". Split on both for backwards compatibility.
                pkg, other = re.split(r'\s|@', dep, 1)
                outdated.append(pkg)

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
        unsafe_perm=dict(default=False, type='bool'),
        ci=dict(default=False, type='bool'),
    )
    arg_spec['global'] = dict(default='no', type='bool')
    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    name = module.params['name']
    path = module.params['path']
    version = module.params['version']
    glbl = module.params['global']
    production = module.params['production']
    executable = module.params['executable']
    registry = module.params['registry']
    state = module.params['state']
    ignore_scripts = module.params['ignore_scripts']
    unsafe_perm = module.params['unsafe_perm']
    ci = module.params['ci']

    if not path and not glbl:
        module.fail_json(msg='path must be specified when not using global')
    if state == 'absent' and not name:
        module.fail_json(msg='uninstalling a package is only available for named packages')

    npm = Npm(module, name=name, path=path, version=version, glbl=glbl, production=production,
              executable=executable, registry=registry, ignore_scripts=ignore_scripts,
              unsafe_perm=unsafe_perm, state=state)

    changed = False
    if ci:
        npm.ci_install()
        changed = True
    elif state == 'present':
        installed, missing = npm.list()
        if missing:
            changed = True
            npm.install()
    elif state == 'latest':
        installed, missing = npm.list()
        outdated = npm.list_outdated()
        if missing:
            changed = True
            npm.install()
        if outdated:
            changed = True
            npm.update()
    else:  # absent
        installed, missing = npm.list()
        if name in installed:
            changed = True
            npm.uninstall()

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
