#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Michael Warkentin <mwarkentin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: bower
short_description: Manage bower packages with bower
description:
  - Manage bower packages with bower
version_added: 1.9
author: "Michael Warkentin (@mwarkentin)"
options:
  name:
    description:
      - The name of a bower package to install
  offline:
    description:
      - Install packages from local cache, if the packages were installed before
    type: bool
    default: 'no'
  production:
    description:
      - Install with --production flag
    type: bool
    default: 'no'
    version_added: "2.0"
  path:
    description:
      - The base path where to install the bower packages
    required: true
  relative_execpath:
    description:
      - Relative path to bower executable from install path
    version_added: "2.1"
  state:
    description:
      - The state of the bower package
    default: present
    choices: [ "present", "absent", "latest" ]
  version:
    description:
      - The version to be installed
'''

EXAMPLES = '''
- name: Install "bootstrap" bower package.
  bower:
    name: bootstrap

- name: Install "bootstrap" bower package on version 3.1.1.
  bower:
    name: bootstrap
    version: '3.1.1'

- name: Remove the "bootstrap" bower package.
  bower:
    name: bootstrap
    state: absent

- name: Install packages based on bower.json.
  bower:
    path: /app/location

- name: Update packages based on bower.json to their latest version.
  bower:
    path: /app/location
    state: latest

# install bower locally and run from there
- npm:
    path: /app/location
    name: bower
    global: no
- bower:
    path: /app/location
    relative_execpath: node_modules/.bin
'''
import json
import os

from ansible.module_utils.basic import AnsibleModule


class Bower(object):
    def __init__(self, module, **kwargs):
        self.module = module
        self.name = kwargs['name']
        self.offline = kwargs['offline']
        self.production = kwargs['production']
        self.path = kwargs['path']
        self.relative_execpath = kwargs['relative_execpath']
        self.version = kwargs['version']

        if kwargs['version']:
            self.name_version = self.name + '#' + self.version
        else:
            self.name_version = self.name

    def _exec(self, args, run_in_check_mode=False, check_rc=True):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = []

            if self.relative_execpath:
                cmd.append(os.path.join(self.path, self.relative_execpath, "bower"))
                if not os.path.isfile(cmd[-1]):
                    self.module.fail_json(msg="bower not found at relative path %s" % self.relative_execpath)
            else:
                cmd.append("bower")

            cmd.extend(args)
            cmd.extend(['--config.interactive=false', '--allow-root'])

            if self.name:
                cmd.append(self.name_version)

            if self.offline:
                cmd.append('--offline')

            if self.production:
                cmd.append('--production')

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
        cmd = ['list', '--json']

        installed = list()
        missing = list()
        outdated = list()
        data = json.loads(self._exec(cmd, True, False))
        if 'dependencies' in data:
            for dep in data['dependencies']:
                dep_data = data['dependencies'][dep]
                if dep_data.get('missing', False):
                    missing.append(dep)
                elif ('version' in dep_data['pkgMeta'] and
                        'update' in dep_data and
                        dep_data['pkgMeta']['version'] != dep_data['update']['latest']):
                    outdated.append(dep)
                elif dep_data.get('incompatible', False):
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
        production=dict(default='no', type='bool'),
        path=dict(required=True, type='path'),
        relative_execpath=dict(default=None, required=False, type='path'),
        state=dict(default='present', choices=['present', 'absent', 'latest', ]),
        version=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    name = module.params['name']
    offline = module.params['offline']
    production = module.params['production']
    path = module.params['path']
    relative_execpath = module.params['relative_execpath']
    state = module.params['state']
    version = module.params['version']

    if state == 'absent' and not name:
        module.fail_json(msg='uninstalling a package is only available for named packages')

    bower = Bower(module, name=name, offline=offline, production=production, path=path, relative_execpath=relative_execpath, version=version)

    changed = False
    if state == 'present':
        installed, missing, outdated = bower.list()
        if missing:
            changed = True
            bower.install()
    elif state == 'latest':
        installed, missing, outdated = bower.list()
        if missing or outdated:
            changed = True
            bower.update()
    else:  # Absent
        installed, missing, outdated = bower.list()
        if name in installed:
            changed = True
            bower.uninstall()

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
