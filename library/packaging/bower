#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Austin O'Neil <austin.oneil@beardon.com>, Beardon Services
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


# You definitely need to change the top-level version added.  Possibly some other things as well.
DOCUMENTATION = '''
---
module: bower
short_description: Manage packages with Bower
description:
  - Manage packages with Bower
version_added: 1.2
author: Austin O'Neil
options:
  name:
    description:
      - The name of a library to install
    required: false
  path:
    description:
      - The base path where to install the libraries
    required: false
  version:
    description:
      - The version to be installed
    required: false
  global:
    description:
      - Install the library globally
    required: false
    default: no
    choices: [ "yes", "no" ]
  executable:
    description:
      - The executable location for Bower.
    required: false
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
      - The state of the library
    required: false
    default: present
    choices: [ "present", "absent", "latest" ]
'''

EXAMPLES = '''
description: Install "moment" package.
- bower: name=moment path=/app/location

description: Install "moment" package on version 1.6.1.
- bower: name=moment version=1.6.1 path=/app/location

description: Install "moment" package globally.
- bower: name=moment global=yes

description: Remove the globally package "moment".
- bower: name=moment global=yes state=absent

description: Install "moment" package from custom registry.
- bower: name=moment registry=http://registry.mysite.com

description: Install packages based on package.json.
- bower: path=/app/location

description: Update packages based on package.json to their latest version.
- bower: path=/app/location state=latest

description: Install packages based on package.json using the bower installed with nvm v0.10.1.
- bower: path=/app/location executable=/opt/nvm/v0.10.1/bin/bower state=present
'''

import os

try:
    import json
except ImportError:
    import simplejson as json

class Bower(object):#delta
    def __init__(self, module, **kwargs):
        self.module = module
        self.glbl = kwargs['glbl']
        self.name = kwargs['name']
        self.version = kwargs['version']
        self.path = kwargs['path']
        self.registry = kwargs['registry']
        self.production = kwargs['production']

        if kwargs['executable']:
            self.executable = kwargs['executable'].split(' ')
        else:
            self.executable = [module.get_bin_path('bower', True)]#delta

        if kwargs['version']:
            self.name_version = self.name + '@' + self.version
        else:
            self.name_version = self.name

    def _exec(self, args, run_in_check_mode=False, check_rc=True):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = self.executable + args

            if self.glbl:
                cmd.append('--global')
            if self.production:
                cmd.append('--production')
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
                pkg, other = re.split('\s|@', dep, 1)
                outdated.append(pkg)

        return outdated


def main():
    arg_spec = dict(
        name=dict(default=None),
        path=dict(default=None),
        version=dict(default=None),
        production=dict(default='no', type='bool'),
        executable=dict(default=None),
        registry=dict(default=None),
        state=dict(default='present', choices=['present', 'absent', 'latest'])
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

    if not path and not glbl:
        module.fail_json(msg='path must be specified when not using global')
    if state == 'absent' and not name:
        module.fail_json(msg='uninstalling a package is only available for named packages')

    bower = Bower(module, name=name, path=path, version=version, glbl=glbl, production=production, \
              executable=executable, registry=registry)

    changed = False
    if state == 'present':
        installed, missing = bower.list()
        if len(missing):
            changed = True
            bower.install()
    elif state == 'latest':
        installed, missing = bower.list()
        outdated = bower.list_outdated()
        if len(missing) or len(outdated):
            changed = True
            bower.install()
    else: #absent
        installed, missing = bower.list()
        if name in installed:
            changed = True
            bower.uninstall()

    module.exit_json(changed=changed)

# import module snippets
from ansible.module_utils.basic import *
main()

