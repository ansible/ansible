#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Chris Hoffman <christopher.hoffman@gmail.com>
#
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
    choices: [ "yes", "no" ]
  executable:
    description:
      - The executable location for npm.
      - This is useful if you are using a version manager, such as nvm
    required: false
  ignore_scripts:
    description:
      - Use the --ignore-scripts flag when installing.
    required: false
    choices: [ "yes", "no" ]
    default: no
    version_added: "1.8"
  production:
    description:
      - Install dependencies in production mode, excluding devDependencies
    required: false
    choices: [ "yes", "no" ]
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
'''

EXAMPLES = '''
description: Install "coffee-script" node.js package.
- npm: name=coffee-script path=/app/location

description: Install "coffee-script" node.js package on version 1.6.1.
- npm: name=coffee-script version=1.6.1 path=/app/location

description: Install "coffee-script" node.js package globally.
- npm: name=coffee-script global=yes

description: Remove the globally package "coffee-script".
- npm: name=coffee-script global=yes state=absent

description: Install "coffee-script" node.js package from custom registry.
- npm: name=coffee-script registry=http://registry.mysite.com

description: Install packages based on package.json.
- npm: path=/app/location

description: Update packages based on package.json to their latest version.
- npm: path=/app/location state=latest

description: Install packages based on package.json using the npm installed with nvm v0.10.1.
- npm: path=/app/location executable=/opt/nvm/v0.10.1/bin/npm state=present
'''

import os

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # Let snippet from module_utils/basic.py return a proper error in this case
        pass


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

        if kwargs['executable']:
            self.executable = kwargs['executable'].split(' ')
        else:
            self.executable = [module.get_bin_path('npm', True)]

        if kwargs['version']:
            self.name_version = self.name + '@' + str(self.version)
        else:
            self.name_version = self.name

    def _exec(self, args, run_in_check_mode=False, check_rc=True):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = self.executable + args

            if self.glbl:
                cmd.append('--global')
            if self.production:
                cmd.append('--production')
            if self.ignore_scripts:
                cmd.append('--ignore-scripts')
            if self.name:
                cmd.append(self.name_version)
            if self.registry:
                cmd.append('--registry')
                cmd.append(self.registry)

            #If path is specified, cd into that path and run the command.
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
        cmd = ['list', '--json']

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
        #Named dependency not installed
        else:
            missing.append(self.name)

        return installed, missing

    def install(self):
        return self._exec(['install'])

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
                pkg, other = re.split('\s|@', dep, 1)
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

    if not path and not glbl:
        module.fail_json(msg='path must be specified when not using global')
    if state == 'absent' and not name:
        module.fail_json(msg='uninstalling a package is only available for named packages')

    npm = Npm(module, name=name, path=path, version=version, glbl=glbl, production=production, \
              executable=executable, registry=registry, ignore_scripts=ignore_scripts)

    changed = False
    if state == 'present':
        installed, missing = npm.list()
        if len(missing):
            changed = True
            npm.install()
    elif state == 'latest':
        installed, missing = npm.list()
        outdated = npm.list_outdated()
        if len(missing) or len(outdated):
            changed = True
            npm.update()
    else: #absent
        installed, missing = npm.list()
        if name in installed:
            changed = True
            npm.uninstall()

    module.exit_json(changed=changed)

# import module snippets
from ansible.module_utils.basic import *
main()
