#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Andrew Dunham <andrew@du.nham.ca>
# (c) 2013, Daniel Jaouen <dcj24@cornell.edu>
# (c) 2015-2017, Indrajit Raychaudhuri <irc+code@indrajit.com>
#
# Based on macports (Jimmy Tang <jcftang@gmail.com>)
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: homebrew
author:
    - "Indrajit Raychaudhuri (@indrajitr)"
    - "Daniel Jaouen (@danieljaouen)"
    - "Andrew Dunham (@andrew-d)"
requirements:
   - "python >= 2.6"
short_description: Package manager for Homebrew
description:
    - Manages Homebrew packages
version_added: "1.1"
options:
    name:
        description:
            - name of package to install/remove
        required: false
        default: None
        aliases: ['pkg', 'package', 'formula']
    path:
        description:
            - >
              ':' separated list of paths to search for 'brew' executable. Since A package (I(formula) in homebrew parlance) location is prefixed
              relative to the actual path of I(brew) command, providing an alternative I(brew) path enables managing different set of packages in an
              alternative location in the system.
        required: false
        default: '/usr/local/bin'
    state:
        description:
            - state of the package
        choices: [ 'head', 'latest', 'present', 'absent', 'linked', 'unlinked' ]
        required: false
        default: present
    update_homebrew:
        description:
            - update homebrew itself first
        required: false
        default: no
        choices: [ "yes", "no" ]
        aliases: ['update-brew']
    upgrade_all:
        description:
            - upgrade all homebrew packages
        required: false
        default: no
        choices: [ "yes", "no" ]
        aliases: ['upgrade']
    install_options:
        description:
            - options flags to install a package
        required: false
        default: null
        aliases: ['options']
        version_added: "1.4"
notes:  []
'''
EXAMPLES = '''
# Install formula foo with 'brew' in default path (C(/usr/local/bin))
- homebrew:
    name: foo
    state: present

# Install formula foo with 'brew' in alternate path C(/my/other/location/bin)
- homebrew:
    name: foo
    path: /my/other/location/bin
    state: present

# Update homebrew first and install formula foo with 'brew' in default path
- homebrew:
    name: foo
    state: present
    update_homebrew: yes

# Update homebrew first and upgrade formula foo to latest available with 'brew' in default path
- homebrew:
    name: foo
    state: latest
    update_homebrew: yes

# Update homebrew and upgrade all packages
- homebrew:
    update_homebrew: yes
    upgrade_all: yes

# Miscellaneous other examples
- homebrew:
    name: foo
    state: head

- homebrew:
    name: foo
    state: linked

- homebrew:
    name: foo
    state: absent

- homebrew:
    name: foo,bar
    state: absent

- homebrew:
    name: foo
    state: present
    install_options: with-baz,enable-debug
