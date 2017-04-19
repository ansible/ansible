#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Daniel Jaouen <dcj24@cornell.edu>
# (c) 2016-2017, Indrajit Raychaudhuri <irc+code@indrajit.com>
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
module: homebrew_cask
author:
    - "Indrajit Raychaudhuri (@indrajitr)"
    - "Daniel Jaouen (@danieljaouen)"
    - "Enric Lluelles (@enriclluelles)"
requirements:
   - "python >= 2.6"
short_description: Install/uninstall homebrew casks.
description:
    - Manages Homebrew casks.
version_added: "1.6"
options:
    name:
        description:
            - name of cask to install/remove
        required: true
        aliases: ['pkg', 'package', 'cask']
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
            - state of the cask
        choices: [ 'present', 'absent' ]
        required: false
        default: present
    update_homebrew:
        description:
            - update homebrew itself first. Note that C(brew cask update) is
              a synonym for C(brew update).
        required: false
        default: no
        choices: [ "yes", "no" ]
        aliases: ['update-brew']
        version_added: "2.2"
    install_options:
        description:
            - options flags to install a package
        required: false
        default: null
        aliases: ['options']
        version_added: "2.2"
'''
EXAMPLES = '''
- homebrew_cask:
    name: alfred
    state: present

- homebrew_cask:
    name: alfred
    state: absent

- homebrew_cask:
    name: alfred
    state: present
    install_options: 'appdir=/Applications'

- homebrew_cask:
    name: alfred
    state: present
    install_options: 'debug,appdir=/Applications'

- homebrew_cask:
    name: alfred
    state: absent
    install_options: force
