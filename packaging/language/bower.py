#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Michael Warkentin <mwarkentin@gmail.com>
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
module: bower
short_description: Manage bower packages with bower
description:
  - Manage bower packages with bower
version_added: 1.9
author: Michael Warkentin
options:
  name:
    description:
      - The name of a bower package to install
    required: false
  offline:
    description:
      - Install packages from local cache, if the packages were installed before
    required: false
    default: no
    choices: [ "yes", "no" ]
  path:
    description:
      - The base path where to install the bower packages
    required: true
  state:
    description:
      - The state of the bower package
    required: false
    default: present
    choices: [ "present", "absent", "latest" ]
  version:
    description:
      - The version to be installed
    required: false
'''

EXAMPLES = '''
description: Install "bootstrap" bower package.
- bower: name=bootstrap

description: Install "bootstrap" bower package on version 3.1.1.
- bower: name=bootstrap version=3.1.1

description: Remove the "bootstrap" bower package.
- bower: name=bootstrap state=absent

description: Install packages based on bower.json.
- bower: path=/app/location

description: Update packages based on bower.json to their latest version.
- bower: path=/app/location state=latest
'''


class Bower(object):
    def __init__(self, module, **kwargs):
        self.module = module
        self.name = kwargs['name']
        self.offline = kwargs['offline']
        self.path = kwargs['path']
        self.version = kwargs['version']

        if kwargs['version']:
            self.name_version = self.name + '#' + self.version
        else:
            self.name_version = self.name

    def _exec(self, args, run_in_check_mode=False, check_rc=True):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = ["bower"] + args

            if self.name:
                cmd.append(self.name_version)

            if self.offline:
                cmd.append('--offline')

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
        cmd = ['list', '--json', '--config.interactive=false', '--allow-root']

        installed = list()
        missing = list()
        outdated = list()
        data = json.loads(self._exec(cmd, True, False))
        if 'dependencies' in data:
            for dep in data['dependencies']:
                if 'missing' in data['dependencies'][dep] and data['dependencies'][dep]['missing']:
                    missing.append(dep)
                elif data['dependencies'][dep]['pkgMeta']['version'] != data['dependencies'][dep]['update']['latest']:
                    outdated.append(dep)
                elif 'incompatible' in data['dependencies'][dep] and data['dependencies'][dep]['incompatible']:
                    outdated.append(dep)
                else:
                    installed.append(dep)
        # Named dependency not installed
        else:
            missing.append(self.name)

        return installed, missing, outdated

    def install(self):
        return self._exec(['install'])

    def update(self):
        return self._exec(['update'])

    def uninstall(self):
        return self._exec(['uninstall'])


def main():
    arg_spec = dict(
        name=dict(default=None),
        offline=dict(default='no', type='bool'),
        path=dict(required=True),
        state=dict(default='present', choices=['present', 'absent', 'latest', ]),
        version=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    name = module.params['name']
    offline = module.params['offline']
    path = module.params['path']
    state = module.params['state']
    version = module.params['version']

    if state == 'absent' and not name:
        module.fail_json(msg='uninstalling a package is only available for named packages')

    bower = Bower(module, name=name, offline=offline, path=path, version=version)

    changed = False
    if state == 'present':
        installed, missing, outdated = bower.list()
        if len(missing):
            changed = True
            bower.install()
    elif state == 'latest':
        installed, missing, outdated = bower.list()
        if len(missing) or len(outdated):
            changed = True
            bower.update()
    else:  # Absent
        installed, missing, outdated = bower.list()
        if name in installed:
            changed = True
            bower.uninstall()

    module.exit_json(changed=changed)

# Import module snippets
from ansible.module_utils.basic import *
main()