'''

from ansible.module_utils.homebrew import *

class Homebrew(HomebrewBase):
    '''A class to manage Homebrew packages.'''

    # class regexes ------------------------------------------------ {{{
    VALID_PACKAGE_CHARS = r'''
        \w                  # alphanumeric characters (i.e., [a-zA-Z0-9_])
        .                   # dots
        /                   # slash (for taps)
        \+                  # plusses
        -                   # dashes
        :                   # colons (for URLs)
        @                   # at-sign
    '''

    INVALID_PACKAGE_REGEX = negate_regex_group(VALID_PACKAGE_CHARS)
    # /class regexes ----------------------------------------------- }}}

    # class validations -------------------------------------------- {{{
    @classmethod
    def valid_package(cls, package):
        '''A valid package is either None or alphanumeric.'''

        if package is None:
            return True

        return (
            isinstance(package, basestring)
            and not cls.INVALID_PACKAGE_REGEX.search(package)
        )

    @classmethod
    def valid_state(cls, state):
        '''
        A valid state is one of:
            - None
            - installed
            - upgraded
            - head
            - linked
            - unlinked
            - absent
        '''

        if state is None:
            return True
        else:
            return (
                isinstance(state, basestring)
                and state.lower() in (
                    'installed',
                    'upgraded',
                    'head',
                    'linked',
                    'unlinked',
                    'absent',
                )
            )

    @classmethod
    def valid_module(cls, module):
        '''A valid module is an instance of AnsibleModule.'''

        return isinstance(module, AnsibleModule)

    # /class validations ------------------------------------------- }}}

    # class properties --------------------------------------------- {{{
    @property
    def current_package(self):
        return self._current_package

    @current_package.setter
    def current_package(self, package):
        if not self.valid_package(package):
            self._current_package = None
            self.failed = True
            self.message = 'Invalid package: {0}.'.format(package)
            raise HomebrewException(self.message)

        else:
            self._current_package = package
            return package
    # /class properties -------------------------------------------- }}}

    def __init__(self, module, path, packages=None, state=None,
                 update_homebrew=False, upgrade_all=False,
                 install_options=None):
        super(Homebrew, self).__init__()
        if not install_options:
            install_options = list()
        self._setup_status_vars()
        self._setup_instance_vars(module=module, path=path, packages=packages,
                                  state=state, update_homebrew=update_homebrew,
                                  upgrade_all=upgrade_all,
                                  install_options=install_options, )

        self._prep()

    # checks ------------------------------------------------------- {{{
    def _current_package_is_installed(self):
        if not self.valid_package(self.current_package):
            self.failed = True
            self.message = 'Invalid package: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

        cmd = [
            "{brew_path}".format(brew_path=self.brew_path),
            "info",
            self.current_package,
        ]
        rc, out, err = self.module.run_command(cmd)
        for line in out.split('\n'):
            if (
                re.search(r'Built from source', line)
                or re.search(r'Poured from bottle', line)
            ):
                return True

        return False

    def _current_package_is_outdated(self):
        if not self.valid_package(self.current_package):
            return False

        rc, out, err = self.module.run_command([
            self.brew_path,
            'outdated',
            self.current_package,
        ])

        return rc != 0

    def _current_package_is_installed_from_head(self):
        if not Homebrew.valid_package(self.current_package):
            return False
        elif not self._current_package_is_installed():
            return False

        rc, out, err = self.module.run_command([
            self.brew_path,
            'info',
            self.current_package,
        ])

        try:
            version_info = [line for line in out.split('\n') if line][0]
        except IndexError:
            return False

        return version_info.split(' ')[-1] == 'HEAD'
    # /checks ------------------------------------------------------ }}}

    # commands ----------------------------------------------------- {{{
    def _run(self):
        if self.update_homebrew:
            self._update_homebrew()

        if self.upgrade_all:
            self._upgrade_all()

        if self.packages:
            if self.state == 'installed':
                return self._install_packages()
            elif self.state == 'upgraded':
                return self._upgrade_packages()
            elif self.state == 'head':
                return self._install_packages()
            elif self.state == 'linked':
                return self._link_packages()
            elif self.state == 'unlinked':
                return self._unlink_packages()
            elif self.state == 'absent':
                return self._uninstall_packages()

    # updated -------------------------------- {{{
    def _update_homebrew(self):
        rc, out, err = self.module.run_command([
            self.brew_path,
            'update',
        ])
        if rc == 0:
            if out and isinstance(out, basestring):
                already_updated = any(
                    re.search(r'Already up-to-date.', s.strip(), re.IGNORECASE)
                    for s in out.split('\n')
                    if s
                )
                if not already_updated:
                    self.changed = True
                    self.message = 'Homebrew updated successfully.'
                else:
                    self.message = 'Homebrew already up-to-date.'

            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewException(self.message)
    # /updated ------------------------------- }}}

    # _upgrade_all --------------------------- {{{
    def _upgrade_all(self):
        rc, out, err = self.module.run_command([
            self.brew_path,
            'upgrade',
        ])
        if rc == 0:
            if not out:
                self.message = 'Homebrew packages already upgraded.'

            else:
                self.changed = True
                self.message = 'Homebrew upgraded.'

            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewException(self.message)
    # /_upgrade_all -------------------------- }}}

    # installed ------------------------------ {{{
    def _install_current_package(self):
        if not self.valid_package(self.current_package):
            self.failed = True
            self.message = 'Invalid package: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

        if self._current_package_is_installed():
            self.unchanged_count += 1
            self.message = 'Package already installed: {0}'.format(
                self.current_package,
            )
            return True

        if self.module.check_mode:
            self.changed = True
            self.message = 'Package would be installed: {0}'.format(
                self.current_package
            )
            raise HomebrewException(self.message)

        if self.state == 'head':
            head = '--HEAD'
        else:
            head = None

        opts = (
            [self.brew_path, 'install']
            + self.install_options
            + [self.current_package, head]
        )
        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if self._current_package_is_installed():
            self.changed_count += 1
            self.changed = True
            self.message = 'Package installed: {0}'.format(self.current_package)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewException(self.message)

    def _install_packages(self):
        for package in self.packages:
            self.current_package = package
            self._install_current_package()

        return True
    # /installed ----------------------------- }}}

    # upgraded ------------------------------- {{{
    def _upgrade_current_package(self):
        command = 'upgrade'

        if not self.valid_package(self.current_package):
            self.failed = True
            self.message = 'Invalid package: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

        if not self._current_package_is_installed():
            command = 'install'

        if self._current_package_is_installed() and not self._current_package_is_outdated():
            self.message = 'Package is already upgraded: {0}'.format(
                self.current_package,
            )
            self.unchanged_count += 1
            return True

        if self.module.check_mode:
            self.changed = True
            self.message = 'Package would be upgraded: {0}'.format(
                self.current_package
            )
            raise HomebrewException(self.message)

        opts = (
            [self.brew_path, command]
            + self.install_options
            + [self.current_package]
        )
        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if self._current_package_is_installed() and not self._current_package_is_outdated():
            self.changed_count += 1
            self.changed = True
            self.message = 'Package upgraded: {0}'.format(self.current_package)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewException(self.message)

    def _upgrade_all_packages(self):
        opts = (
            [self.brew_path, 'upgrade']
            + self.install_options
        )
        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.changed = True
            self.message = 'All packages upgraded.'
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewException(self.message)

    def _upgrade_packages(self):
        if not self.packages:
            self._upgrade_all_packages()
        else:
            for package in self.packages:
                self.current_package = package
                self._upgrade_current_package()
            return True
    # /upgraded ------------------------------ }}}

    # uninstalled ---------------------------- {{{
    def _uninstall_current_package(self):
        if not self.valid_package(self.current_package):
            self.failed = True
            self.message = 'Invalid package: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

        if not self._current_package_is_installed():
            self.unchanged_count += 1
            self.message = 'Package already uninstalled: {0}'.format(
                self.current_package,
            )
            return True

        if self.module.check_mode:
            self.changed = True
            self.message = 'Package would be uninstalled: {0}'.format(
                self.current_package
            )
            raise HomebrewException(self.message)

        opts = (
            [self.brew_path, 'uninstall']
            + self.install_options
            + [self.current_package]
        )
        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if not self._current_package_is_installed():
            self.changed_count += 1
            self.changed = True
            self.message = 'Package uninstalled: {0}'.format(self.current_package)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewException(self.message)

    def _uninstall_packages(self):
        for package in self.packages:
            self.current_package = package
            self._uninstall_current_package()

        return True
    # /uninstalled ----------------------------- }}}

    # linked --------------------------------- {{{
    def _link_current_package(self):
        if not self.valid_package(self.current_package):
            self.failed = True
            self.message = 'Invalid package: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

        if not self._current_package_is_installed():
            self.failed = True
            self.message = 'Package not installed: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

        if self.module.check_mode:
            self.changed = True
            self.message = 'Package would be linked: {0}'.format(
                self.current_package
            )
            raise HomebrewException(self.message)

        opts = (
            [self.brew_path, 'link']
            + self.install_options
            + [self.current_package]
        )
        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.changed_count += 1
            self.changed = True
            self.message = 'Package linked: {0}'.format(self.current_package)

            return True
        else:
            self.failed = True
            self.message = 'Package could not be linked: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

    def _link_packages(self):
        for package in self.packages:
            self.current_package = package
            self._link_current_package()

        return True
    # /linked -------------------------------- }}}

    # unlinked ------------------------------- {{{
    def _unlink_current_package(self):
        if not self.valid_package(self.current_package):
            self.failed = True
            self.message = 'Invalid package: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

        if not self._current_package_is_installed():
            self.failed = True
            self.message = 'Package not installed: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

        if self.module.check_mode:
            self.changed = True
            self.message = 'Package would be unlinked: {0}'.format(
                self.current_package
            )
            raise HomebrewException(self.message)

        opts = (
            [self.brew_path, 'unlink']
            + self.install_options
            + [self.current_package]
        )
        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.changed_count += 1
            self.changed = True
            self.message = 'Package unlinked: {0}'.format(self.current_package)

            return True
        else:
            self.failed = True
            self.message = 'Package could not be unlinked: {0}.'.format(self.current_package)
            raise HomebrewException(self.message)

    def _unlink_packages(self):
        for package in self.packages:
            self.current_package = package
            self._unlink_current_package()

        return True
    # /unlinked ------------------------------ }}}
    # /commands ---------------------------------------------------- }}}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(
                aliases=["pkg", "package", "formula"],
                required=False,
                type='list',
            ),
            path=dict(
                default="/usr/local/bin",
                required=False,
                type='path',
            ),
            state=dict(
                default="present",
                choices=[
                    "present", "installed",
                    "latest", "upgraded", "head",
                    "linked", "unlinked",
                    "absent", "removed", "uninstalled",
                ],
            ),
            update_homebrew=dict(
                default=False,
                aliases=["update-brew"],
                type='bool',
            ),
            upgrade_all=dict(
                default=False,
                aliases=["upgrade"],
                type='bool',
            ),
            install_options=dict(
                default=None,
                aliases=['options'],
                type='list',
            )
        ),
        supports_check_mode=True,
    )

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    p = module.params

    if p['name']:
        packages = p['name']
    else:
        packages = None

    path = p['path']
    if path:
        path = path.split(':')

    state = p['state']
    if state in ('present', 'installed'):
        state = 'installed'
    if state in ('head', ):
        state = 'head'
    if state in ('latest', 'upgraded'):
        state = 'upgraded'
    if state == 'linked':
        state = 'linked'
    if state == 'unlinked':
        state = 'unlinked'
    if state in ('absent', 'removed', 'uninstalled'):
        state = 'absent'

    update_homebrew = p['update_homebrew']
    upgrade_all = p['upgrade_all']
    p['install_options'] = p['install_options'] or []
    install_options = ['--{0}'.format(install_option)
                       for install_option in p['install_options']]

    brew = Homebrew(module=module, path=path, packages=packages,
                    state=state, update_homebrew=update_homebrew,
                    upgrade_all=upgrade_all, install_options=install_options)
    (failed, changed, message) = brew.run()
    if failed:
        module.fail_json(msg=message)
    else:
        module.exit_json(changed=changed, msg=message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