'''

from ansible.module_utils.homebrew import *

# exceptions -------------------------------------------------------------- {{{
class HomebrewCaskException(Exception):
    pass
# /exceptions ------------------------------------------------------------- }}}

class HomebrewCask(HomebrewBase):
    '''A class to manage Homebrew casks.'''

    # class regexes ------------------------------------------------ {{{
    VALID_CASK_CHARS = r'''
        \w                  # alphanumeric characters (i.e., [a-zA-Z0-9_])
        .                   # dots
        /                   # slash (for taps)
        -                   # dashes
    '''

    INVALID_CASK_REGEX = negate_regex_group(VALID_CASK_CHARS)
    # /class regexes ----------------------------------------------- }}}

    # class validations -------------------------------------------- {{{
    @classmethod
    def valid_cask(cls, cask):
        '''A valid cask is either None or alphanumeric + backslashes.'''

        if cask is None:
            return True

        return (
            isinstance(cask, basestring)
            and not cls.INVALID_CASK_REGEX.search(cask)
        )

    @classmethod
    def valid_state(cls, state):
        '''
        A valid state is one of:
            - installed
            - absent
        '''

        if state is None:
            return True
        else:
            return (
                isinstance(state, basestring)
                and state.lower() in (
                    'installed',
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
    def current_cask(self):
        return self._current_cask

    @current_cask.setter
    def current_cask(self, cask):
        if not self.valid_cask(cask):
            self._current_cask = None
            self.failed = True
            self.message = 'Invalid cask: {0}.'.format(cask)
            raise HomebrewCaskException(self.message)

        else:
            self._current_cask = cask
            return cask
    # /class properties -------------------------------------------- }}}

    def __init__(self, module, path, casks=None, state=None,
                 update_homebrew=False, install_options=None):
        super(HomebrewCask, self).__init__()
        if not install_options:
            install_options = list()
        self._setup_status_vars()
        self._setup_instance_vars(module=module, path=path, casks=casks,
                                  state=state, update_homebrew=update_homebrew,
                                  install_options=install_options,)

        self._prep()

    # checks ------------------------------------------------------- {{{
    def _current_cask_is_installed(self):
        if not self.valid_cask(self.current_cask):
            self.failed = True
            self.message = 'Invalid cask: {0}.'.format(self.current_cask)
            raise HomebrewCaskException(self.message)

        cmd = [
            "{brew_path}".format(brew_path=self.brew_path),
            "cask",
            "list"
        ]
        rc, out, err = self.module.run_command(cmd)

        if 'nothing to list' in err:
            return False
        elif rc == 0:
            casks = [cask_.strip() for cask_ in out.split('\n') if cask_.strip()]
            return self.current_cask in casks
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewCaskException(self.message)
    # /checks ------------------------------------------------------ }}}

    # commands ----------------------------------------------------- {{{
    def _run(self):
        if self.update_homebrew:
            self._update_homebrew()

        if self.state == 'installed':
            return self._install_casks()
        elif self.state == 'absent':
            return self._uninstall_casks()

        if self.command:
            return self._command()

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
            raise HomebrewCaskException(self.message)
    # /updated ------------------------------- }}}

    # installed ------------------------------ {{{
    def _install_current_cask(self):
        if not self.valid_cask(self.current_cask):
            self.failed = True
            self.message = 'Invalid cask: {0}.'.format(self.current_cask)
            raise HomebrewCaskException(self.message)

        if self._current_cask_is_installed():
            self.unchanged_count += 1
            self.message = 'Cask already installed: {0}'.format(
                self.current_cask,
            )
            return True

        if self.module.check_mode:
            self.changed = True
            self.message = 'Cask would be installed: {0}'.format(
                self.current_cask
            )
            raise HomebrewCaskException(self.message)

        opts = (
            [self.brew_path, 'cask', 'install', self.current_cask]
            + self.install_options
        )

        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if self._current_cask_is_installed():
            self.changed_count += 1
            self.changed = True
            self.message = 'Cask installed: {0}'.format(self.current_cask)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewCaskException(self.message)

    def _install_casks(self):
        for cask in self.casks:
            self.current_cask = cask
            self._install_current_cask()

        return True
    # /installed ----------------------------- }}}

    # uninstalled ---------------------------- {{{
    def _uninstall_current_cask(self):
        if not self.valid_cask(self.current_cask):
            self.failed = True
            self.message = 'Invalid cask: {0}.'.format(self.current_cask)
            raise HomebrewCaskException(self.message)

        if not self._current_cask_is_installed():
            self.unchanged_count += 1
            self.message = 'Cask already uninstalled: {0}'.format(
                self.current_cask,
            )
            return True

        if self.module.check_mode:
            self.changed = True
            self.message = 'Cask would be uninstalled: {0}'.format(
                self.current_cask
            )
            raise HomebrewCaskException(self.message)

        cmd = [opt
               for opt in (self.brew_path, 'cask', 'uninstall', self.current_cask)
               if opt]

        rc, out, err = self.module.run_command(cmd)

        if not self._current_cask_is_installed():
            self.changed_count += 1
            self.changed = True
            self.message = 'Cask uninstalled: {0}'.format(self.current_cask)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewCaskException(self.message)

    def _uninstall_casks(self):
        for cask in self.casks:
            self.current_cask = cask
            self._uninstall_current_cask()

        return True
    # /uninstalled ----------------------------- }}}
    # /commands ---------------------------------------------------- }}}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(
                aliases=["pkg", "package", "cask"],
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
                    "absent", "removed", "uninstalled",
                ],
            ),
            update_homebrew=dict(
                default=False,
                aliases=["update-brew"],
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
        casks = p['name']
    else:
        casks = None

    path = p['path']
    if path:
        path = path.split(':')

    state = p['state']
    if state in ('present', 'installed'):
        state = 'installed'
    if state in ('absent', 'removed', 'uninstalled'):
        state = 'absent'

    update_homebrew = p['update_homebrew']
    p['install_options'] = p['install_options'] or []
    install_options = ['--{0}'.format(install_option)
                       for install_option in p['install_options']]

    brew_cask = HomebrewCask(module=module, path=path, casks=casks,
                             state=state, update_homebrew=update_homebrew,
                             install_options=install_options)
    (failed, changed, message) = brew_cask.run()
    if failed:
        module.fail_json(msg=message)
    else:
        module.exit_json(changed=changed, msg=message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
